"""
El grafo del agente de triaje de OTs.

Tres ideas de LangGraph en un solo archivo:
  - ESTADO: un diccionario compartido que todos los pasos leen y completan.
  - NODOS: cada paso del proceso es una función normal de Python.
  - ARISTAS: quién va después de quién; algunas son condicionales (decisiones).

Y dos capacidades que lo hacen útil en operaciones:
  - interrupt(): el grafo se PARA y espera a que una persona decida.
  - checkpointer: el estado se guarda en cada paso, así se puede retomar
    horas o días después, incluso desde otro proceso.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from . import herramientas as h
from .llm import clasificar, redactar_mensaje

UMBRAL_POTENCIA_DBM = -27.0  # por debajo, la señal óptica es insuficiente
MAX_REINICIOS = 1


# ---------- ESTADO ----------

class Estado(TypedDict, total=False):
    texto: str                 # la incidencia tal como llega
    clasificacion: dict        # tipo, urgencia, cliente, resumen
    cliente: dict
    historico: list
    diagnostico: dict
    reinicios: int
    decision: str              # "remoto" | "visita"
    motivo: str
    propuesta: dict            # lo que se enseña al humano para aprobar
    aprobacion: dict
    ot_id: str
    situacion: str             # qué le vamos a contar al cliente
    mensaje_cliente: str
    traza: Annotated[list[str], operator.add]  # cada nodo añade una línea


# ---------- NODOS ----------

def clasificar_incidencia(estado: Estado) -> dict:
    c = clasificar(estado["texto"])
    return {
        "clasificacion": c.model_dump(),
        "reinicios": 0,
        "traza": [f"[clasificar] {c.cliente_id} · {c.tipo} · urgencia {c.urgencia}"],
    }


def consultar_datos(estado: Estado) -> dict:
    cid = estado["clasificacion"]["cliente_id"]
    cliente = h.consultar_cliente(cid)
    historico = h.consultar_historico(cid)
    return {
        "cliente": cliente,
        "historico": historico,
        "traza": [f"[consultar] {cliente.get('nombre')} ({cliente.get('segmento')}, {cliente.get('zona')}) · "
                  f"{len(historico)} {'OT' if len(historico) == 1 else 'OTs'} en 30 días"],
    }


def diagnosticar(estado: Estado) -> dict:
    cid = estado["clasificacion"]["cliente_id"]
    d = h.diagnosticar_ont(cid, reiniciada=estado.get("reinicios", 0) > 0)
    return {"diagnostico": d, "traza": [f"[diagnosticar] {d}"]}


def reiniciar(estado: Estado) -> dict:
    cid = estado["clasificacion"]["cliente_id"]
    return {"reinicios": estado.get("reinicios", 0) + 1, "traza": [f"[reiniciar] {h.reiniciar_ont(cid)}"]}


def decidir(estado: Estado) -> dict:
    d = estado["diagnostico"]
    potencia = d.get("potencia_optica_dbm")
    if not d.get("ont_responde"):
        decision, motivo = "visita", "La ONT no responde ni tras reinicio remoto"
    elif d.get("alarma") == "LOS":
        decision, motivo = "visita", "Sin señal óptica (LOS): avería física en la acometida"
    elif potencia is not None and potencia < UMBRAL_POTENCIA_DBM:
        decision, motivo = "visita", f"Potencia óptica baja ({potencia} dBm)"
    elif d.get("wifi_canal_saturado"):
        decision, motivo = "remoto", "Línea correcta; el problema es el wifi saturado"
    else:
        decision, motivo = "remoto", "Línea correcta tras el diagnóstico"
    return {"decision": decision, "motivo": motivo, "traza": [f"[decidir] {decision.upper()}: {motivo}"]}


def resolver_remoto(estado: Estado) -> dict:
    d = estado["diagnostico"]
    if d.get("wifi_canal_saturado"):
        situacion = "Hemos detectado interferencias en tu wifi y lo hemos cambiado de canal en remoto. Debería ir mejor ya."
    elif estado.get("reinicios", 0) > 0:
        situacion = "Hemos reiniciado tu router en remoto y la conexión ya está restablecida."
    else:
        situacion = "Hemos revisado tu línea y funciona correctamente."
    return {"situacion": situacion, "traza": ["[resolver_remoto] Resuelto sin desplazamiento"]}


def proponer_visita(estado: Estado) -> dict:
    cliente, historico = estado["cliente"], estado["historico"]
    tecnico = h.buscar_tecnico(cliente["zona"])
    alertas = []
    if len(historico) >= 2:
        alertas.append(f"Cliente reincidente: {len(historico)} visitas en 30 días. Valorar escalar a ingeniería.")
    if cliente.get("segmento") == "Pyme":
        alertas.append("Pyme: impacto en su negocio.")
    propuesta = {
        "cliente": f"{cliente['nombre']} ({estado['clasificacion']['cliente_id']})",
        "motivo": estado["motivo"],
        "urgencia": estado["clasificacion"]["urgencia"],
        "tecnico": tecnico,
        "alertas": alertas,
    }
    return {"propuesta": propuesta, "traza": [f"[proponer_visita] {tecnico['nombre']} · {tecnico['hueco']}"
                                              + (f" · {len(alertas)} {'alerta' if len(alertas) == 1 else 'alertas'}" if alertas else "")]}


def aprobacion_humana(estado: Estado) -> dict:
    # Aquí el grafo se detiene. Lo que pasemos a interrupt() es lo que ve la persona.
    # La ejecución se reanuda cuando alguien llama con Command(resume={...}).
    respuesta = interrupt(estado["propuesta"])
    aprobado = bool(respuesta.get("aprobado"))
    comentario = respuesta.get("comentario", "")
    return {
        "aprobacion": {"aprobado": aprobado, "comentario": comentario},
        "traza": [f"[aprobacion_humana] {'APROBADA' if aprobado else 'RECHAZADA'}"
                  + (f" · \"{comentario}\"" if comentario else "")],
    }


def crear_ot(estado: Estado) -> dict:
    p = estado["propuesta"]
    ot = h.crear_ot(estado["clasificacion"]["cliente_id"], "averia", p["tecnico"], estado["motivo"])
    situacion = f"Hemos programado la visita de un técnico ({p['tecnico']['nombre']}) para {p['tecnico']['hueco'].lower()}. Referencia {ot}."
    return {"ot_id": ot, "situacion": situacion, "traza": [f"[crear_ot] {ot} creada"]}


def escalar_back_office(estado: Estado) -> dict:
    situacion = "Un compañero de soporte está revisando tu caso y te llamará hoy."
    nota = estado["aprobacion"].get("comentario") or "sin comentario"
    return {"situacion": situacion, "traza": [f"[escalar] Derivado a revisión manual ({nota})"]}


def notificar_cliente(estado: Estado) -> dict:
    c = estado["cliente"]
    msg = redactar_mensaje(c["nombre"], c["segmento"], estado["situacion"])
    return {"mensaje_cliente": msg, "traza": ["[notificar] Mensaje al cliente redactado"]}


# ---------- ARISTAS CONDICIONALES ----------

def tras_diagnostico(estado: Estado) -> str:
    if not estado["diagnostico"].get("ont_responde") and estado.get("reinicios", 0) < MAX_REINICIOS:
        return "ONT no responde"
    return "diagnóstico completo"


def tras_decidir(estado: Estado) -> str:
    return estado["decision"]


def tras_aprobacion(estado: Estado) -> str:
    return "aprobada" if estado["aprobacion"]["aprobado"] else "rechazada"


# ---------- CONSTRUCCIÓN DEL GRAFO ----------

def construir_grafo(checkpointer=None):
    g = StateGraph(Estado)

    g.add_node("clasificar", clasificar_incidencia)
    g.add_node("consultar_datos", consultar_datos)
    g.add_node("diagnosticar", diagnosticar)
    g.add_node("reiniciar_ont", reiniciar)
    g.add_node("decidir", decidir)
    g.add_node("resolver_remoto", resolver_remoto)
    g.add_node("proponer_visita", proponer_visita)
    g.add_node("aprobacion_humana", aprobacion_humana)
    g.add_node("crear_ot", crear_ot)
    g.add_node("escalar_back_office", escalar_back_office)
    g.add_node("notificar_cliente", notificar_cliente)

    g.add_edge(START, "clasificar")
    g.add_edge("clasificar", "consultar_datos")
    g.add_edge("consultar_datos", "diagnosticar")
    g.add_conditional_edges("diagnosticar", tras_diagnostico,
                            {"ONT no responde": "reiniciar_ont", "diagnóstico completo": "decidir"})
    g.add_edge("reiniciar_ont", "diagnosticar")  # bucle: reiniciar y volver a diagnosticar
    g.add_conditional_edges("decidir", tras_decidir,
                            {"remoto": "resolver_remoto", "visita": "proponer_visita"})
    g.add_edge("proponer_visita", "aprobacion_humana")
    g.add_conditional_edges("aprobacion_humana", tras_aprobacion,
                            {"aprobada": "crear_ot", "rechazada": "escalar_back_office"})
    g.add_edge("resolver_remoto", "notificar_cliente")
    g.add_edge("crear_ot", "notificar_cliente")
    g.add_edge("escalar_back_office", "notificar_cliente")
    g.add_edge("notificar_cliente", END)

    return g.compile(checkpointer=checkpointer)

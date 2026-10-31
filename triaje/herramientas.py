"""
Herramientas: las "manos" del agente.

Cada función simula una llamada a un sistema real (CRM, gestión de red,
planificador). El agente no inventa datos: los pide a estas funciones.
"""

from .datos import CLIENTES, ESTADO_RED, HISTORICO_OTS, TECNICOS


def consultar_cliente(cliente_id: str) -> dict:
    return CLIENTES.get(cliente_id, {})


def consultar_historico(cliente_id: str) -> list[dict]:
    return HISTORICO_OTS.get(cliente_id, [])


def diagnosticar_ont(cliente_id: str, reiniciada: bool = False) -> dict:
    estado = ESTADO_RED.get(cliente_id, {"ont_responde": False})
    if reiniciada and "tras_reinicio" in estado:
        return estado["tras_reinicio"]
    return {k: v for k, v in estado.items() if k != "tras_reinicio"}


def reiniciar_ont(cliente_id: str) -> str:
    return f"Orden de reinicio enviada a la ONT de {cliente_id}"


def buscar_tecnico(zona: str) -> dict | None:
    """Devuelve el técnico de la zona con el hueco más temprano."""
    candidatos = [t for t in TECNICOS if zona in t["zonas"]]
    if not candidatos:
        return None
    orden = lambda t: (0 if t["huecos"][0].startswith("Hoy") else 1, t["huecos"][0])
    t = sorted(candidatos, key=orden)[0]
    return {"id": t["id"], "nombre": t["nombre"], "hueco": t["huecos"][0]}


_contador_ot = {"n": 4810}


def crear_ot(cliente_id: str, tipo: str, tecnico: dict, descripcion: str) -> str:
    _contador_ot["n"] += 1
    return f"OT-{_contador_ot['n']}"

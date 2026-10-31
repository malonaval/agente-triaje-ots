"""
Las dos tareas donde usamos un modelo de lenguaje:
  1. Entender la incidencia escrita en texto libre.
  2. Redactar el mensaje al cliente.

Todo lo demás (consultar datos, decidir la ruta) son reglas y código normal.
Eso es intencionado: el LLM se usa donde aporta, no en todas partes.

Proveedor del LLM (por orden de preferencia):
  - ANTHROPIC_API_KEY en el entorno -> Claude.
  - GROQ_API_KEY en el entorno      -> modelo abierto en Groq (tiene capa gratuita).
  - Ninguna                         -> "modo demo" con reglas simples, sin coste ni cuenta.
Se puede forzar con PROVEEDOR_LLM=anthropic|groq|demo.
"""

import os
import re
from typing import Literal

from pydantic import BaseModel, Field

MODELO_CLAUDE = os.getenv("MODELO_CLAUDE", "claude-sonnet-5-5")
MODELO_GROQ = os.getenv("MODELO_GROQ", "llama-3.3-70b-versatile")


class Clasificacion(BaseModel):
    cliente_id: str = Field(description="Identificador del cliente, formato C-XXXX")
    tipo: Literal["sin_servicio", "lentitud", "cortes_intermitentes", "otro"]
    urgencia: Literal["alta", "media", "baja"]
    resumen: str = Field(description="Resumen de la incidencia en una frase")


def proveedor() -> str:
    """Devuelve "anthropic", "groq" o "demo"."""
    forzado = os.getenv("PROVEEDOR_LLM", "").strip().lower()
    if forzado in ("anthropic", "groq", "demo"):
        return forzado
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    return "demo"


def usando_llm() -> bool:
    return proveedor() != "demo"


def descripcion_modo() -> str:
    return {
        "anthropic": f"Claude ({MODELO_CLAUDE})",
        "groq": f"Groq ({MODELO_GROQ})",
        "demo": "demo sin API key",
    }[proveedor()]


def _llm():
    if proveedor() == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=MODELO_GROQ, temperature=0)
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model=MODELO_CLAUDE, temperature=0)


# ---------- 1. Clasificar la incidencia ----------

PROMPT_CLASIFICAR = """Eres el primer filtro del back office de un operador de fibra.
Lee la incidencia y extrae: cliente, tipo de problema, urgencia y un resumen.
Urgencia alta: el cliente no tiene servicio, o es una pyme afectada en horario laboral.
Urgencia media: servicio degradado. Urgencia baja: consultas o molestias menores.

Incidencia:
{texto}"""


def clasificar(texto: str) -> Clasificacion:
    if usando_llm():
        return _llm().with_structured_output(Clasificacion).invoke(PROMPT_CLASIFICAR.format(texto=texto))
    return _clasificar_demo(texto)


def _clasificar_demo(texto: str) -> Clasificacion:
    t = texto.lower()
    m = re.search(r"c-\d{4}", t)
    cliente = m.group(0).upper() if m else "DESCONOCIDO"
    if any(p in t for p in ["sin internet", "no tengo conexión", "sin conexión", "no funciona", "sin servicio", "caído"]):
        tipo, urgencia = "sin_servicio", "alta"
    elif any(p in t for p in ["lento", "lentitud", "va mal"]):
        tipo, urgencia = "lentitud", "media"
    elif any(p in t for p in ["se corta", "cortes", "intermitente"]):
        tipo, urgencia = "cortes_intermitentes", "media"
    else:
        tipo, urgencia = "otro", "baja"
    return Clasificacion(cliente_id=cliente, tipo=tipo, urgencia=urgencia, resumen=texto.strip()[:120])


# ---------- 2. Redactar el mensaje al cliente ----------

PROMPT_MENSAJE = """Redacta un SMS breve (máximo 300 caracteres), cercano y claro,
para el cliente {nombre}. Tutea si es residencial; usa usted si es pyme ({segmento}).
Situación: {situacion}
No prometas nada que no esté en la situación. Firma como "Soporte Fibra"."""


def redactar_mensaje(nombre: str, segmento: str, situacion: str) -> str:
    if usando_llm():
        return _llm().invoke(PROMPT_MENSAJE.format(nombre=nombre, segmento=segmento, situacion=situacion)).content
    if segmento == "Residencial":
        return f"Hola {nombre.split()[0]}: {situacion} Gracias por tu paciencia. Soporte Fibra"
    usted = (situacion.replace("tu ", "su ").replace("te llamará", "le llamará"))
    return f"Estimado cliente ({nombre}): {usted} Gracias por su paciencia. Soporte Fibra"

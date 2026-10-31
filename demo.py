"""
Ejecuta 4 incidencias de ejemplo de principio a fin, sin intervención,
y guarda las trazas en salidas/trazas.txt.

Las decisiones del "humano" están predefinidas para que la demo sea reproducible.
"""

import os

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from triaje.grafo import construir_grafo
from triaje.llm import descripcion_modo

load_dotenv()

ESCENARIOS = [
    ("Lentitud: se resuelve en remoto",
     "Cliente C-1001: dice que internet le va muy lento por las noches, sobre todo en el salón.",
     None),
    ("Sin conexión: el agente reinicia y vuelve a diagnosticar (bucle)",
     "C-1003 llama porque no tengo conexión desde esta mañana.",
     None),
    ("Avería física: propone técnico y el back office aprueba",
     "Talleres Hermanos Ruiz (C-1002): sin internet desde ayer, la ONT tiene la luz LOS en rojo.",
     {"aprobado": True, "comentario": ""}),
    ("Cliente reincidente: el back office rechaza y escala",
     "Clínica Dental Sonrisas, cliente C-1004: otra vez sin servicio, no funciona nada.",
     {"aprobado": False, "comentario": "Tercera visita en un mes: que lo mire ingeniería antes de mandar a nadie"}),
]


def main():
    grafo = construir_grafo(InMemorySaver())
    salida = [f"Modo: {descripcion_modo()}\n"]

    for i, (titulo, texto, decision_humana) in enumerate(ESCENARIOS, 1):
        config = {"configurable": {"thread_id": f"demo-{i}"}}
        bloque = [f"\n{'=' * 70}\nESCENARIO {i}: {titulo}\nEntrada: {texto}\n"]

        estado = grafo.invoke({"texto": texto}, config)
        snap = grafo.get_state(config)
        if snap.next:  # el grafo está parado en la aprobación humana
            hechos = len(estado["traza"])
            bloque += [f"  {l}" for l in estado["traza"]]
            propuesta = snap.tasks[0].interrupts[0].value
            bloque.append(f"  ⏸  PAUSA. El grafo espera a una persona. Propuesta: {propuesta}")
            estado = grafo.invoke(Command(resume=decision_humana), config)
            bloque += [f"  {l}" for l in estado["traza"][hechos:]]
        else:
            bloque += [f"  {l}" for l in estado["traza"]]
        bloque.append(f"\n  Mensaje al cliente: {estado['mensaje_cliente']}")
        salida.append("\n".join(bloque))

    texto_final = "\n".join(salida)
    print(texto_final)
    os.makedirs("salidas", exist_ok=True)
    with open("salidas/trazas.txt", "w") as f:
        f.write(texto_final + "\n")


if __name__ == "__main__":
    main()

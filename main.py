"""
Uso:
  python main.py "texto de la incidencia"            -> ejecuta y, si hace falta, te pide aprobación en el terminal
  python main.py --pausar "texto de la incidencia"   -> ejecuta hasta la aprobación, guarda y SALE
  python main.py --pendientes                        -> lista los casos esperando aprobación
  python main.py --retomar <caso> --aprobar|--rechazar [--comentario "..."]

El estado se guarda en triaje.db (SQLite). Por eso un caso pausado se puede
retomar más tarde, desde otro terminal o tras reiniciar el ordenador.
"""

import argparse
import json
import sqlite3
import uuid

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from triaje.grafo import construir_grafo
from triaje.llm import usando_claude

load_dotenv()
DB = "triaje.db"


def mostrar_resultado(estado: dict):
    print("\n--- Traza ---")
    for linea in estado.get("traza", []):
        print(" ", linea)
    if estado.get("mensaje_cliente"):
        print("\n--- Mensaje al cliente ---\n ", estado["mensaje_cliente"])


def mostrar_propuesta(p: dict):
    print("\n=== APROBACIÓN NECESARIA ===")
    print(f"  Cliente:  {p['cliente']}")
    print(f"  Motivo:   {p['motivo']}")
    print(f"  Urgencia: {p['urgencia']}")
    print(f"  Técnico:  {p['tecnico']['nombre']} ({p['tecnico']['id']}) · {p['tecnico']['hueco']}")
    for a in p.get("alertas", []):
        print(f"  ⚠ {a}")


def interrupcion_pendiente(grafo, config):
    snap = grafo.get_state(config)
    for tarea in snap.tasks:
        if tarea.interrupts:
            return tarea.interrupts[0].value
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("texto", nargs="?")
    ap.add_argument("--pausar", action="store_true")
    ap.add_argument("--pendientes", action="store_true")
    ap.add_argument("--retomar")
    ap.add_argument("--aprobar", action="store_true")
    ap.add_argument("--rechazar", action="store_true")
    ap.add_argument("--comentario", default="")
    args = ap.parse_args()

    print(f"(Modo: {'Claude' if usando_claude() else 'demo sin API key'})")
    conn = sqlite3.connect(DB, check_same_thread=False)
    grafo = construir_grafo(SqliteSaver(conn))

    if args.pendientes:
        vistos = set()
        for cp in SqliteSaver(conn).list(None):
            caso = cp.config["configurable"]["thread_id"]
            if caso in vistos:
                continue
            vistos.add(caso)
            p = interrupcion_pendiente(grafo, {"configurable": {"thread_id": caso}})
            if p:
                print(f"  {caso}: {p['cliente']} · {p['motivo']}")
        return

    if args.retomar:
        config = {"configurable": {"thread_id": args.retomar}}
        p = interrupcion_pendiente(grafo, config)
        if not p:
            print("Ese caso no está esperando aprobación.")
            return
        mostrar_propuesta(p)
        decision = {"aprobado": args.aprobar and not args.rechazar, "comentario": args.comentario}
        mostrar_resultado(grafo.invoke(Command(resume=decision), config))
        return

    if not args.texto:
        ap.error("Falta el texto de la incidencia")

    caso = "caso-" + uuid.uuid4().hex[:6]
    config = {"configurable": {"thread_id": caso}}
    print(f"Caso {caso}")
    estado = grafo.invoke({"texto": args.texto}, config)

    p = interrupcion_pendiente(grafo, config)
    if p:
        mostrar_propuesta(p)
        if args.pausar:
            print(f"\nCaso guardado. Retómalo con:\n  python main.py --retomar {caso} --aprobar")
            return
        r = input("\n¿Apruebas la visita? (s/n): ").strip().lower()
        comentario = input("Comentario (opcional): ").strip()
        estado = grafo.invoke(Command(resume={"aprobado": r == "s", "comentario": comentario}), config)

    mostrar_resultado(estado)


if __name__ == "__main__":
    main()

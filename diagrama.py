"""
Dibuja el diagrama del agente (tres carriles: entender, decidir, actuar)
y lo guarda como salidas/grafo.svg y salidas/grafo.png.

La colocación es a mano para que se lea bien, pero las conexiones se
comprueban contra el grafo REAL de LangGraph: si el código cambia y el
dibujo no, el script falla en vez de mentir.

Requisitos: `rsvg-convert` (librsvg) y las fuentes de la carpeta fuentes/
(Space Grotesk y JetBrains Mono, licencia OFL) instaladas en el sistema.
"""

import os
import subprocess

from triaje.grafo import construir_grafo

W, H = 2000, 1240
SANS = "'Space Grotesk', Inter, Arial, sans-serif"
MONO = "'JetBrains Mono', 'DejaVu Sans Mono', monospace"

# Paleta: tinta sobre negro cálido, un solo color de acento
FONDO = "#0F0F0D"
TINTA = "#F2EFE8"
APAGADO = "#8A877F"
TENUE = "#3A3934"
ACENTO = "#FF5B1F"
CAJA_REGLA = "#181816"

BW, BH = 250, 108

CARRILES = [  # (número, nombre en dos líneas, y_superior, y_inferior)
    ("01", ("Entender y", "diagnosticar"), 262, 530),
    ("02", ("Decidir", ""), 530, 810),
    ("03", ("Actuar y", "avisar"), 810, 1120),
]
Y1, Y2, Y3 = 400, 670, 950

# nodo -> (cx, cy, tipo, paso, título, subtítulo)
NODOS = {
    "__start__":           (318, Y1, "inicio", "", "", ""),
    "clasificar":          (760, Y1, "ia", "01", "Clasificar", "tipo · urgencia · cliente"),
    "consultar_datos":     (1050, Y1, "sistema", "02", "Consultar cliente", "ficha + OTs de 30 días"),
    "diagnosticar":        (1340, Y1, "sistema", "03", "Diagnosticar ONT", "señal y alarmas"),
    "reiniciar_ont":       (1760, Y1, "sistema", "04", "Reiniciar ONT", "en remoto"),
    "decidir":             (520, Y2, "decision", "05", "¿Remoto o técnico?", ""),
    "proponer_visita":     (900, Y2, "regla", "06", "Proponer técnico", "zona + primer hueco"),
    "aprobacion_humana":   (1270, Y2, "persona", "07", "Aprobación", "el back office decide"),
    "crear_ot":            (1700, Y2, "sistema", "08", "Crear OT", "y reservar hueco"),
    "resolver_remoto":     (520, Y3, "regla", "09", "Resolver en remoto", "sin desplazamiento"),
    "escalar_back_office": (1270, Y3, "regla", "10", "Escalar caso", "revisión manual"),
    "notificar_cliente":   (1700, Y3, "ia", "11", "Mensaje al cliente", "SMS en su tono"),
    "__end__":             (1905, Y3, "fin", "", "", ""),
}

M, T = BW / 2, BH / 2
CONEXIONES = [  # (origen, destino, etiqueta, recorrido en ángulo recto)
    ("__start__", "clasificar", "", [(592, Y1), (760 - M, Y1)]),
    ("clasificar", "consultar_datos", "", [(760 + M, Y1), (1050 - M, Y1)]),
    ("consultar_datos", "diagnosticar", "", [(1050 + M, Y1), (1340 - M, Y1)]),
    ("diagnosticar", "reiniciar_ont", "no responde", [(1340 + M, Y1 - 24), (1760 - M, Y1 - 24)]),
    ("reiniciar_ont", "diagnosticar", "reintenta ×1", [(1760 - M, Y1 + 24), (1340 + M, Y1 + 24)]),
    ("diagnosticar", "decidir", "diagnóstico completo",
     [(1340, Y1 + T), (1340, 530), (520, 530), (520, Y2 - 66)]),
    ("decidir", "proponer_visita", "visita", [(520 + 140, Y2), (900 - M, Y2)]),
    ("decidir", "resolver_remoto", "remoto", [(520, Y2 + 66), (520, Y3 - T)]),
    ("proponer_visita", "aprobacion_humana", "", [(900 + M, Y2), (1270 - M, Y2)]),
    ("aprobacion_humana", "crear_ot", "aprobada", [(1270 + M, Y2), (1700 - M, Y2)]),
    ("aprobacion_humana", "escalar_back_office", "rechazada", [(1270, Y2 + T), (1270, Y3 - T)]),
    ("crear_ot", "notificar_cliente", "", [(1700, Y2 + T), (1700, Y3 - T)]),
    ("escalar_back_office", "notificar_cliente", "", [(1270 + M, Y3), (1700 - M, Y3)]),
    ("resolver_remoto", "notificar_cliente", "",
     [(520, Y3 + T), (520, 1074), (1650, 1074), (1650, Y3 + T)]),
    ("notificar_cliente", "__end__", "", [(1700 + M, Y3), (1905 - 30, Y3)]),
]
BUCLE = {("diagnosticar", "reiniciar_ont"), ("reiniciar_ont", "diagnosticar")}


def comprobar_contra_grafo():
    g = construir_grafo().get_graph()
    reales = {(e.source, e.target) for e in g.edges}
    dibujadas = {(o, d) for o, d, _, _ in CONEXIONES}
    if reales != dibujadas:
        raise SystemExit(f"El dibujo no coincide con el grafo.\n"
                         f"Faltan: {reales - dibujadas}\nSobran: {dibujadas - reales}")
    faltan = set(g.nodes) - set(NODOS)
    if faltan:
        raise SystemExit(f"Nodos sin posición en el dibujo: {faltan}")


def t(x, y, s, size, color=TINTA, weight=400, anchor="start", fuente=SANS, spacing=0):
    return (f'<text x="{x}" y="{y}" font-family="{fuente}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}" letter-spacing="{spacing}">{s}</text>')


def mono(x, y, s, size=14, color=APAGADO, weight=500, anchor="start", spacing=1.5):
    return t(x, y, s.upper(), size, color, weight, anchor, MONO, spacing)


def ancho_mono(s, size=14, spacing=1.5):
    return len(s) * (size * 0.6 + spacing)


def nodo(cx, cy, tipo, paso, titulo, sub):
    if tipo == "inicio":
        x = cx
        return "\n".join([
            mono(x, cy - 58, "Entrada", 14, ACENTO),
            t(x - 6, cy + 4, "“", 64, ACENTO, 700),
            t(x + 30, cy - 10, "Sin internet desde ayer,", 20, TINTA, 500),
            t(x + 30, cy + 18, "la ONT tiene la luz roja.”", 20, TINTA, 500),
            mono(x + 30, cy + 54, "texto libre del cliente", 12.5),
        ])
    if tipo == "fin":
        return "\n".join([
            f'<circle cx="{cx}" cy="{cy}" r="26" fill="none" stroke="{ACENTO}" stroke-width="2.5"/>',
            f'<circle cx="{cx}" cy="{cy}" r="11" fill="{ACENTO}"/>',
            mono(cx, cy + 56, "Fin", 13, TINTA, anchor="middle"),
        ])
    if tipo == "decision":
        pts = f"{cx},{cy - 66} {cx + 140},{cy} {cx},{cy + 66} {cx - 140},{cy}"
        return "\n".join([
            f'<polygon points="{pts}" fill="{CAJA_REGLA}" stroke="{APAGADO}" stroke-width="2"/>',
            mono(cx, cy - 22, f"{paso} · regla", 12.5, APAGADO, anchor="middle"),
            t(cx, cy + 10, titulo, 21, TINTA, 600, "middle"),
        ])

    estilos = {  # relleno, borde, texto, texto secundario, etiqueta
        "ia":      (ACENTO, ACENTO, FONDO, "#4A1A08", "IA"),
        "persona": (TINTA, TINTA, FONDO, "#5E5B54", "Persona"),
        "sistema": (FONDO, TINTA, TINTA, APAGADO, "Sistema"),
        "regla":   (CAJA_REGLA, APAGADO, TINTA, APAGADO, "Regla"),
    }
    relleno, borde, color, color2, etiqueta = estilos[tipo]
    x, y = cx - BW / 2, cy - BH / 2
    return "\n".join([
        f'<rect x="{x}" y="{y}" width="{BW}" height="{BH}" fill="{relleno}" stroke="{borde}" stroke-width="2"/>',
        mono(x + 18, y + 28, paso, 13, color2, 700),
        mono(x + BW - 18, y + 28, etiqueta, 13, color2, 700, "end"),
        t(x + 18, y + 68, titulo, 23, color, 600),
        t(x + 18, y + 92, sub, 15.5, color2, 400),
    ])


def conexion(o, d, etiqueta, pts):
    bucle = (o, d) in BUCLE
    color = ACENTO if bucle else APAGADO
    marcador = "flecha_acento" if bucle else "flecha"
    camino = "M" + " L".join(f"{x},{y}" for x, y in pts)
    out = [f'<path d="{camino}" fill="none" stroke="{color}" stroke-width="2" marker-end="url(#{marcador})"/>']
    if etiqueta:
        tramos = list(zip(pts, pts[1:]))
        (x1, y1), (x2, y2) = max(tramos, key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if x1 == x2 and min(y1, y2) < 810 < max(y1, y2):
            my = 810  # sobre la línea entre carriles
        if bucle:
            out.append(mono(mx, my + (-12 if y1 < Y1 else 26), etiqueta, 13, ACENTO, 600, "middle", 1.2))
        else:
            w = ancho_mono(etiqueta, 13, 1.2) + 24
            out.append(f'<rect x="{mx - w / 2}" y="{my - 14}" width="{w}" height="28" fill="{FONDO}"/>')
            out.append(mono(mx, my + 5, etiqueta, 13, TINTA, 600, "middle", 1.2))
    return "\n".join(out)


def construir_svg() -> str:
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<defs>',
         f'<pattern id="puntos" width="32" height="32" patternUnits="userSpaceOnUse">'
         f'<circle cx="2" cy="2" r="1.2" fill="#1F1E1B"/></pattern>',
         f'<marker id="flecha" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
         f'<path d="M0,1 L10,5 L0,9 z" fill="{APAGADO}"/></marker>',
         f'<marker id="flecha_acento" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
         f'<path d="M0,1 L10,5 L0,9 z" fill="{ACENTO}"/></marker>',
         '</defs>',
         f'<rect width="{W}" height="{H}" fill="{FONDO}"/>',
         f'<rect width="{W}" height="{H}" fill="url(#puntos)"/>']

    # Cabecera
    p.append(mono(60, 84, "Caso práctico · LangGraph", 16, ACENTO, 600, spacing=3))
    p.append(t(56, 160, "Agente de triaje de OTs", 76, TINTA, 700, spacing=-1.5))
    p.append(t(60, 206, "De una incidencia en texto libre a una orden de trabajo, en 11 pasos.", 24, APAGADO, 400))
    for x, num, etiqueta, color in [(1440, "11", "pasos", TINTA), (1620, "2", "con IA", ACENTO),
                                    (1780, "1", "persona decide", TINTA)]:
        p.append(t(x, 160, num, 92, color, 700, spacing=-3))
        p.append(mono(x + 4, 200, etiqueta, 14, APAGADO))
    p.append(f'<line x1="60" y1="{CARRILES[0][2]}" x2="{W - 60}" y2="{CARRILES[0][2]}" stroke="{TENUE}" stroke-width="1.5"/>')

    # Carriles
    for num, (l1, l2), y0, y1 in CARRILES:
        p.append(t(60, y0 + 74, num, 52, ACENTO, 700, spacing=-1))
        p.append(mono(62, y0 + 106, l1, 14, TINTA, 600))
        if l2:
            p.append(mono(62, y0 + 128, l2, 14, TINTA, 600))
        p.append(f'<line x1="60" y1="{y1}" x2="{W - 60}" y2="{y1}" stroke="{TENUE}" stroke-width="1.5"'
                 f'{"" if y1 == CARRILES[-1][3] else " stroke-dasharray=\"2 6\""}/>')

    for o, d, e, pts in CONEXIONES:
        p.append(conexion(o, d, e, pts))
    for cx, cy, tipo, paso, titulo, sub in NODOS.values():
        p.append(nodo(cx, cy, tipo, paso, titulo, sub))

    # Pie: leyenda y nota
    y = H - 62
    x = 60
    for relleno, borde, nombre in [(ACENTO, ACENTO, "IA"), (TINTA, TINTA, "Persona"),
                                   (FONDO, TINTA, "Sistema"), (CAJA_REGLA, APAGADO, "Regla")]:
        p.append(f'<rect x="{x}" y="{y - 14}" width="18" height="18" fill="{relleno}" stroke="{borde}" stroke-width="2"/>')
        p.append(mono(x + 30, y + 1, nombre, 13, TINTA, 500))
        x += 30 + ancho_mono(nombre, 13) + 40
    p.append(mono(W - 60, y + 1, "Datos sintéticos · conexiones validadas contra el código", 13, APAGADO, anchor="end", spacing=1))
    p.append("</svg>")
    return "\n".join(p)


def main():
    comprobar_contra_grafo()
    os.makedirs("salidas", exist_ok=True)
    with open("salidas/grafo.svg", "w") as f:
        f.write(construir_svg())
    with open("salidas/grafo.mmd", "w") as f:
        f.write(construir_grafo().get_graph().draw_mermaid())
    subprocess.run(["rsvg-convert", "-z", "1.5", "salidas/grafo.svg", "-o", "salidas/grafo.png"], check=True)
    print("Generado salidas/grafo.png, salidas/grafo.svg y salidas/grafo.mmd")


if __name__ == "__main__":
    main()

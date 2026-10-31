"""
Datos sintéticos. Nada de esto viene de clientes reales.

En un sistema real, estas tablas serían el CRM, el histórico de OTs
y el planificador de técnicos. Aquí son diccionarios para que el ejemplo
se pueda ejecutar en cualquier portátil.
"""

CLIENTES = {
    "C-1001": {"nombre": "Laura Gómez", "zona": "Madrid Norte", "servicio": "Fibra 600 Mb", "segmento": "Residencial"},
    "C-1002": {"nombre": "Talleres Hermanos Ruiz", "zona": "Getafe", "servicio": "Fibra 1 Gb", "segmento": "Pyme"},
    "C-1003": {"nombre": "Javier Martín", "zona": "Alcorcón", "servicio": "Fibra 300 Mb", "segmento": "Residencial"},
    "C-1004": {"nombre": "Clínica Dental Sonrisas", "zona": "Getafe", "servicio": "Fibra 1 Gb", "segmento": "Pyme"},
}

# OTs cerradas en los últimos 30 días
HISTORICO_OTS = {
    "C-1001": [],
    "C-1002": [],
    "C-1003": [{"fecha": "2026-10-12", "motivo": "Corte de servicio", "resolucion": "Reinicio remoto de la ONT"}],
    "C-1004": [
        {"fecha": "2026-10-09", "motivo": "Sin servicio", "resolucion": "Visita: conector reparado en roseta"},
        {"fecha": "2026-10-23", "motivo": "Sin servicio", "resolucion": "Visita: sustitución de latiguillo"},
    ],
}

# Estado que devolvería el sistema de gestión de red al consultar la ONT.
# "tras_reinicio" simula qué pasa si se reinicia en remoto.
ESTADO_RED = {
    "C-1001": {"ont_responde": True, "potencia_optica_dbm": -19.5, "wifi_canal_saturado": True},
    "C-1002": {"ont_responde": True, "potencia_optica_dbm": None, "alarma": "LOS"},
    "C-1003": {"ont_responde": False, "tras_reinicio": {"ont_responde": True, "potencia_optica_dbm": -20.1}},
    "C-1004": {"ont_responde": True, "potencia_optica_dbm": -28.7, "alarma": "Potencia baja"},
}

TECNICOS = [
    {"id": "T-07", "nombre": "Sergio", "zonas": ["Getafe", "Alcorcón"], "huecos": ["Hoy 16:00", "Mañana 09:00"]},
    {"id": "T-12", "nombre": "Marta", "zonas": ["Madrid Norte"], "huecos": ["Mañana 12:00"]},
    {"id": "T-15", "nombre": "Iván", "zonas": ["Getafe"], "huecos": ["Mañana 11:00"]},
]

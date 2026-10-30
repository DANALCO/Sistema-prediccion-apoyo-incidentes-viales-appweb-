"""Nombres en espanol de variables, zonas, grupos y metodos, y colores (un solo lugar)."""

INFRAESTRUCTURA = ["Amenity", "Bump", "Crossing", "Give_Way", "Junction", "No_Exit", "Railway",
                   "Roundabout", "Station", "Stop", "Traffic_Calming", "Traffic_Signal", "Turning_Loop"]

VARIABLE = {
    "State": "Estado", "Start_Lat": "Latitud", "Start_Lng": "Longitud", "Tipo_via": "Tipo de vía",
    "Hora": "Hora del día", "Dia_semana": "Día de la semana", "Mes": "Mes", "Estacion": "Estación del año",
    "Es_fin_de_semana": "Fin de semana", "Es_hora_pico": "Hora pico", "Sunrise_Sunset": "Día o noche",
    "Temperature(F)": "Temperatura (°F)", "Humidity(%)": "Humedad (%)", "Pressure(in)": "Presión (in)",
    "Visibility(mi)": "Visibilidad (mi)", "Wind_Speed(mph)": "Viento (mph)",
    "Precipitation(in)": "Precipitación (in)", "Wind_Direction": "Dirección del viento",
    "Weather_Condition": "Condición climática",
    "Amenity": "Servicio cercano", "Bump": "Resalto o reductor", "Crossing": "Cruce peatonal",
    "Give_Way": "Ceda el paso", "Junction": "Intersección", "No_Exit": "Calle sin salida",
    "Railway": "Cruce ferroviario", "Roundabout": "Rotonda", "Station": "Estación",
    "Stop": "Señal de pare", "Traffic_Calming": "Moderación de tráfico",
    "Traffic_Signal": "Semáforo", "Turning_Loop": "Lazo de giro",
}

GRUPO = {"Ubicacion": "Ubicación", "Infraestructura": "Infraestructura", "Tiempo": "Tiempo",
         "Clima": "Clima", "Informacion posterior": "Información posterior", "Otros": "Otros"}

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Las cuatro zonas que entrega el predictor (columna `Nivel`), de menor a mayor riesgo.
ZONAS = ["Normal", "Vigilancia (bajo el umbral)", "Vigilancia (sobre el umbral)", "Critico"]
ZONA_TEXTO = {"Normal": "Normal", "Vigilancia (bajo el umbral)": "Vigilancia · bajo el umbral",
              "Vigilancia (sobre el umbral)": "Vigilancia · sobre el umbral", "Critico": "Crítico"}

# Colores (una paleta corta; el acento marca lo que importa y el resto va en gris).
ACENTO = "#1f6feb"
GRIS = "#9aa3ad"
GRIS_CLARO = "#d5d9de"
ROJO = "#c0392b"
AMBAR = "#d98e04"
VERDE = "#2e8b57"
COLOR_ZONA = {"Normal": VERDE, "Vigilancia (bajo el umbral)": AMBAR,
              "Vigilancia (sobre el umbral)": "#e0782b", "Critico": ROJO}


def etiqueta_variable(v):
    return VARIABLE.get(v, v)


def etiqueta_categoria(variable, categoria):
    """Etiqueta legible de una categoria de la tabla de patrones (Hora '7' -> '07 h', Dia '0' -> 'Lun'...)."""
    c = str(categoria)
    try:
        if variable == "Hora":
            return f"{int(c):02d} h"
        if variable == "Dia_semana":
            return DIAS[int(c)]
        if variable == "Mes":
            return MESES[int(c) - 1]
    except (ValueError, IndexError):
        return c
    return {"Otonio": "Otoño", "Si": "Sí", "Day": "Día", "Night": "Noche", "Desconocido": "Sin dato"}.get(c, c)


def etiqueta_metodo(m):
    return {"Regresion_Logistica": "Regresión logística", "Promedio_ponderado": "Promedio ponderado",
            "Random_Forest": "Random Forest"}.get(m, str(m).replace("_", " "))

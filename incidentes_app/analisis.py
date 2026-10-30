"""
LOGICA DEL ANALISIS DE UN CASO: prediccion, explicacion por grupo, valores legibles y variantes del
«que pasaria si». Usa SOLO PredictorIncidentes (no reimplementa ninguna transformacion del modelo).
"""

import numpy as np
import pandas as pd

from .etiquetas import DIAS, MESES, etiqueta_variable

# «Que pasaria si»: campo que el operador puede mover -> columna del modelo
CAMPOS_WHATIF = {
    "Condición climática": "Weather_Condition",
    "Visibilidad (mi)": "Visibility(mi)",
    "Precipitación (in)": "Precipitation(in)",
    "Velocidad del viento (mph)": "Wind_Speed(mph)",
    "Temperatura (°F)": "Temperature(F)",
    "Hora del día": "Hora",
    "Día de la semana": "Dia_semana",
    "Semáforo": "Traffic_Signal",
    "Intersección": "Junction",
    "Cruce peatonal": "Crossing",
    "Señal de pare": "Stop",
    "Rotonda": "Roundabout",
    "Tipo de vía": "Tipo_via",
}
GRILLAS = {"Visibility(mi)": [0.25, 1, 3, 6, 10], "Precipitation(in)": [0, 0.05, 0.1, 0.25, 0.5],
           "Wind_Speed(mph)": [0, 5, 10, 20, 30, 40], "Temperature(F)": [0, 20, 32, 50, 70, 90, 100]}
BANDERAS_WHATIF = {"Traffic_Signal", "Junction", "Crossing", "Stop", "Roundabout"}


def _falta(v):
    return v is None or (isinstance(v, float) and np.isnan(v))


def grupos_netos(aportes):
    """Aporte NETO por grupo tematico (se suman los aportes de sus variables)."""
    from accidentes import config as cfg
    from accidentes.explain import grupo_de_variable
    netos = {}
    for variable, v in aportes.items():
        g = grupo_de_variable(variable, cfg.GRUPOS_TEMATICOS)
        netos[g] = netos.get(g, 0.0) + float(v)
    return netos


def valores_del_caso(predictor, df):
    """Valor legible de cada variable del modelo para este caso ('estimado' si el operador no lo dio)."""
    from accidentes.features import agregar_variables_temporales
    tabla, _ = predictor.validar(df)
    fila = agregar_variables_temporales(tabla).iloc[0]
    valores = {}
    for col, v in fila.items():
        if _falta(v) or (isinstance(v, float) and np.isnan(v)):
            valores[col] = "estimado"
        elif col == "Dia_semana":
            valores[col] = DIAS[int(v)]
        elif col == "Mes":
            valores[col] = MESES[int(v) - 1]
        elif col == "Hora":
            valores[col] = f"{int(v):02d} h"
        elif col == "Sunrise_Sunset":
            valores[col] = {"Day": "día", "Night": "noche"}.get(v, v)
        elif isinstance(v, (bool, np.bool_)):
            valores[col] = "sí" if v else "no"
        elif isinstance(v, (float, np.floating)):
            valores[col] = f"{v:.4g}"
        else:
            valores[col] = str(v)
    return valores


def analizar(predictor, entrada, umbral=None):
    """Prediccion + explicacion de UN incidente. `umbral=None` usa el oficial."""
    df = pd.DataFrame([entrada])
    resultado = predictor.predecir(df, umbral=umbral).iloc[0].to_dict()
    resultado["Es_critico"] = bool(resultado["Es_critico"])
    resultado["Campos_estimados"] = int(resultado["Campos_estimados"])
    aportes = base = grupos = None
    try:
        por_variable, base = predictor.explicar(df)
        aportes = {k: float(v) for k, v in por_variable.iloc[0].items()}
        base = float(base)
        grupos = grupos_netos(aportes)
    except RuntimeError:
        pass          # sin explicador_estado.json: la app sigue funcionando sin la explicacion
    return {"entrada": entrada, "resultado": resultado, "aportes": aportes, "base": base, "grupos": grupos,
            "valores": valores_del_caso(predictor, df),
            "umbral_usado": float(predictor.decision["umbral"] if umbral is None else umbral)}


def variantes(entrada, campo, opciones):
    """(etiquetas, filas, indice_actual, titulo) para variar UN campo y dejar el resto igual."""
    col = CAMPOS_WHATIF[campo]
    t = pd.Timestamp(entrada["Start_Time"])

    def con(**cambios):
        e = dict(entrada)
        e.update(cambios)
        return e

    if col == "Hora":
        return ([f"{h:02d} h" for h in range(24)], [con(Start_Time=t.replace(hour=h)) for h in range(24)],
                t.hour, "Hora del día")
    if col == "Dia_semana":
        return (list(DIAS), [con(Start_Time=t + pd.Timedelta(days=d - t.dayofweek)) for d in range(7)],
                t.dayofweek, "Día de la semana")
    actual_valor = entrada.get(col)
    if col in BANDERAS_WHATIF:
        valores = [np.nan, True, False]
        etiquetas = ["No sé (se estima)", "Sí", "No"]
        i = 0 if _falta(actual_valor) else (1 if bool(actual_valor) else 2)
        return etiquetas, [con(**{col: v}) for v in valores], i, etiqueta_variable(col)
    if col in ("Weather_Condition", "Tipo_via"):
        valores = [np.nan] + [o for o in opciones[col] if o != "Desconocido"]
        etiquetas = ["No sé (se estima)"] + valores[1:]
        i = 0 if _falta(actual_valor) else valores.index(actual_valor)
        return etiquetas, [con(**{col: v}) for v in valores], i, etiqueta_variable(col)
    grilla = sorted(set(GRILLAS[col]) | ({float(actual_valor)} if not _falta(actual_valor) else set()))
    valores = [np.nan] + grilla
    etiquetas = ["No sé (se estima)"] + [f"{g:g}" for g in grilla]
    i = 0 if _falta(actual_valor) else 1 + grilla.index(float(actual_valor))
    return etiquetas, [con(**{col: v}) for v in valores], i, etiqueta_variable(col)

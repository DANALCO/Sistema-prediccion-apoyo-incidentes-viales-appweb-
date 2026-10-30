"""
HISTORIAL DE CONSULTAS: cada analisis queda en datos_locales/historial.csv (en esta carpeta, no sale del
computador). Guarda la entrada completa en JSON para poder reabrir el caso en el formulario.
"""

import json
import math
from datetime import datetime

import numpy as np
import pandas as pd

from . import config

COLUMNAS = ["Consulta", "Fecha_consulta", "Start_Time", "State", "Start_Lat", "Start_Lng",
            "Probabilidad", "Nivel", "Umbral", "Campos_estimados", "Entrada_json"]


def _ruta():
    return config.dir_datos_locales() / "historial.csv"


def _limpio(v):
    """Valor serializable en JSON: NaN -> None, numpy -> python, fecha -> texto ISO."""
    if v is None:
        return None
    if isinstance(v, (pd.Timestamp, datetime)):
        return pd.Timestamp(v).isoformat()
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if math.isnan(float(v)) else float(v)
    return str(v)


def serializar(entrada):
    return json.dumps({k: _limpio(v) for k, v in entrada.items()}, ensure_ascii=False)


def deserializar(texto):
    d = json.loads(texto)
    if d.get("Start_Time"):
        d["Start_Time"] = pd.Timestamp(d["Start_Time"])
    return d


def leer():
    """Historial, el mas reciente primero (DataFrame vacio si no hay consultas)."""
    ruta = _ruta()
    if not ruta.exists():
        return pd.DataFrame(columns=COLUMNAS)
    df = pd.read_csv(ruta, encoding="utf-8-sig")
    return df.sort_values("Consulta", ascending=False).reset_index(drop=True)


def registrar(entrada, probabilidad, nivel, umbral, estimados):
    """Agrega una consulta y devuelve su numero."""
    previo = leer()
    numero = int(previo["Consulta"].max()) + 1 if len(previo) else 1
    fila = pd.DataFrame([{
        "Consulta": numero,
        "Fecha_consulta": datetime.now().isoformat(timespec="seconds"),
        "Start_Time": pd.Timestamp(entrada["Start_Time"]).isoformat(sep=" ", timespec="minutes"),
        "State": entrada["State"], "Start_Lat": entrada["Start_Lat"], "Start_Lng": entrada["Start_Lng"],
        "Probabilidad": round(float(probabilidad), 6), "Nivel": nivel, "Umbral": round(float(umbral), 6),
        "Campos_estimados": int(estimados), "Entrada_json": serializar(entrada),
    }], columns=COLUMNAS)
    ruta = _ruta()
    nuevo = not ruta.exists()
    fila.to_csv(ruta, mode="a", header=nuevo, index=False, encoding="utf-8-sig" if nuevo else "utf-8")
    return numero


def borrar():
    ruta = _ruta()
    if ruta.exists():
        ruta.unlink()

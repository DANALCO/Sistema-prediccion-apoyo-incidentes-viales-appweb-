"""
CARGA DE DATOS: el predictor y las tablas de models/reportes/ (todo cacheado).

El modelo y las tablas viven dentro de la carpeta de la app (los copia `sincronizar_modelo.py` desde el
repositorio del modelo); la app solo las lee. Si una tabla falta, la funcion devuelve None y la pagina
avisa que script la produce.
"""

import json

import pandas as pd
import streamlit as st

from . import config

# Que script del repositorio del modelo produce cada tabla (para el aviso cuando falta).
ORIGEN = {
    "patrones_de_riesgo.csv": "eda/patrones_de_riesgo.py",
    "perdida_tiempo_real.csv": "pipeline/03_entrenar_modelos.py (con los dos escenarios)",
    "importancia_global_tiempo_real.csv": "pipeline/04_explicabilidad_shap.py",
    "importancia_por_grupo_tiempo_real.csv": "pipeline/04_explicabilidad_shap.py",
    "curva_umbral_tiempo_real.csv": "pipeline/06_exportar_para_app.py",
    "zonas_vigilancia_tiempo_real.csv": "pipeline/03_entrenar_modelos.py",
    "tabla_comparativa_tiempo_real.csv": "pipeline/03_entrenar_modelos.py",
}


def iniciar():
    """Primera linea de cada pagina: comprueba que el modelo esta en la carpeta de la app o detiene la pagina."""
    aviso = config.aviso_de_instalacion()
    if aviso:
        st.error(aviso)
        st.stop()
    config.preparar_importacion()


@st.cache_resource(show_spinner="Cargando el modelo…")
def _cargar_predictor(ruta_modelos):
    from accidentes.inference import PredictorIncidentes
    return PredictorIncidentes.cargar(ruta_modelos, config.ESCENARIO)


def predictor():
    """El predictor (cacheado). Si no se puede cargar, explica por que en lugar de mostrar un traceback."""
    config.preparar_importacion()
    try:
        return _cargar_predictor(str(config.dir_modelos()))
    except ModuleNotFoundError as e:
        st.error(f"Falta instalar una librería: **{e.name}**. Ejecute `python -m pip install {e.name}` "
                 "(o `python -m pip install -r requirements.txt`) y reinicie la app.")
    except Exception as e:                                      # versiones distintas, archivo dañado, etc.
        st.error("No se pudo cargar el modelo. Lo más frecuente es que las librerías instaladas tengan "
                 "una versión distinta a la del entrenamiento (vea «Acerca del modelo» → versiones).\n\n"
                 f"Detalle técnico: `{type(e).__name__}: {e}`")
    st.stop()


@st.cache_data(show_spinner=False, ttl=300)      # si regenera los reportes, se refrescan solos en 5 minutos
def _leer(nombre, ruta_modelos):
    ruta = config.dir_modelos() / "reportes" / nombre
    return pd.read_csv(ruta, encoding="utf-8-sig") if ruta.exists() else None


def reporte(nombre):
    """DataFrame de models/reportes/<nombre> o None si no existe. La clave de cache incluye la carpeta."""
    return _leer(nombre, str(config.dir_modelos()))


def reporte_o_aviso(nombre):
    """Como `reporte`, pero si falta muestra el aviso con el script que lo produce."""
    df = reporte(nombre)
    if df is None:
        st.warning(f"Falta la tabla `models/reportes/{nombre}`. Se genera con "
                   f"`{ORIGEN.get(nombre, 'pipeline/06_exportar_para_app.py')}` en el repositorio del modelo; "
                   "luego ejecute `python sincronizar_modelo.py` para copiarla a la app.")
    return df


def nombre_reporte(base):
    return f"{base}_{config.ESCENARIO}.csv"


def umbral_activo():
    """Umbral que usa el analisis: el elegido en la pagina Umbral o None (= el oficial)."""
    return st.session_state.get("umbral_activo")


def _json(ruta):
    if not ruta.exists():
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False, ttl=300)
def _leer_json(nombre_relativo, ruta_modelos):
    return _json(config.dir_modelos() / nombre_relativo)


def ejemplos():
    """Casos reales de validacion (los escribe eda/ejemplos_para_app.py) o None si aun no existen."""
    return _leer_json("reportes/ejemplos_app.json", str(config.dir_modelos()))


def manifiesto():
    """Manifiesto de la exportacion (versiones, fecha, archivos) o None."""
    return _leer_json(f"manifest_{config.ESCENARIO}.json", str(config.dir_modelos()))


def sincronizacion():
    """Constancia que deja `sincronizar_modelo.py` (de donde y cuando se copio el modelo) o None."""
    return _leer_json("sincronizado.json", str(config.dir_modelos()))

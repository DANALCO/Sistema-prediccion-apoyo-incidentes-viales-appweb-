"""
APLICACION WEB - Sistema de apoyo a la decision para incidentes viales criticos.
Se ejecuta en local:   streamlit run app.py   (o doble clic en iniciar_app.bat)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

st.set_page_config(page_title="Incidentes viales críticos", page_icon=":material/traffic:", layout="wide")

from incidentes_app import config, datos, estilo

estilo.aplicar()
if hasattr(st, "logo"):
    st.logo(str(Path(__file__).resolve().parent / "assets" / "logo.svg"), size="large")

paginas = [
    st.Page("paginas/analizar.py", title="Analizar incidente", icon=":material/car_crash:", default=True),
    st.Page("paginas/explorador.py", title="Explorador de patrones", icon=":material/insights:"),
    st.Page("paginas/tiempo_real_vs_completa.py", title="Tiempo real vs completa", icon=":material/compare_arrows:"),
    st.Page("paginas/umbral.py", title="Umbral y costo", icon=":material/tune:"),
    st.Page("paginas/historial.py", title="Historial y exportación", icon=":material/history:"),
    st.Page("paginas/acerca.py", title="Acerca del modelo", icon=":material/info:"),
]
actual = st.navigation(paginas)

with st.sidebar:
    if not hasattr(st, "logo"):
        estilo.barra_lateral_marca()
    tau = st.session_state.get("umbral_activo")
    st.caption("Umbral de alerta: " + ("oficial" if tau is None else f"modificado ({tau:.1%})"))
    st.caption("Apoyo a la decisión: muestra asociaciones, no causas. La decisión final es de la persona.")
    try:                                   # aviso si las librerias no son las del entrenamiento
        if not config.problemas_de_instalacion():
            distintas = [v["libreria"] for v in config.comparar_versiones(datos.manifiesto())
                         if v["critica"] and not v["coincide"]]
            if distintas:
                st.warning("Versiones distintas a las del entrenamiento: " + ", ".join(distintas) +
                           ". El modelo podría fallar; vea «Acerca del modelo».")
    except Exception:
        pass

actual.run()

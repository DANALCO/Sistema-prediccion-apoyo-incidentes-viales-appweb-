"""Umbral y costo: que cuesta mover el umbral de decision (curva precisión global / recall)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # permite importar incidentes_app

import numpy as np
import streamlit as st

from incidentes_app import datos, estilo, graficos, ui

datos.iniciar()
predictor = datos.predictor()
estilo.encabezado("Umbral y costo",
                  "Ajuste qué tan sensible es el sistema y vea qué cuesta: detectar más incidentes críticos "
                  "también genera más falsas alarmas.")
st.write("El sistema marca un incidente como **crítico** cuando su riesgo estimado supera un **umbral** (τ). Un umbral "
         "bajo detecta más críticos pero genera más falsas alarmas; uno alto hace lo contrario. Aquí se ve qué cuesta "
         "cada valor, sin recalcular nada: son resultados de la evaluación sobre **test** (datos posteriores al "
         "entrenamiento).")

curva = datos.reporte_o_aviso(datos.nombre_reporte("curva_umbral"))
if curva is None:
    st.stop()
c = curva[curva["Particion"] == "test"].sort_values("Alertas_%").reset_index(drop=True)
i_ofi = int(np.flatnonzero(c["Es_umbral_oficial"].astype(bool).to_numpy())[0])

# El umbral activo (si lo hay) decide donde empieza el control.
activo = datos.umbral_activo()
if "slider_umbral" not in st.session_state:
    st.session_state["slider_umbral"] = i_ofi if activo is None else int((c["Umbral"] - activo).abs().idxmin())

i = st.select_slider("Umbral, expresado como % de incidentes que se marcan como críticos", options=list(range(len(c))),
                     format_func=lambda k: f"{c['Alertas_%'].iloc[k]:.2f} %  ·  τ = {c['Umbral'].iloc[k]:.4f}"
                                           f"{'  (oficial)' if k == i_ofi else ''}", key="slider_umbral")
f = c.iloc[i]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Precisión global", f"{f['Exactitud']:.4f}",
          help=f"De cada 100 incidentes, en cuántos acierta. Referencia: decir siempre «todo normal» tendría {f['Baseline']:.4f}, "
               "porque los críticos son pocos.")
m2.metric("Recall", f"{f['Recall']:.3f}", help="De cada 100 incidentes críticos, cuántos detecta.")
m3.metric("Precisión de las alertas", f"{f['Precision']:.3f}", help="De cada 100 alertas, cuántas eran realmente críticas.")
m4.metric("F1", f"{f['F1']:.3f}")

st.markdown("**Por cada 1,000 incidentes:**")
d1, d2, d3 = st.columns(3)
d1.metric("Críticos detectados", f"{f['Criticos_detectados_x1000']:.1f}")
d2.metric("Falsas alarmas", f"{f['Falsas_alarmas_x1000']:.1f}")
d3.metric("Críticos que se pierden", f"{f['Criticos_perdidos_x1000']:.1f}")

ui.grafico(graficos.fig_umbral(c, i, i_ofi), key="g_umbral")
if not (c["Exactitud"] >= c["Baseline"]).any():
    st.info(f"Ningún umbral supera la precisión global de «todo normal» ({f['Baseline']:.4f}): como solo una pequeña parte de "
            "los incidentes es crítica, decir siempre «normal» acierta casi siempre pero no detecta ninguno. Por eso "
            "el sistema se evalúa también por recall, precisión de las alertas y PR-AUC, y la precisión global se muestra siempre junto a "
            "esa referencia.")
st.caption("Las cifras son de una evaluación histórica: orientativas, no una garantía para incidentes futuros (la "
           "tasa de críticos cambia con el tiempo).")

st.divider()
a, b, _ = st.columns([2, 2, 3])
if a.button("Usar este umbral en «Analizar incidente»", type="primary", disabled=(i == i_ofi and activo is None)):
    st.session_state["umbral_activo"] = None if i == i_ofi else float(f["Umbral"])
    st.rerun()


def _volver_al_oficial(posicion_oficial):
    """Callback del boton: corre ANTES de dibujar el control, asi puede moverlo (despues de dibujarlo, no)."""
    st.session_state["umbral_activo"] = None
    st.session_state["slider_umbral"] = posicion_oficial


b.button("Volver al umbral oficial", disabled=activo is None, on_click=_volver_al_oficial, args=(i_ofi,))
if activo is None:
    st.success(f"Análisis con el umbral oficial (τ = {predictor.decision['umbral']:.4f}), el que se evaluó en test.")
else:
    st.warning(f"Los análisis nuevos usan τ = {activo:.4f}. La franja de vigilancia se reescala en la misma proporción.")

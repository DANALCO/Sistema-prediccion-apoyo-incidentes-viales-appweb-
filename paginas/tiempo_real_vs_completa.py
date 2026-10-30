"""Tiempo real vs informacion completa (pregunta de investigacion 4): resultados precalculados."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # permite importar incidentes_app

import streamlit as st

from incidentes_app import datos, estilo, graficos, ui
from incidentes_app.etiquetas import etiqueta_metodo

METRICAS = {"PR_AUC": "PR-AUC", "ROC_AUC": "ROC-AUC", "Recall": "Recall", "Precision": "Precisión de las alertas",
            "F1": "F1", "Exactitud": "Precisión global"}

datos.iniciar()
predictor = datos.predictor()
estilo.encabezado("Tiempo real vs información completa",
                  "¿Qué tan buenas son las predicciones con lo que se sabe al reportar el accidente, frente a las del "
                  "registro completo?")
st.markdown("**Pregunta 4.** ¿Qué tanta precisión se pierde al predecir con solo la información disponible al "
            "reportar el incidente, frente a un modelo con el registro completo?")
st.write("Se entrenaron los mismos modelos, con la misma partición temporal y el mismo protocolo, en dos escenarios: "
         "**tiempo real** (lo que se sabe al reportar; el que usa esta app) e **información completa** (agrega "
         "`Distance(mi)`, la longitud afectada, que solo se conoce después). Resultados sobre el conjunto de test.")

perdida = datos.reporte_o_aviso("perdida_tiempo_real.csv")
if perdida is None:
    st.stop()

final = predictor.decision.get("metodo_final", "Stacking")
metrica = st.radio("Métrica", list(METRICAS), format_func=METRICAS.get, horizontal=True, key="metrica_pi4")
ui.grafico(graficos.fig_perdida(perdida, metrica, etiqueta_metodo), key="g_perdida")

f = perdida[perdida["Metodo"] == final]
if not f.empty:
    f = f.iloc[0]
    tr, co, dif = f[f"{metrica}_tiempo_real"], f[f"{metrica}_completa"], f[f"{metrica}_perdida"]
    if abs(dif) < 5e-4:
        veredicto = "prácticamente no cambia"
    elif dif > 0:
        veredicto = f"baja {dif:.3f} al operar en tiempo real (la información posterior ayuda)"
    else:
        veredicto = f"es {abs(dif):.3f} mayor en tiempo real (la información posterior no ayuda)"
    st.markdown(f"**Método final ({etiqueta_metodo(final)}), {METRICAS[metrica]}:** {tr:.3f} en tiempo real y "
                f"{co:.3f} con información completa; {veredicto}.")

st.caption("«Pérdida» = completa − tiempo real: positivo significa que la información posterior ayuda. PR-AUC y "
           "ROC-AUC no dependen de ningún umbral; Recall, Precisión de las alertas, F1 y Precisión global usan el umbral de cada escenario "
           "(elegido en validación), por lo que comparan también esa elección.")
with st.expander("Ver la tabla completa"):
    cols = ["Metodo"] + [f"{m}_{s}" for m in METRICAS for s in ("tiempo_real", "completa", "perdida")]
    tabla = perdida[[c for c in cols if c in perdida.columns]].copy()
    tabla["Metodo"] = [etiqueta_metodo(m) for m in tabla["Metodo"]]
    sufijo = {"tiempo_real": "tiempo real", "completa": "información completa", "perdida": "pérdida"}
    tabla = tabla.rename(columns={f"{m}_{s}": f"{nombre} · {sufijo[s]}"
                                  for m, nombre in METRICAS.items() for s in sufijo})
    ui.tabla(tabla.round(4), hide_index=True)

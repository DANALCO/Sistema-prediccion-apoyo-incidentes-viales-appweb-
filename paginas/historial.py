"""Historial de consultas y exportacion (se guarda en datos_locales/historial.csv)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # permite importar incidentes_app

import streamlit as st

from incidentes_app import datos, estilo, exportar, historial, ui
from incidentes_app.etiquetas import ZONA_TEXTO, ZONAS

datos.iniciar()
estilo.encabezado("Historial y exportación",
                  "Cada análisis queda guardado en su computador. Puede reabrir un caso o descargar el historial.")

h = historial.leer()
if h.empty:
    st.info("Aún no hay consultas. Cada análisis que haga en «Analizar incidente» queda guardado aquí, en su "
            "computador.")
    st.stop()

if st.session_state.pop("_ir_a_analizar", False):
    st.switch_page("paginas/analizar.py")


def reabrir(entrada_json):
    st.session_state["_cargar"] = historial.deserializar(entrada_json)
    st.session_state["_ir_a_analizar"] = True


st.write(f"**{len(h)}** {'consulta guardada' if len(h) == 1 else 'consultas guardadas'} en `datos_locales/historial.csv`.")
cols = st.columns(len(ZONAS))
for col, z in zip(cols, ZONAS):
    col.metric(ZONA_TEXTO[z], int((h["Nivel"] == z).sum()))

filtro = st.multiselect("Filtrar por zona", ZONAS, default=ZONAS, format_func=ZONA_TEXTO.get)
vista = h[h["Nivel"].isin(filtro)].reset_index(drop=True)
mostrar = vista.drop(columns=["Entrada_json"]).copy()
mostrar["Nivel"] = [ZONA_TEXTO[z] for z in mostrar["Nivel"]]
mostrar["Probabilidad"] = mostrar["Probabilidad"].map(lambda p: f"{p:.1%}")
evento = ui.tabla(mostrar, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_historial")
filas = evento.selection.rows if evento is not None and hasattr(evento, "selection") else []
if filas:
    elegida = vista.iloc[filas[0]]
    st.button(f"Reabrir la consulta n.º {int(elegida['Consulta'])} en el formulario", type="primary",
              on_click=reabrir, args=(elegida["Entrada_json"],))
else:
    st.caption("Seleccione una fila para volver a abrir ese caso en el formulario.")

st.divider()
st.markdown("**Exportar**")
a, b = st.columns(2)
with a:
    ui.boton_descarga("Historial (CSV, resumen)", exportar.csv_bytes(vista.drop(columns=["Entrada_json"])),
                      "historial_resumen.csv", "text/csv", "d_hist_resumen")
with b:
    ui.boton_descarga("Historial (CSV, con la entrada completa)", exportar.csv_bytes(vista),
                      "historial_completo.csv", "text/csv", "d_hist_completo")

with st.expander("Borrar el historial"):
    if st.checkbox("Entiendo que se borran todas las consultas guardadas", key="confirma_borrar"):
        if st.button("Borrar historial"):
            historial.borrar()
            st.session_state.pop("ultimo", None)
            st.rerun()

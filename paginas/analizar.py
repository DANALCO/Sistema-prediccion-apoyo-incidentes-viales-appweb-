"""Analizar un incidente: formulario, prediccion, zona, recomendacion, SHAP, que pasaria si, exportar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # permite importar incidentes_app

import json

import streamlit as st

from incidentes_app import analisis, datos, estilo, formulario, historial, ui, vista_caso
from incidentes_app.etiquetas import ZONA_TEXTO

datos.iniciar()
predictor = datos.predictor()
formulario.restaurar_y_aplicar_pendiente()

estilo.encabezado(
    "Analizar un incidente",
    "Cuente qué se sabe del accidente al recibir el aviso. El sistema estima qué tan probable es que cause un "
    "impacto crítico en el tráfico, sugiere qué hacer y explica por qué.",
    pasos=["Complete lo que sepa", "Pulse «Analizar»", "Siga la recomendación"])

tau_activo = datos.umbral_activo()
if tau_activo is not None:
    st.warning(f"Está usando un umbral distinto del oficial ({tau_activo:.1%}). Cámbielo en la página «Umbral y costo».")


def etiqueta_ejemplo(ej):
    return (f"{ZONA_TEXTO[ej['zona']]} · en los datos {'fue crítico' if ej['real_critico'] else 'no fue crítico'}"
            f" · riesgo {ej['probabilidad']:.1%}")


def cargar_ejemplo_real(lista):
    ej = next((e for e in lista if e["id"] == st.session_state.get("sel_ejemplo_real")), None)
    if ej is not None:
        formulario.escribir_estado(historial.deserializar(json.dumps(ej["entrada"])))
        st.session_state["ejemplo_real"] = ej


ejemplos = datos.ejemplos()
with st.expander("¿Quiere probar con un caso real? (casos de validación para ver cada zona)"):
    if not ejemplos:
        st.caption("Aún no hay casos reales cargados. En el repositorio del modelo ejecute "
                   "`python eda/ejemplos_para_app.py`, copie el resultado con `python sincronizar_modelo.py` y "
                   "reinicie la app: genera un caso por zona a partir de datos de validación.")
    else:
        por_id = {e["id"]: e for e in ejemplos}
        st.selectbox("Caso", list(por_id), index=None, placeholder="Elija un caso", key="sel_ejemplo_real",
                     format_func=lambda i: etiqueta_ejemplo(por_id[i]))
        st.button("Cargar este caso en el formulario", on_click=cargar_ejemplo_real, args=(ejemplos,))
        st.caption("Son incidentes reales de datos de validación (no del test). Después de analizar uno, la app "
                   "compara lo que dijo el modelo con lo que pasó de verdad. Un caso aislado no mide el modelo.")

formulario.dibujar(predictor.opciones_formulario())

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
b1, b2, b3, _ = st.columns([1.3, 1, 1, 1.4])
with b1:
    analizar = ui.boton("Analizar incidente", type="primary", icon=":material/analytics:")
with b2:
    ui.boton("Cargar ejemplo", on_click=formulario.escribir_estado, args=(formulario.EJEMPLO,),
             help="Llena el formulario con un incidente real de pruebas.", icon=":material/science:")
with b3:
    ui.boton("Vaciar formulario", on_click=formulario.vaciar, icon=":material/delete_sweep:")
formulario.guardar_para_navegar()

if analizar:
    try:
        entrada = formulario.leer_estado()
        with st.spinner("Calculando el riesgo y la explicación…"):
            ultimo = analisis.analizar(predictor, entrada, tau_activo)
    except ValueError as e:
        st.error(str(e))
    else:
        r = ultimo["resultado"]
        ej = st.session_state.get("ejemplo_real")      # solo cuenta si el formulario sigue siendo ese caso
        ultimo["ejemplo_real"] = ej if (ej and ej["entrada"]["State"] == entrada["State"]
                                        and abs(ej["probabilidad"] - r["Probabilidad"]) < 2e-3) else None
        ultimo["ubicacion_aproximada"] = formulario.ubicacion_aproximada(entrada)
        ultimo["consulta"] = historial.registrar(entrada, r["Probabilidad"], r["Nivel"], ultimo["umbral_usado"],
                                                 r["Campos_estimados"])
        st.session_state["ultimo"] = ultimo

if "ultimo" in st.session_state:
    ultimo = st.session_state["ultimo"]
    st.divider()
    st.subheader(f"Resultado · consulta n.º {ultimo['consulta']}")
    st.caption("Si cambia algo del formulario, pulse «Analizar incidente» otra vez para actualizar el resultado.")
    vista_caso.mostrar(ultimo, predictor)
else:
    estilo.vacio("🚦", "Aquí aparecerá el resultado",
                 "Complete el estado (lo único obligatorio) y pulse «Analizar incidente», o pruebe «Cargar ejemplo».")

"""Acerca del modelo: que hace el sistema, cuanto se puede confiar en el, y las reglas de gestion."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # permite importar incidentes_app

import pandas as pd
import streamlit as st

from incidentes_app import config, datos, estilo, reglas, ui
from incidentes_app.etiquetas import ZONA_TEXTO, etiqueta_metodo

datos.iniciar()
predictor = datos.predictor()
d = predictor.decision
estilo.encabezado("Acerca del modelo",
                  "Qué hace el sistema, qué tan confiable es y qué límites tiene.")

st.markdown(
    "**Qué hace.** Estima, con la información disponible **al momento de reportar** un accidente, la probabilidad de "
    "que su impacto en el tráfico sea **crítico** (Severity ≥ 3 en el conjunto *US Accidents*). La etiqueta mide el "
    "impacto operativo en la vía, **no** la gravedad médica de las personas.\n\n"
    f"**Cómo decide.** Cuatro modelos (Random Forest, XGBoost, LightGBM y regresión logística) entrenados con pesos de "
    f"clase se combinan con un apilador ({etiqueta_metodo(d.get('metodo_final', 'Stacking'))}). El incidente es crítico si "
    f"el riesgo supera τ = **{d['umbral']:.4f}**, elegido en validación como el mayor recall que mantiene la precisión global "
    f"en al menos {d.get('exactitud_minima_validacion', 0.94):.2f}. Alrededor de τ hay una franja de **vigilancia**.")

manifiesto = datos.manifiesto() or {}
creado = manifiesto.get("creado", "")
st.caption(f"Modelo cargado desde `{config.dir_modelos() / config.ESCENARIO}`" + (f" · exportado el {creado[:10]}" if creado else ""))

with st.expander("Detalles de la instalación (para quien mantiene la app)"):
    sinc = datos.sincronizacion()
    st.markdown(
        f"- **Código del modelo en uso:** `{config.origen_del_codigo()}`\n"
        f"- **Modelos y tablas:** `{config.dir_modelos()}`\n"
        + (f"- **Última sincronización:** {sinc['sincronizado'][:16].replace('T', ' ')} desde `{sinc['origen']}`\n" if sinc else
           "- **Última sincronización:** sin registro (copiado a mano)\n"))
    versiones = config.comparar_versiones(manifiesto)
    ui.tabla(pd.DataFrame([{"Librería": v["libreria"], "Al entrenar": v["exportado"], "Instalada": v["instalado"],
                            "Estado": "igual" if v["coincide"] else ("DISTINTA (puede fallar)" if v["critica"] else "distinta")}
                           for v in versiones]), hide_index=True)
    st.caption("scikit-learn, xgboost y lightgbm deben coincidir exactamente con las del entrenamiento; "
               "`python sincronizar_modelo.py --solo-verificar` lo comprueba desde la consola.")

comparativa = datos.reporte(datos.nombre_reporte("tabla_comparativa"))
if comparativa is not None:
    st.subheader("Resultados en test del método final")
    f = comparativa[(comparativa["Particion"] == "test") & (comparativa["Metodo"] == d.get("metodo_final", "Stacking"))]
    if not f.empty:
        f = f.iloc[0]
        cols = st.columns(4)
        for col, (nombre, clave) in zip(cols * 2, [("Precisión global", "Exactitud"), ("«Todo normal»", "Baseline"),
                                                    ("Recall", "Recall"), ("Precisión de las alertas", "Precision"),
                                                    ("F1", "F1"), ("PR-AUC", "PR_AUC"), ("ROC-AUC", "ROC_AUC"),
                                                    ("Alertas (%)", "Alertas_%")]):
            col.metric(nombre, f"{f[clave]:.4f}" if clave != "Alertas_%" else f"{f[clave]:.2f}")
        st.caption("La precisión global se muestra siempre junto a la de «todo normal» porque los críticos son pocos.")

zonas = datos.reporte(datos.nombre_reporte("zonas_vigilancia"))
if zonas is not None:
    st.subheader("Las cuatro zonas, en test")
    z = zonas[zonas["Particion"] == "test"].copy()
    z["Zona"] = [ZONA_TEXTO.get(x, x) for x in z["Zona"]]
    z = z.rename(columns={"Pct_incidentes": "% de los incidentes", "Pct_critico_en_zona": "% críticos en la zona",
                          "Veces_la_tasa_base": "Veces la tasa base"})
    ui.tabla(z[["Zona", "Incidentes", "% de los incidentes", "Criticos", "% críticos en la zona",
                "Veces la tasa base"]].round(2), hide_index=True)

st.subheader("Reglas de gestión (pregunta 5)")
st.caption(reglas.cargar_reglas()["aviso"])
for r in reglas.tabla_de_reglas():
    with st.expander(f"{ZONA_TEXTO[r['Zona']]} — {r['Titulo']} (prioridad {r['Prioridad'].lower()})"):
        for a in r["Acciones"]:
            st.markdown(f"- {a}")

st.subheader("Límites que conviene tener presentes")
st.markdown(
    "- **El tiempo cambia.** La tasa de críticos varía mes a mes; las cifras de test describen un periodo concreto y "
    "el modelo conviene reentrenarlo periódicamente.\n"
    "- **La ubicación pesa mucho.** Pocos estados concentran muchos incidentes y parte de la capacidad de distinguir "
    "casos viene de saber *dónde* ocurrió; dentro de un mismo estado distingue menos.\n"
    "- **La probabilidad es una estimación global.** En un estado o tramo concreto puede quedar por encima o por "
    "debajo de la frecuencia real.\n"
    "- **Asociación, no causa.** Ni SHAP, ni el explorador, ni «qué pasaría si» demuestran que cambiar un factor "
    "cambie el impacto.\n"
    "- **Campos estimados.** Cuando faltan datos opcionales, el modelo usa valores típicos y la predicción es menos "
    "fiable (la app avisa cuántos).\n"
    "- **Alcance.** Entrenado y evaluado con accidentes de EE. UU.; no se ha validado en otros países.\n"
    "- **Apoyo, no sustituto.** El sistema ayuda al operador a priorizar; la decisión final es de la persona.")

with st.expander("Glosario: palabras que aparecen en la app"):
    st.markdown(
        "- **Incidente crítico:** accidente con un impacto fuerte en el tráfico (en los datos, gravedad 3 o 4 de 4). "
        "Mide el efecto en la vía, no la gravedad de las lesiones.\n"
        "- **Riesgo estimado:** probabilidad (de 0 a 100 %) que calcula el modelo de que el incidente sea crítico.\n"
        "- **Umbral:** riesgo mínimo a partir del cual el sistema marca un incidente como crítico.\n"
        "- **Zona:** Normal (riesgo bajo), Vigilancia (intermedio, cerca del umbral) o Crítico (sobre el umbral).\n"
        "- **Falsa alarma:** el sistema marcó un incidente como crítico y no lo era. "
        "**Crítico perdido:** lo era y no se marcó.\n"
        "- **Recall (sensibilidad):** de cada 100 incidentes críticos reales, cuántos detecta.\n"
        "- **Precisión de las alertas:** de cada 100 alertas, cuántas eran críticas de verdad.\n"
        "- **Precisión global:** de cada 100 incidentes, en cuántos acertó. Ojo: como los críticos son pocos, decir «todo es "
        "normal» ya tiene una precisión global alta; por eso se compara con ese valor.\n"
        "- **SHAP:** método que reparte el riesgo de un caso entre los datos para mostrar cuánto empujó cada uno.\n"
        "- **Datos que faltaban (campos estimados):** datos opcionales que no se informaron; el sistema usó valores típicos.\n"
        "- **Tiempo real / información completa:** lo que se sabe al reportar el accidente frente al registro completo, "
        "que incluye datos que solo se conocen después (por ejemplo, cuántas millas de vía afectó).")

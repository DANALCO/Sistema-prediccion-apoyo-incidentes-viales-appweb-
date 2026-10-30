"""
PANTALLA DE RESULTADO DE UN CASO: zona, recomendacion (PI 5) y las pestanas Por que (SHAP),
Que pasaria si, Como se calculo y Exportar.
"""

import numpy as np
import pandas as pd
import streamlit as st

from . import analisis, datos, estilo, exportar, graficos, historial, reglas, ui
from .ayudas import AYUDA_RESULTADO
from .etiquetas import ZONA_TEXTO, etiqueta_metodo


@st.cache_data(show_spinner=False)
def _probabilidades(_predictor, entrada_json, campo, umbral):
    """Probabilidad de cada variante del «que pasaria si» (cacheada por caso, campo y umbral)."""
    entrada = historial.deserializar(entrada_json)
    for k, v in list(entrada.items()):                       # el JSON guarda None donde faltaba el dato
        if v is None:
            entrada[k] = np.nan
    etiquetas, filas, i, titulo = analisis.variantes(entrada, campo, _predictor.opciones_formulario())
    probs = _predictor.predecir(pd.DataFrame(filas), umbral=umbral)["Probabilidad"].to_numpy()
    return etiquetas, probs.tolist(), i, titulo


def _evidencia(nivel, umbral_usado, umbral_oficial):
    """Frase con el % de criticos de la zona en test (solo vale con el umbral oficial)."""
    zonas = datos.reporte(datos.nombre_reporte("zonas_vigilancia"))
    if zonas is None or abs(umbral_usado - umbral_oficial) > 1e-12:
        return None
    f = zonas[(zonas["Particion"] == "test") & (zonas["Zona"] == nivel)]
    if f.empty:
        return None
    f = f.iloc[0]
    return (f"En la evaluación sobre test, el {f['Pct_critico_en_zona']:.1f} % de los incidentes que cayeron en esta "
            f"zona resultaron críticos ({f['Veces_la_tasa_base']:.1f} veces la tasa base). "
            f"Cifra histórica y orientativa.")


def mostrar(ultimo, predictor):
    r = ultimo["resultado"]
    nivel, p, tau = r["Nivel"], r["Probabilidad"], ultimo["umbral_usado"]
    oficial = float(predictor.decision["umbral"])
    modificado = abs(tau - oficial) >= 1e-12
    aproximada = ultimo.get("ubicacion_aproximada", False)

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    estilo.tarjeta_zona(nivel, p, estilo.bordes_de_zona(predictor.decision, tau), umbral_modificado=modificado)
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Decisión", "Alerta crítica" if r["Es_critico"] else "Sin alerta crítica",
              help=AYUDA_RESULTADO["decision"])
    c2.metric("Umbral de alerta", f"{tau:.1%}", help=AYUDA_RESULTADO["umbral"] + (
        "" if not modificado else f" **Está modificado** (el oficial es {oficial:.1%})."))
    c3.metric("Datos que faltaban", r["Campos_estimados"], help=AYUDA_RESULTADO["estimados"])
    ev = _evidencia(nivel, tau, oficial)
    if ev:
        st.caption("📊 " + ev)
    if aproximada:
        st.warning("**Ubicación aproximada.** No se indicó el lugar exacto, así que se usó el centro del estado y el "
                   "resultado es menos preciso. Vuelva a analizar eligiendo una ciudad, la dirección o el mapa.")
    if ultimo.get("ejemplo_real"):
        _comparar_con_la_realidad(ultimo["ejemplo_real"], r)

    # ---- Recomendacion de gestion (PI 5) ----
    grupo = reglas.grupo_dominante(ultimo["grupos"])
    rec = reglas.recomendar(nivel, grupo, r["Campos_estimados"])
    with st.container(border=True):
        st.markdown(f"### Qué hacer: {rec['titulo']}")
        st.markdown(f"<span class='chip'>Prioridad {rec['prioridad'].lower()}</span>", unsafe_allow_html=True)
        for a in rec["acciones"]:
            st.markdown(f"- {a}")
        if rec["nota_factor"]:
            st.info(rec["nota_factor"])
        if rec["nota_datos"]:
            st.warning(rec["nota_datos"])
        st.caption(rec["aviso"])
    ultimo["recomendacion"] = rec

    with st.expander("Ubicación en el mapa"):
        e = ultimo["entrada"]
        st.map(pd.DataFrame({"lat": [e["Start_Lat"]], "lon": [e["Start_Lng"]]}), zoom=9)
        st.caption("Aproximada (centro del estado)." if aproximada else f"Coordenadas: {e['Start_Lat']:.4f}, {e['Start_Lng']:.4f}")

    st.markdown("#### Detalles del análisis")
    t1, t2, t3, t4 = st.tabs(["Por qué este resultado", "Qué pasaría si…", "Cómo se calculó (técnico)", "Descargar"])
    with t1:
        _tab_shap(ultimo)
    with t2:
        _tab_que_pasaria_si(ultimo, predictor)
    with t3:
        _tab_calculo(ultimo, predictor)
    with t4:
        _tab_exportar(ultimo, rec, oficial, ev)


def _comparar_con_la_realidad(ej, r):
    """Caso real de validacion: lo que paso de verdad frente a lo que dijo el modelo."""
    zona = ZONA_TEXTO[r["Nivel"]]
    if ej["real_critico"] and r["Es_critico"]:
        st.success(f"**Caso real de validación.** En los datos este incidente **fue crítico** y el modelo lo marcó "
                   f"como crítico (zona {zona}): acierto.")
    elif ej["real_critico"]:
        extra = " pero lo dejó en vigilancia, justo bajo el umbral" if r["Nivel"] == "Vigilancia (bajo el umbral)" else ""
        st.warning(f"**Caso real de validación.** En los datos este incidente **fue crítico** y el modelo **no lo "
                   f"marcó**{extra} (zona {zona}): crítico perdido.")
    elif r["Es_critico"]:
        st.info(f"**Caso real de validación.** En los datos este incidente **no fue crítico** y el modelo lo marcó "
                f"(zona {zona}): falsa alarma.")
    else:
        st.success(f"**Caso real de validación.** En los datos este incidente **no fue crítico** y el modelo no lo "
                   f"marcó (zona {zona}): acierto.")
    st.caption("Un caso aislado no mide el modelo: la evaluación completa está en «Acerca del modelo» y «Umbral y costo».")


def _tab_shap(u):
    if u["aportes"] is None:
        st.info("No hay `explicador_estado.json` en el modelo; ejecute `pipeline/04_explicabilidad_shap.py` y "
                "`pipeline/06_exportar_para_app.py` en el repositorio del modelo.")
        return
    base_p = 1 / (1 + np.exp(-u["base"]))
    st.markdown(f"**Qué datos empujaron el riesgo de este caso** (método SHAP). El modelo parte de un riesgo base de "
                f"**{base_p:.1%}** (el de un incidente promedio) y cada dato lo sube (rojo) o lo baja (azul).")
    ui.grafico(graficos.fig_aportes_caso(u["aportes"], u["valores"]), key="g_shap_caso")
    st.markdown("**Por grupo de variables**")
    ui.grafico(graficos.fig_grupos(u["grupos"]), key="g_shap_grupos")
    st.caption("Es lo que el modelo aprendió de los datos históricos (asociación, no causa). «estimado» = ese dato no se "
               "informó y se usó un valor típico. La ubicación suele pesar mucho porque la proporción de críticos "
               "cambia de un estado a otro. Las barras están en escala logit: lo importante es su signo y su tamaño relativo.")


def _tab_que_pasaria_si(u, predictor):
    st.markdown("Cambie **un** dato del caso y vea cómo se mueve el riesgo, dejando todo lo demás igual.")
    campo = st.selectbox("Campo a variar", list(analisis.CAMPOS_WHATIF), key="whatif_campo")
    entrada_json = historial.serializar(u["entrada"])
    etiquetas, probs, i, titulo = _probabilidades(predictor, entrada_json, campo, u["umbral_usado"])
    ui.grafico(graficos.fig_que_pasaria_si(etiquetas, probs, i, u["umbral_usado"], titulo), key="g_whatif")
    actual = probs[i]
    delta = pd.DataFrame({"Valor": etiquetas, "Riesgo": [f"{x:.2%}" for x in probs],
                          "Cambio frente al caso": [f"{(x - actual) * 100:+.2f} pp" for x in probs]})
    ui.tabla(delta, hide_index=True)
    st.caption("Barra azul = el caso tal como se reportó. «pp» = puntos porcentuales. Es la sensibilidad del "
               "**modelo**, no un efecto causal: en la vida real, cambiar un factor suele cambiar otros. "
               "Con «Hora del día» el campo día/noche no se mueve solo.")


def _tab_calculo(u, predictor):
    r = u["resultado"]
    beta = predictor.decision["coeficientes_apilador"]
    filas, total = [], beta["intercepto"]
    for m in predictor.modelos:
        pm = float(np.clip(r[f"Prob_{m}"], 1e-12, 1 - 1e-12))
        z = float(np.log(pm / (1 - pm)))
        total += beta[m] * z
        filas.append({"Modelo": etiqueta_metodo(m), "Probabilidad cruda": f"{pm:.4f}", "logit": f"{z:+.4f}",
                      "Peso β": f"{beta[m]:+.4f}", "Aporte β·logit": f"{beta[m] * z:+.4f}"})
    st.markdown("Cuatro modelos estiman el riesgo por separado y un **apilador** los combina en la escala logit:")
    st.latex(r"\operatorname{logit}\,p(x)=\beta_0+\sum_{m=1}^{4}\beta_m\,\operatorname{logit}\,P_m(x)"
             r"\qquad p(x)=\frac{1}{1+e^{-\operatorname{logit}\,p(x)}}")
    ui.tabla(pd.DataFrame(filas), hide_index=True)
    st.markdown(f"Intercepto β₀ = **{beta['intercepto']:+.4f}** → logit p = **{total:+.4f}** → "
                f"p = **{r['Probabilidad']:.4f}**. Decisión: crítico si p ≥ τ = {u['umbral_usado']:.4f}.")
    st.caption("Las probabilidades crudas salen de modelos entrenados con pesos de clase, por eso son altas; el apilador "
               "las recalibra. Los pesos β se ajustaron en la partición de validación, nunca en test.")


def _tab_exportar(u, rec, oficial, evidencia):
    r = u["resultado"]
    plano = pd.DataFrame([exportar.fila_plana(u["entrada"], r, u["umbral_usado"], rec)])
    st.markdown("Descargue este análisis (también queda en el **Historial**).")
    a, b, c = st.columns(3)
    with a:
        ui.boton_descarga("CSV (una fila)", exportar.csv_bytes(plano), "incidente.csv", "text/csv", "d_csv")
    with b:
        ui.boton_descarga("JSON (completo)", exportar.ficha_json(u["entrada"], r, u["umbral_usado"], rec, u["aportes"],
                                                                 u["base"], u["grupos"], oficial),
                          "incidente.json", "application/json", "d_json")
    with c:
        ui.boton_descarga("Ficha HTML (imprimible)", exportar.ficha_html(u["entrada"], r, u["umbral_usado"], rec,
                                                                         u["aportes"], u["grupos"], oficial, evidencia),
                          "ficha_incidente.html", "text/html", "d_html")
    st.caption("La ficha HTML se abre en el navegador; use Imprimir → Guardar como PDF si la necesita en PDF.")

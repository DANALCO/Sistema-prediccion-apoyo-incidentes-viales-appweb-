"""Explorador de patrones (preguntas de investigacion 1, 2 y 3): riesgo observado por condicion + peso en el modelo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # permite importar incidentes_app

import pandas as pd
import streamlit as st

from incidentes_app import datos, estilo, graficos, ui
from incidentes_app.etiquetas import etiqueta_categoria, etiqueta_variable

PREGUNTAS = {
    1: ("Clima y visibilidad", "¿Qué condiciones climáticas y de visibilidad están más asociadas con accidentes de "
                               "alto impacto en el tráfico?"),
    2: ("Patrones temporales", "¿Existen patrones temporales (hora, día, estación) relacionados con un mayor impacto "
                               "en el tráfico?"),
    3: ("Infraestructura", "¿La infraestructura vial (cruces, semáforos, rotondas) influye en el nivel de impacto de "
                           "un accidente?"),
}

datos.iniciar()
estilo.encabezado("Explorador de patrones",
                  "¿En qué condiciones los accidentes suelen tener más impacto en el tráfico? Aquí se ve qué porcentaje "
                  "de los incidentes fue crítico en cada condición, comparado con el promedio. Son datos históricos; "
                  "no usan el modelo.")

patrones = datos.reporte_o_aviso("patrones_de_riesgo.csv")
if patrones is None:
    st.stop()
imp = datos.reporte(datos.nombre_reporte("importancia_global"))
n_vars = len(imp) if imp is not None else None


def puesto(variable):
    if imp is None:
        return None
    f = imp[imp["Variable"] == variable]
    return None if f.empty else (int(f["Ranking"].iloc[0]), float(f["Aporte_abs_medio_real"].iloc[0]))


def resumen_por_variable(t):
    """Por variable: categoria menos y mas riesgosa entre las que tienen suficientes casos."""
    filas = []
    validas = t[(t["Categoria"].astype(str) != "sin dato") & (~t["Pocos_casos"].astype(bool))]
    for variable, d in validas.groupby("Variable", sort=False):
        if len(d) < 2:
            continue
        lo, hi = d.loc[d["Veces_tasa_base"].idxmin()], d.loc[d["Veces_tasa_base"].idxmax()]
        pu = puesto(variable)
        etiqueta = etiqueta_variable(variable) + (f"  (modelo: #{pu[0]})" if pu else "")
        filas.append({"Variable": variable, "Etiqueta": etiqueta, "Minimo": lo["Veces_tasa_base"],
                      "Maximo": hi["Veces_tasa_base"], "Amplitud": hi["Veces_tasa_base"] - lo["Veces_tasa_base"],
                      "Categoria_min": etiqueta_categoria(variable, lo["Categoria"]),
                      "Categoria_max": etiqueta_categoria(variable, hi["Categoria"])})
    return pd.DataFrame(filas).sort_values("Amplitud", ascending=False).reset_index(drop=True)


def fuerza(amplitud):
    return "débil" if amplitud < 0.25 else ("moderada" if amplitud < 0.75 else "fuerte")


def panel(k):
    tema, pregunta = PREGUNTAS[k]
    t = patrones[patrones["Pregunta"] == k]
    primera = t[t["Variable"] == t["Variable"].iloc[0]]
    base = 100 * primera["Criticos"].sum() / primera["Incidentes"].sum()       # tasa general de criticos, en %
    st.markdown(f"**Pregunta {k}.** {pregunta}")
    st.caption(f"Tasa general de críticos en el alcance: {base:.2f} %. «1.0×» = igual al promedio; «2.0×» = el doble.")

    resumen = resumen_por_variable(t)
    if resumen.empty:
        st.info("No hay variables con suficientes categorías para resumir.")
        return
    st.markdown("**¿Qué variables separan más el riesgo?** (de la categoría menos a la más riesgosa)")
    ui.grafico(graficos.fig_rangos(resumen), key=f"g_rangos_{k}")
    if n_vars:
        st.caption(f"La línea punteada es la tasa base (1×). (modelo: #n) = puesto de la variable en la importancia SHAP del modelo, de {n_vars}. "
                   "Una variable puede separar el riesgo en los datos y pesar poco en el modelo (otras variables, "
                   "sobre todo la ubicación, ya lo explican).")

    st.markdown("**Detalle de una variable**")
    opciones = list(resumen["Variable"])
    variable = st.selectbox("Variable", opciones, format_func=etiqueta_variable, key=f"sel_{k}")
    d = t[t["Variable"] == variable]
    ui.grafico(graficos.fig_detalle_variable(d, variable, base), key=f"g_detalle_{k}")
    r = resumen[resumen["Variable"] == variable].iloc[0]
    pu = puesto(variable)
    texto = (f"**Lectura.** Entre las categorías con suficientes casos, el riesgo va de **{r['Minimo']:.2f}×** "
             f"({r['Categoria_min']}) a **{r['Maximo']:.2f}×** ({r['Categoria_max']}) la tasa base: asociación "
             f"**{fuerza(r['Amplitud'])}**.")
    if pu:
        texto += f" En el modelo ocupa el puesto **{pu[0]} de {n_vars}** (aporte medio |SHAP| = {pu[1]:.3f})."
    st.markdown(texto)
    st.caption("La línea punteada es la tasa base (1×). Barras grises = categoría con pocos casos o sin dato "
               "registrado; las líneas verticales son el intervalo de confianza al 95 %. Asociación débil o moderada también es una respuesta válida. Es asociación, "
               "no causa. Regla práctica de la app para «débil / moderada / fuerte»: diferencia entre extremos "
               "menor que 0.25 / 0.75 veces la tasa base.")
    with st.expander("Ver la tabla"):
        tabla = d[["Categoria", "Incidentes", "Criticos", "Tasa_critico_%", "Veces_tasa_base", "IC95_inf_%",
                   "IC95_sup_%"]].copy()
        tabla["Categoria"] = [etiqueta_categoria(variable, c) for c in tabla["Categoria"]]
        ui.tabla(tabla, hide_index=True)


tabs = st.tabs([f"{k} · {PREGUNTAS[k][0]}" for k in PREGUNTAS])
for tab, k in zip(tabs, PREGUNTAS):
    with tab:
        panel(k)

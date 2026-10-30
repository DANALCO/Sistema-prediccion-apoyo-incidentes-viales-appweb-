"""Figuras de Plotly de la app (una funcion por grafico; las paginas solo las muestran)."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .etiquetas import (ACENTO, GRIS, GRIS_CLARO, ROJO, etiqueta_categoria, etiqueta_variable)

_BASE = dict(template="plotly_white", font=dict(size=13), margin=dict(l=10, r=10, t=40, b=10),
             legend=dict(orientation="h", y=1.12, x=0))


def _disenio(fig, alto, **extra):
    fig.update_layout(height=alto, **_BASE, **extra)
    return fig


# --------------------------------------------------------------------- explicacion del caso (SHAP)
def fig_aportes_caso(aportes, valores, top=10):
    """Barras horizontales: aporte de cada variable al logit del riesgo (positivo = empuja hacia critico)."""
    orden = sorted(aportes.items(), key=lambda kv: -abs(kv[1]))[:top]
    resto = sum(aportes.values()) - sum(v for _, v in orden)
    filas = [("(las demás variables)", resto)] + [
        (f"{etiqueta_variable(k)} = {valores.get(k, '—')}", v) for k, v in reversed(orden)]
    fig = go.Figure(go.Bar(
        y=[f[0] for f in filas], x=[f[1] for f in filas], orientation="h",
        marker_color=[GRIS if i == 0 else (ROJO if f[1] > 0 else ACENTO) for i, f in enumerate(filas)],
        text=[f"{f[1]:+.2f}" for f in filas], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>aporte %{x:+.3f}<extra></extra>"))
    fig.add_vline(x=0, line_color=GRIS)
    fig.update_xaxes(title="Aporte al riesgo (escala logit): rojo empuja hacia crítico, azul hacia normal",
                     zeroline=False)
    return _disenio(fig, 60 + 34 * len(filas), showlegend=False)


def fig_grupos(grupos):
    """Aporte NETO de cada grupo de variables (suma de los aportes de sus variables)."""
    from .etiquetas import GRUPO
    items = sorted(grupos.items(), key=lambda kv: kv[1])
    fig = go.Figure(go.Bar(
        y=[GRUPO.get(k, k) for k, _ in items], x=[v for _, v in items], orientation="h",
        marker_color=[ROJO if v > 0 else ACENTO for _, v in items],
        text=[f"{v:+.2f}" for _, v in items], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>aporte neto %{x:+.3f}<extra></extra>"))
    fig.add_vline(x=0, line_color=GRIS)
    fig.update_xaxes(title="Aporte neto del grupo (logit)", zeroline=False)
    return _disenio(fig, 70 + 40 * len(items), showlegend=False)


# --------------------------------------------------------------------- que pasaria si
def fig_que_pasaria_si(etiquetas, probs, i_actual, tau, titulo_x):
    colores = [ACENTO if i == i_actual else GRIS_CLARO for i in range(len(probs))]
    fig = go.Figure(go.Bar(
        x=etiquetas, y=probs, marker_color=colores,
        text=[f"{p:.1%}" for p in probs], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>riesgo %{y:.2%}<extra></extra>"))
    fig.add_hline(y=tau, line_dash="dash", line_color=ROJO,
                  annotation_text=f"umbral τ = {tau:.4f}", annotation_position="top left")
    fig.update_yaxes(title="Riesgo estimado", tickformat=".0%", rangemode="tozero")
    fig.update_xaxes(title=titulo_x, type="category")
    return _disenio(fig, 380, showlegend=False)


# --------------------------------------------------------------------- explorador de patrones (PI 1-3)
def fig_rangos(resumen):
    """Por variable: de la categoria menos a la mas riesgosa (veces la tasa base). `resumen` ya viene ordenado."""
    fig = go.Figure()
    for _, r in resumen.iterrows():
        fig.add_trace(go.Scatter(x=[r["Minimo"], r["Maximo"]], y=[r["Etiqueta"]] * 2, mode="lines",
                                 line=dict(color=GRIS_CLARO, width=6), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=resumen["Minimo"], y=resumen["Etiqueta"], mode="markers", name="categoría menos riesgosa",
        marker=dict(color=GRIS, size=10), customdata=resumen["Categoria_min"],
        hovertemplate="%{y}<br>menos riesgosa: %{customdata} (%{x:.2f}×)<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=resumen["Maximo"], y=resumen["Etiqueta"], mode="markers", name="categoría más riesgosa",
        marker=dict(color=ACENTO, size=10), customdata=resumen["Categoria_max"],
        hovertemplate="%{y}<br>más riesgosa: %{customdata} (%{x:.2f}×)<extra></extra>"))
    fig.add_vline(x=1, line_dash="dash", line_color=GRIS)
    fig.update_xaxes(title="Veces la tasa base de críticos (1× = igual al promedio)")
    fig.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=list(resumen["Etiqueta"]))
    return _disenio(fig, 110 + 30 * len(resumen))


def fig_detalle_variable(tabla, variable, base):
    """Veces la tasa base por categoria, con el intervalo de confianza al 95 %."""
    t = tabla.copy()
    x = [etiqueta_categoria(variable, c) for c in t["Categoria"]]
    y = t["Veces_tasa_base"]
    sin_dato = t["Categoria"].astype(str) == "sin dato"
    pocos = t["Pocos_casos"].astype(bool)
    colores = [GRIS_CLARO if (s or p) else ACENTO for s, p in zip(sin_dato, pocos)]
    fig = go.Figure(go.Bar(
        x=x, y=y, marker_color=colores,
        error_y=dict(type="data", symmetric=False, color=GRIS,
                     array=(t["IC95_sup_%"] / base - y).clip(lower=0), arrayminus=(y - t["IC95_inf_%"] / base).clip(lower=0)),
        customdata=np.stack([t["Incidentes"], t["Tasa_critico_%"]], axis=-1),
        hovertemplate="%{x}<br>%{y:.2f}× la tasa base<br>críticos: %{customdata[1]:.2f} % de %{customdata[0]:,.0f} incidentes"
                      "<extra></extra>"))
    fig.add_hline(y=1, line_dash="dash", line_color=GRIS)
    fig.update_xaxes(type="category", title=etiqueta_variable(variable))
    fig.update_yaxes(title="Veces la tasa base", rangemode="tozero")
    return _disenio(fig, 380, showlegend=False)


# --------------------------------------------------------------------- tiempo real vs completa (PI 4)
def fig_perdida(df, metrica, etiqueta_metodo):
    nombres = [etiqueta_metodo(m) for m in df["Metodo"]]
    fig = go.Figure()
    fig.add_bar(x=nombres, y=df[f"{metrica}_tiempo_real"], name="Tiempo real (al reportar)", marker_color=ACENTO,
                text=[f"{v:.3f}" for v in df[f"{metrica}_tiempo_real"]], textposition="outside", cliponaxis=False)
    fig.add_bar(x=nombres, y=df[f"{metrica}_completa"], name="Información completa", marker_color=GRIS_CLARO,
                text=[f"{v:.3f}" for v in df[f"{metrica}_completa"]], textposition="outside", cliponaxis=False)
    fig.update_layout(barmode="group")
    fig.update_yaxes(title=metrica.replace("_", "-"), rangemode="tozero")
    return _disenio(fig, 400)


# --------------------------------------------------------------------- control de umbral
def fig_umbral(curva, i_sel, i_ofi):
    """Precisión global (con la de «todo normal») y recall contra el % de alertas, con el umbral elegido marcado."""
    x = curva["Alertas_%"]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("Precisión global", "Recall (críticos detectados)"))
    hover = ("%{x:.2f} % de alertas<br>umbral %{customdata[0]:.4f}<br>precisión global %{customdata[1]:.4f}"
             "<br>recall %{customdata[2]:.3f}<extra></extra>")
    datos = np.stack([curva["Umbral"], curva["Exactitud"], curva["Recall"]], axis=-1)
    fig.add_trace(go.Scatter(x=x, y=curva["Exactitud"], mode="lines", line=dict(color=GRIS, width=2),
                             customdata=datos, hovertemplate=hover, showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=curva["Baseline"], mode="lines", line=dict(color=GRIS, dash="dash", width=1.5),
                             name="«todo normal»", hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=curva["Recall"], mode="lines", line=dict(color=GRIS, width=2),
                             customdata=datos, hovertemplate=hover, showlegend=False), row=2, col=1)
    for i, color, nombre in ((i_ofi, GRIS, "umbral oficial"), (i_sel, ACENTO, "umbral elegido")):
        for fila, col in ((1, "Exactitud"), (2, "Recall")):
            fig.add_trace(go.Scatter(
                x=[x.iloc[i]], y=[curva[col].iloc[i]], mode="markers", name=nombre, showlegend=(fila == 1),
                marker=dict(color=color, size=13 if i == i_sel else 9, line=dict(color="white", width=2)),
                hoverinfo="skip"), row=fila, col=1)
    fig.update_xaxes(title="Alertas (% de los incidentes marcados como críticos)", row=2, col=1)
    fig.update_yaxes(title="", row=1, col=1)
    return _disenio(fig, 520)

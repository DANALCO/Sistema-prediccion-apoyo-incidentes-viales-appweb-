"""EXPORTAR RESULTADOS: una consulta (CSV, JSON, ficha HTML imprimible) y el historial (CSV)."""

import html
import json
from datetime import datetime

import pandas as pd

from . import historial
from .etiquetas import GRUPO, ZONA_TEXTO, etiqueta_variable


def csv_bytes(df):
    """CSV con BOM para que Excel en Windows respete las tildes."""
    return df.to_csv(index=False).encode("utf-8-sig")


def fila_plana(entrada, resultado, umbral, recomendacion):
    fila = {k: (None if pd.isna(v) else v) if not isinstance(v, (list, dict)) else v
            for k, v in entrada.items()}
    fila.update({"Probabilidad": resultado["Probabilidad"], "Nivel": resultado["Nivel"],
                 "Es_critico": bool(resultado["Es_critico"]), "Umbral_usado": umbral,
                 "Campos_estimados": int(resultado["Campos_estimados"]),
                 "Recomendacion": recomendacion["titulo"], "Prioridad": recomendacion["prioridad"]})
    for k, v in resultado.items():
        if k.startswith(("Prob_", "Aporte_")):
            fila[k] = v
    return fila


def ficha_json(entrada, resultado, umbral, recomendacion, aportes, base, grupos, umbral_oficial):
    cuerpo = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "entrada": json.loads(historial.serializar(entrada)),
        "resultado": {k: (bool(v) if k == "Es_critico" else v) for k, v in resultado.items()},
        "umbral_usado": umbral, "umbral_oficial": umbral_oficial,
        "recomendacion": recomendacion,
        "explicacion": {"valor_base_logit": base, "aporte_por_variable_logit": aportes,
                        "aporte_neto_por_grupo_logit": grupos} if aportes is not None else None,
    }
    return json.dumps(cuerpo, ensure_ascii=False, indent=2, default=float).encode("utf-8")


def ficha_html(entrada, resultado, umbral, recomendacion, aportes, grupos, umbral_oficial, evidencia=None):
    e = html.escape
    filas_entrada = "".join(
        f"<tr><td>{e(etiqueta_variable(k))}</td><td>{e(str(v))}</td></tr>"
        for k, v in historial.deserializar(historial.serializar(entrada)).items() if v is not None)
    acciones = "".join(f"<li>{e(a)}</li>" for a in recomendacion["acciones"])
    notas = "".join(f"<p class='nota'>{e(n)}</p>" for n in (recomendacion["nota_factor"], recomendacion["nota_datos"]) if n)
    shap = ""
    if aportes:
        top = sorted(aportes.items(), key=lambda kv: -abs(kv[1]))[:10]
        shap = ("<h2>Qué empujó el riesgo (aporte en escala logit; positivo = hacia crítico)</h2><table>"
                + "".join(f"<tr><td>{e(etiqueta_variable(k))}</td><td>{v:+.3f}</td></tr>" for k, v in top)
                + "</table>")
        if grupos:
            shap += "<p>Por grupo: " + "; ".join(f"{e(GRUPO.get(g, g))} {v:+.3f}" for g, v in grupos.items()) + "</p>"
    ev = f"<p>{e(evidencia)}</p>" if evidencia else ""
    oficial = "" if abs(umbral - umbral_oficial) < 1e-12 else f" (el oficial es {umbral_oficial:.4f})"
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Ficha del incidente</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:760px;margin:2rem auto;color:#1c2128}}
h1{{font-size:1.4rem}}h2{{font-size:1.05rem;margin-top:1.6rem}}table{{border-collapse:collapse;width:100%}}
td{{border-bottom:1px solid #e1e4e8;padding:.3rem .5rem;font-size:.92rem}}
.zona{{padding:.8rem 1rem;border-radius:6px;background:#f3f4f6;font-size:1.1rem}}
.nota{{background:#fff8e1;padding:.5rem .8rem;border-radius:4px}}.peq{{color:#57606a;font-size:.8rem}}</style></head>
<body><h1>Ficha del incidente</h1><p class="peq">Generada el {datetime.now():%Y-%m-%d %H:%M}</p>
<div class="zona"><b>{e(ZONA_TEXTO[resultado['Nivel']])}</b> · riesgo estimado {resultado['Probabilidad']:.1%}
· umbral {umbral:.4f}{e(oficial)}</div>{ev}
<h2>Recomendación: {e(recomendacion['titulo'])} (prioridad {e(recomendacion['prioridad'])})</h2>
<ul>{acciones}</ul>{notas}<p class="peq">{e(recomendacion['aviso'])}</p>
<h2>Datos del reporte</h2><table>{filas_entrada}</table>{shap}
<p class="peq">Estimación de un modelo entrenado con datos históricos: asociación, no causa. Cifras orientativas;
la tasa de críticos cambia con el tiempo y entre estados.</p></body></html>""".encode("utf-8")

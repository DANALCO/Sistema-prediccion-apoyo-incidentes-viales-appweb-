"""
ESTILO VISUAL: una sola hoja de estilos y unos pocos componentes HTML reutilizables.

Streamlit se ve «de fabrica» muy funcional pero plano; aqui se le da identidad: encabezado de pagina, tarjetas,
numeros de paso en el formulario, tarjeta de resultado con una barra de riesgo, y metricas mas legibles.
Todo es CSS/HTML estatico (sin internet ni dependencias). Si una version de Streamlit cambia un selector,
la app sigue funcionando; solo se pierde el detalle visual.
"""

import html

import streamlit as st

from .etiquetas import ACENTO, COLOR_ZONA, ZONA_TEXTO

ICONO_ZONA = {"Normal": "✓", "Vigilancia (bajo el umbral)": "!", "Vigilancia (sobre el umbral)": "!!", "Critico": "⚠"}

CSS = """
<style>
:root{
  --acento:#1f6feb; --acento-osc:#0b3d91; --tinta:#1b2430; --tinta-suave:#5b6675; --linea:#e3e8ef;
  --fondo-tarjeta:#ffffff; --verde:#2e8b57; --ambar:#d98e04; --naranja:#e0782b; --rojo:#c0392b;
}
/* --- estructura general --- */
.block-container{max-width:1180px;padding-top:2.2rem;padding-bottom:4rem}
header[data-testid="stHeader"]{background:transparent}
h1,h2,h3{letter-spacing:-.01em;color:var(--tinta)}
h2{font-size:1.45rem!important;margin-top:1.4rem}
h3{font-size:1.15rem!important}
hr{margin:1.4rem 0!important;border-color:var(--linea)!important}
[data-testid="stCaptionContainer"]{color:var(--tinta-suave)}

/* --- barra lateral --- */
[data-testid="stSidebar"]{border-right:1px solid var(--linea)}
[data-testid="stSidebar"] [data-testid="stSidebarNav"]{padding-top:.4rem}
.marca{display:flex;align-items:center;gap:.65rem;padding:1.1rem 1rem .6rem 1rem}
.marca .logo{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,var(--acento),var(--acento-osc));
  display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.25rem;box-shadow:0 4px 10px rgba(31,111,235,.35)}
.marca .nombre{font-weight:700;line-height:1.15;color:var(--tinta);font-size:.98rem}
.marca .sub{font-size:.76rem;color:var(--tinta-suave)}

/* --- encabezado de pagina --- */
.hero{background:linear-gradient(120deg,#0b3d91 0%,#1f6feb 62%,#4a90f5 100%);color:#fff;border-radius:18px;
  padding:1.5rem 1.8rem;margin-bottom:1.3rem;position:relative;overflow:hidden;box-shadow:0 8px 24px rgba(11,61,145,.22)}
.hero:after{content:"";position:absolute;right:-60px;top:-60px;width:220px;height:220px;border-radius:50%;
  background:rgba(255,255,255,.08)}
.hero:before{content:"";position:absolute;right:70px;bottom:-90px;width:170px;height:170px;border-radius:50%;
  background:rgba(255,255,255,.06)}
.hero h1{color:#fff!important;font-size:1.85rem!important;margin:0 0 .25rem 0!important;padding:0!important}
.hero p{color:rgba(255,255,255,.92);margin:0;font-size:1.02rem;max-width:760px}
.hero .pasos{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:1rem}
.hero .paso{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);border-radius:999px;
  padding:.28rem .85rem;font-size:.86rem;backdrop-filter:blur(2px)}
.hero .paso b{background:#fff;color:var(--acento-osc);border-radius:50%;display:inline-block;width:1.35rem;height:1.35rem;
  line-height:1.35rem;text-align:center;margin-right:.45rem;font-size:.78rem}

/* --- tarjetas (st.container(border=True)) --- */
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px!important;border-color:var(--linea)!important;
  background:var(--fondo-tarjeta);box-shadow:0 1px 3px rgba(20,32,50,.05),0 6px 18px rgba(20,32,50,.04)}
.paso-titulo{display:flex;align-items:center;gap:.65rem;margin:.1rem 0 .55rem 0}
.paso-titulo .num{width:1.9rem;height:1.9rem;border-radius:50%;background:var(--acento);color:#fff;font-weight:700;
  display:flex;align-items:center;justify-content:center;font-size:.95rem;flex:none}
.paso-titulo .txt{font-weight:700;font-size:1.08rem;color:var(--tinta)}
.paso-titulo .det{color:var(--tinta-suave);font-size:.88rem;margin-left:.2rem}
.etiqueta-obligatorio{background:#fdecea;color:#a12a1f;border-radius:999px;padding:.05rem .55rem;font-size:.72rem;
  font-weight:600;margin-left:.4rem}
.etiqueta-opcional{background:#eef2f7;color:#5b6675;border-radius:999px;padding:.05rem .55rem;font-size:.72rem;
  font-weight:600;margin-left:.4rem}

/* --- metricas --- */
[data-testid="stMetric"]{background:var(--fondo-tarjeta);border:1px solid var(--linea);border-radius:14px;
  padding:.85rem 1rem;box-shadow:0 1px 2px rgba(20,32,50,.04)}
[data-testid="stMetricLabel"]{color:var(--tinta-suave)}
[data-testid="stMetricValue"]{font-weight:700;color:var(--tinta)}

/* --- pestañas --- */
[data-baseweb="tab-list"]{gap:.4rem;border-bottom:1px solid var(--linea)}
[data-baseweb="tab"]{font-weight:600;padding:.55rem 1rem;border-radius:10px 10px 0 0}
[data-baseweb="tab-highlight"]{height:3px!important;border-radius:3px}

/* --- botones y campos --- */
.stButton>button,.stDownloadButton>button{border-radius:11px;font-weight:600;padding:.5rem 1.15rem;
  border:1px solid var(--linea);transition:transform .08s ease,box-shadow .15s ease}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(20,32,50,.12)}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#1f6feb,#0b57d0);border:none;color:#fff;
  box-shadow:0 4px 12px rgba(31,111,235,.35)}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="base-input"]{border-radius:10px!important}
[data-testid="stExpander"]{border-radius:14px!important;border-color:var(--linea)!important;background:var(--fondo-tarjeta)}
[data-testid="stExpander"] summary{font-weight:600}
[data-testid="stAlert"]{border-radius:12px}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden}

/* --- tarjeta de resultado --- */
.zona{--c:#2e8b57;border-radius:18px;background:var(--fondo-tarjeta);border:1px solid var(--linea);
  border-top:7px solid var(--c);padding:1.2rem 1.5rem 1.1rem 1.5rem;box-shadow:0 10px 28px rgba(20,32,50,.09)}
.zona .fila{display:flex;align-items:center;gap:1rem;flex-wrap:wrap}
.zona .icono{width:3.4rem;height:3.4rem;border-radius:16px;background:var(--c);color:#fff;font-size:1.6rem;font-weight:800;
  display:flex;align-items:center;justify-content:center;flex:none}
.zona .rotulo{font-size:.76rem;letter-spacing:.09em;text-transform:uppercase;color:var(--tinta-suave);font-weight:700}
.zona .nombre{font-size:1.9rem;font-weight:800;color:var(--c);line-height:1.1}
.zona .riesgo{margin-left:auto;text-align:right}
.zona .riesgo .num{font-size:2.5rem;font-weight:800;color:var(--tinta);line-height:1}
.zona .riesgo .txt{font-size:.82rem;color:var(--tinta-suave)}
.zona .barra{position:relative;display:flex;height:16px;border-radius:999px;overflow:hidden;margin:1.25rem 0 .2rem 0;
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.05)}
.zona .barra span{display:block;height:100%}
.zona .marca-p{position:absolute;top:-6px;width:4px;height:28px;background:var(--tinta);border-radius:3px;
  transform:translateX(-2px);box-shadow:0 0 0 2px #fff}
.zona .escala{position:relative;height:2.7rem;font-size:.74rem;color:var(--tinta-suave)}
.zona .escala span.b{top:1.15rem;font-weight:700;color:var(--tinta)}
.zona .escala span{position:absolute;transform:translateX(-50%);white-space:nowrap}
.zona .pie{margin-top:.4rem;font-size:.84rem;color:var(--tinta-suave)}
.zona .leyenda{display:flex;flex-wrap:wrap;gap:.3rem 1.1rem;font-size:.82rem;color:var(--tinta-suave);margin-top:.15rem}
.zona .li i{display:inline-block;width:.7rem;height:.7rem;border-radius:3px;margin-right:.35rem;vertical-align:-1px}
.zona .li i.caso{width:4px;height:.85rem;background:var(--tinta);border-radius:2px;margin-right:.45rem;vertical-align:-2px}
.chip{display:inline-block;border-radius:999px;padding:.12rem .65rem;font-size:.78rem;font-weight:600;
  background:#eef2f7;color:#3d4756;margin-right:.35rem}
.chip.aviso{background:#fff4de;color:#8a5a00}
.chip.ok{background:#e4f5ec;color:#1d6b43}
.ubic{border-radius:12px;background:#f2f7ff;border:1px solid #cfe0fb;padding:.65rem .9rem;margin-top:.5rem;color:var(--tinta)}
.ubic.aprox{background:#fff8e8;border-color:#f3dfae}
.ubic .t{font-weight:700}
.ubic .c{font-size:.85rem;color:var(--tinta-suave)}
.vacio{border:2px dashed var(--linea);border-radius:16px;padding:2rem;text-align:center;color:var(--tinta-suave)}
.vacio .g{font-size:2rem}
</style>
"""


def aplicar():
    """Inyecta la hoja de estilos (llamar una vez por ejecucion, en app.py)."""
    st.markdown(CSS, unsafe_allow_html=True)


def barra_lateral_marca():
    st.markdown(
        "<div class='marca'><div class='logo'>🚦</div><div><div class='nombre'>Incidentes viales</div>"
        "<div class='sub'>Apoyo a la decisión</div></div></div>", unsafe_allow_html=True)


def encabezado(titulo, subtitulo, pasos=None):
    """Banner de pagina. `pasos`: lista de textos cortos (se numeran) para guiar a quien llega por primera vez."""
    chips = ""
    if pasos:
        chips = "<div class='pasos'>" + "".join(
            f"<span class='paso'><b>{i}</b>{html.escape(p)}</span>" for i, p in enumerate(pasos, 1)) + "</div>"
    st.markdown(f"<div class='hero'><h1>{html.escape(titulo)}</h1><p>{html.escape(subtitulo)}</p>{chips}</div>",
                unsafe_allow_html=True)


def titulo_de_paso(numero, titulo, detalle="", obligatorio=None):
    """Encabezado numerado de una tarjeta del formulario. obligatorio: True, False o None (sin etiqueta)."""
    etiqueta = ""
    if obligatorio is True:
        etiqueta = "<span class='etiqueta-obligatorio'>obligatorio</span>"
    elif obligatorio is False:
        etiqueta = "<span class='etiqueta-opcional'>opcional</span>"
    det = f"<span class='det'>{html.escape(detalle)}</span>" if detalle else ""
    st.markdown(f"<div class='paso-titulo'><span class='num'>{numero}</span><span class='txt'>{html.escape(titulo)}</span>"
                f"{etiqueta}{det}</div>", unsafe_allow_html=True)


def tarjeta_ubicacion(texto, lat=None, lng=None, aproximada=False):
    c = f"<div class='c'>{lat:.4f}, {lng:.4f}</div>" if lat is not None else ""
    clase = "ubic aprox" if aproximada else "ubic"
    icono = "📍" if not aproximada else "🧭"
    st.markdown(f"<div class='{clase}'><div class='t'>{icono} {html.escape(texto)}</div>{c}</div>", unsafe_allow_html=True)


def vacio(icono, titulo, texto):
    st.markdown(f"<div class='vacio'><div class='g'>{icono}</div><b>{html.escape(titulo)}</b><br>{html.escape(texto)}</div>",
                unsafe_allow_html=True)


def bordes_de_zona(decision, tau):
    """(inferior, tau, superior): los tres cortes entre las cuatro zonas para el umbral usado."""
    oficial = float(decision["umbral"])
    f = 1.0 if abs(tau - oficial) < 1e-12 else tau / oficial
    return f * float(decision["umbral_vigilancia_inferior"]), tau, f * float(decision["umbral_vigilancia_superior"])


def tarjeta_zona(nivel, p, bordes, umbral_modificado=False, pie=""):
    """Tarjeta grande con la zona, el riesgo y una barra con las cuatro zonas y la posicion del caso."""
    inf, tau, sup = bordes
    tope = min(1.0, max(0.30, 3.0 * sup))
    pos = lambda x: 100.0 * min(max(x, 0.0), tope) / tope
    tramos = [(0, inf, COLOR_ZONA["Normal"]), (inf, tau, COLOR_ZONA["Vigilancia (bajo el umbral)"]),
              (tau, sup, COLOR_ZONA["Vigilancia (sobre el umbral)"]), (sup, tope, COLOR_ZONA["Critico"])]
    barra = "".join(f"<span style='width:{pos(b) - pos(a):.3f}%;background:{c}'></span>" for a, b, c in tramos)
    cortes = (f"<span style='left:{pos(inf):.2f}%'>{inf:.1%}</span>"
              f"<span class='b' style='left:{pos(tau):.2f}%'>umbral {tau:.1%}</span>"
              f"<span style='left:{pos(sup):.2f}%'>{sup:.1%}</span>")
    extremo = f"<span style='left:100%'>{tope:.0%}+</span>" if tope < 1 else ""
    cero = "<span style='left:0%'>0 %</span>"
    color = COLOR_ZONA[nivel]
    etiqueta_tau = " · umbral modificado" if umbral_modificado else ""
    leyenda = "".join(f"<span class='li'><i style='background:{COLOR_ZONA[z]}'></i>{html.escape(ZONA_TEXTO[z])}</span>"
                      for z in ("Normal", "Vigilancia (bajo el umbral)", "Vigilancia (sobre el umbral)", "Critico"))
    st.markdown(
        f"<div class='zona' style='--c:{color}'><div class='fila'><div class='icono'>{ICONO_ZONA[nivel]}</div>"
        f"<div><div class='rotulo'>Zona del incidente</div><div class='nombre'>{html.escape(ZONA_TEXTO[nivel])}</div></div>"
        f"<div class='riesgo'><div class='num'>{p:.1%}</div><div class='txt'>riesgo estimado de impacto crítico</div></div></div>"
        f"<div class='barra'>{barra}<div class='marca-p' style='left:{pos(p):.2f}%'></div></div>"
        f"<div class='escala'>{cero}{cortes}{extremo}</div>"
        f"<div class='leyenda'>{leyenda}<span class='li'><i class='caso'></i>este caso{etiqueta_tau}</span></div>"
        f"{('<div class=pie>' + html.escape(pie) + '</div>') if pie else ''}</div>", unsafe_allow_html=True)

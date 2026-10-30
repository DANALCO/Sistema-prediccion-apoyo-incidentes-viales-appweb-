"""
FORMULARIO DE REPORTE DEL INCIDENTE (funcionalidad 1).

Solo pide lo que conoce el operador al recibir el reporte. Obligatorio: fecha, hora y ESTADO. El lugar exacto
es opcional y se elige sin escribir coordenadas (ciudad, busqueda, mapa o coordenadas pegadas); si no se indica,
se usa el centro del estado y la app avisa que el resultado es mas aproximado. Los campos opcionales pueden
quedar vacios: el modelo los estima con valores tipicos de entrenamiento y avisa cuantos fueron.

Las claves de los widgets empiezan por `f_`; `leer_estado` las convierte en el dict que espera el predictor y
`escribir_estado` hace el camino inverso (ejemplo, reabrir una consulta del historial).
Claves que NO son widgets (f_lat, f_lng, f_lugar) guardan el lugar elegido; se pueden cambiar en cualquier momento.
"""

import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from . import estilo, lugares, ui
from .ayudas import (AYUDA, AYUDA_BANDERA, AYUDA_INFRA, DIA_NOCHE_TEXTO, TIPO_VIA_TEXTO, VIENTO_TEXTO)
from .etiquetas import INFRAESTRUCTURA, VARIABLE

NO_SE = "No sé"
# clave del widget -> (columna, minimo, maximo, paso, formato)
NUMERICOS = {
    "f_temp": ("Temperature(F)", -60.0, 135.0, 1.0, "%.1f"),
    "f_hum": ("Humidity(%)", 0.0, 100.0, 1.0, "%.0f"),
    "f_pres": ("Pressure(in)", 20.0, 35.0, 0.01, "%.2f"),
    "f_vis": ("Visibility(mi)", 0.0, 150.0, 0.5, "%.1f"),
    "f_viento": ("Wind_Speed(mph)", 0.0, 250.0, 1.0, "%.1f"),
    "f_precip": ("Precipitation(in)", 0.0, 50.0, 0.01, "%.2f"),
}
CATEGORICOS = {"f_clima": "Weather_Condition", "f_dirviento": "Wind_Direction",
               "f_dianoche": "Sunrise_Sunset", "f_tipovia": "Tipo_via"}
BANDERAS = {f"f_i_{c}": c for c in INFRAESTRUCTURA}
LUGAR = ["f_lat", "f_lng", "f_lugar"]                 # no son widgets
METODOS = ["📍 Ciudad", "🔎 Buscar", "🗺️ Mapa", "🧭 Coordenadas"]
CIUDAD, BUSCAR, MAPA, COORD = METODOS
CLAVES = (["f_fecha", "f_hora", "f_estado", "f_calle", "f_metodo_ubic", "f_busqueda", "f_coords_texto"]
          + LUGAR + list(NUMERICOS) + list(CATEGORICOS) + list(BANDERAS))

# Un incidente real de pruebas (el mismo del documento del modelo matematico, seccion 13).
EJEMPLO = {
    "Start_Time": pd.Timestamp("2022-05-18 11:08"), "State": "PA", "Start_Lat": 40.4103, "Start_Lng": -79.6192,
    "Temperature(F)": 61.0, "Humidity(%)": 48.0, "Pressure(in)": 28.82, "Visibility(mi)": 10.0,
    "Wind_Speed(mph)": 0.0, "Precipitation(in)": np.nan, "Wind_Direction": "Calm",
    "Weather_Condition": "Nublado", "Sunrise_Sunset": "Day", "Tipo_via": "Carretera",
    **{c: (c == "Stop") for c in INFRAESTRUCTURA},
}


# ----------------------------------------------------------------------------
# Leer / escribir el estado del formulario
# ----------------------------------------------------------------------------
def leer_estado():
    """Convierte lo que hay en el formulario en el dict de entrada. ValueError si falta algo obligatorio.

    Si no se eligio un lugar, usa el centro del estado (ubicacion aproximada)."""
    s = st.session_state
    if s.get("f_estado") is None:
        raise ValueError("Falta elegir el estado donde ocurrió el incidente (campo obligatorio).")
    lat, lng = s.get("f_lat"), s.get("f_lng")
    if lat is None or lng is None:
        centro = lugares.centro_del_estado(s["f_estado"])
        if centro is None:
            raise ValueError("No tengo un punto de referencia para ese estado: elija una ciudad, busque el lugar "
                             "o pegue las coordenadas.")
        lat, lng = centro
    entrada = {"Start_Time": pd.Timestamp(dt.datetime.combine(s["f_fecha"], s["f_hora"])),
               "State": s["f_estado"], "Start_Lat": float(lat), "Start_Lng": float(lng)}
    for clave, (col, *_resto) in NUMERICOS.items():
        v = s.get(clave)
        entrada[col] = np.nan if v is None else float(v)
    for clave, col in CATEGORICOS.items():
        v = s.get(clave)
        entrada[col] = np.nan if not v else v
    for clave, col in BANDERAS.items():
        v = s.get(clave, NO_SE)
        entrada[col] = np.nan if v == NO_SE else (v == "Sí")
    calle = (s.get("f_calle") or "").strip()
    if pd.isna(entrada["Tipo_via"]) and calle:       # la calle solo completa un Tipo_via que falta
        entrada["Street"] = calle
    return entrada


def ubicacion_aproximada(entrada):
    """True si las coordenadas de la entrada son el centro del estado (no se indico un lugar)."""
    return lugares.es_centro_del_estado(entrada["State"], entrada["Start_Lat"], entrada["Start_Lng"])


def _vacio(v):
    return v is None or (isinstance(v, float) and np.isnan(v))


def _olvidar_lugar_en_widgets():
    for k in ("f_ciudad", "f_busqueda", "f_resultado", "f_coords_texto", "_busqueda", "_ultimo_clic", "_vista_mapa"):
        st.session_state.pop(k, None)


def escribir_estado(entrada):
    """Pone una entrada (EJEMPLO o una del historial) en los widgets. Llamar ANTES de dibujarlos."""
    s = st.session_state
    t = pd.Timestamp(entrada["Start_Time"])
    s["f_fecha"], s["f_hora"] = t.date(), t.time().replace(second=0, microsecond=0)
    s["f_estado"] = entrada["State"]
    s["f_lat"], s["f_lng"] = float(entrada["Start_Lat"]), float(entrada["Start_Lng"])
    s["f_lugar"] = (f"Centro de {lugares.nombre_estado(entrada['State'])} (aproximado)"
                    if ubicacion_aproximada(entrada) else "Lugar del caso cargado")
    _olvidar_lugar_en_widgets()
    s["f_calle"] = entrada.get("Street") or ""
    for clave, (col, *_resto) in NUMERICOS.items():
        v = entrada.get(col)
        s[clave] = None if _vacio(v) else float(v)
    for clave, col in CATEGORICOS.items():
        v = entrada.get(col)
        s[clave] = None if _vacio(v) else v
    for clave, col in BANDERAS.items():
        v = entrada.get(col)
        s[clave] = NO_SE if _vacio(v) else ("Sí" if bool(v) else "No")


def vaciar():
    ahora = dt.datetime.now()
    s = st.session_state
    s["f_fecha"], s["f_hora"] = ahora.date(), ahora.time().replace(second=0, microsecond=0)
    for k in ["f_estado", *NUMERICOS, *CATEGORICOS]:
        s[k] = None
    s["f_lat"], s["f_lng"], s["f_lugar"] = None, None, ""
    _olvidar_lugar_en_widgets()
    s["f_calle"] = ""
    for k in BANDERAS:
        s[k] = NO_SE


def restaurar_y_aplicar_pendiente():
    """Al abrir la pagina: recupera lo escrito antes de navegar y aplica un caso pendiente (historial)."""
    s = st.session_state
    for k, v in s.get("_form_guardado", {}).items():       # Streamlit borra widgets de paginas no mostradas
        if k not in s:
            s[k] = v
    pendiente = s.pop("_cargar", None)
    if pendiente is not None:
        escribir_estado(pendiente)


def guardar_para_navegar():
    st.session_state["_form_guardado"] = {k: st.session_state[k] for k in CLAVES if k in st.session_state}


# ----------------------------------------------------------------------------
# Elegir el lugar (callbacks: corren ANTES de dibujar, asi pueden cambiar widgets)
# ----------------------------------------------------------------------------
def _poner_lugar(lat, lng, texto):
    s = st.session_state
    s["f_lat"] = None if lat is None else float(lat)
    s["f_lng"] = None if lng is None else float(lng)
    s["f_lugar"] = texto


def _quitar_lugar():
    _poner_lugar(None, None, "")
    _olvidar_lugar_en_widgets()


def _al_cambiar_estado():
    """Si el lugar elegido ya no cae en el estado nuevo, se quita (y se avisa)."""
    s = st.session_state
    if (s.get("f_lat") is not None and s.get("f_estado")
            and lugares.dentro_del_estado(s["f_estado"], s["f_lat"], s["f_lng"]) is False):
        _quitar_lugar()
        s["_aviso_ubic"] = "Cambió el estado, así que quité el lugar anterior (ya no correspondía). Elija el lugar otra vez."
    s.pop("f_ciudad", None)


def _elegir_ciudad():
    s = st.session_state
    estado, v = s.get("f_estado"), s.get("f_ciudad")
    if not estado or not v:
        return
    if v == "__centro__":
        lat, lng = lugares.centro_del_estado(estado)
        _poner_lugar(lat, lng, f"Centro de {lugares.nombre_estado(estado)} (aproximado)")
        return
    for nombre, lat, lng in lugares.ciudades(estado):
        if nombre == v:
            _poner_lugar(lat, lng, f"{nombre}, {estado}")
            return


@st.cache_data(show_spinner=False, ttl=3600)
def _buscar_en_red(texto, estado):
    return lugares.buscar(texto, estado)


def _buscar():
    s = st.session_state
    texto = (s.get("f_busqueda") or "").strip()
    s.pop("f_resultado", None)
    if not texto:
        s["_busqueda"] = None
        return
    try:
        s["_busqueda"] = {"texto": texto, "resultados": _buscar_en_red(texto, s.get("f_estado")), "error": None}
    except lugares.BusquedaNoDisponible:
        s["_busqueda"] = {"texto": texto, "resultados": [], "error": (
            "No pude conectarme al servicio de búsqueda (¿hay internet?). Use la lista de ciudades, el mapa "
            "o pegue las coordenadas.")}


def _usar_resultado(estados_validos):
    s = st.session_state
    b = s.get("_busqueda") or {}
    i = s.get("f_resultado", 0)
    if not b.get("resultados") or i is None or i >= len(b["resultados"]):
        return
    r = b["resultados"][i]
    if r["estado"] and r["estado"] not in estados_validos:
        s["_aviso_ubic"] = (f"Ese lugar está en {lugares.nombre_estado(r['estado'])}, un estado que el modelo no cubre "
                            "(solo hay datos de los estados de la lista).")
        return
    if r["estado"]:
        s["f_estado"] = r["estado"]
    _poner_lugar(r["lat"], r["lng"], r["texto"].split(",")[0] + (f", {r['estado']}" if r["estado"] else ""))


def _usar_coordenadas():
    s = st.session_state
    lat, lng, nota = lugares.leer_coordenadas(s.get("f_coords_texto"))
    if lat is None:
        s["_aviso_ubic"] = nota
        return
    _poner_lugar(lat, lng, "Coordenadas indicadas")
    if nota:
        s["_aviso_ubic"] = nota


def _cambiar_estado_a(codigo):
    st.session_state["f_estado"] = codigo
    st.session_state.pop("f_ciudad", None)


# ----------------------------------------------------------------------------
# Dibujo
# ----------------------------------------------------------------------------
def _metodo_ciudad():
    s = st.session_state
    estado = s.get("f_estado")
    if not estado:
        st.info("Primero elija el estado (arriba) y aquí aparecerán sus ciudades principales.")
        return
    ciudades = [n for n, *_ in lugares.ciudades(estado)]
    opciones = ["__centro__"] + ciudades
    st.selectbox("Ciudad más cercana al incidente", opciones, index=None, key="f_ciudad", on_change=_elegir_ciudad,
                 placeholder="Elija una ciudad", help=AYUDA["f_ciudad"],
                 format_func=lambda v: (f"Centro de {lugares.nombre_estado(estado)} (aproximado)"
                                        if v == "__centro__" else v))


def _metodo_buscar(estados):
    s = st.session_state
    a, b = st.columns([4, 1], vertical_alignment="bottom")
    a.text_input("Dirección, calle o lugar", key="f_busqueda", on_change=_buscar, help=AYUDA["f_busqueda"],
                 placeholder="Ej.: I-95 y Broad St, Philadelphia")
    b.button("Buscar", on_click=_buscar, key="btn_buscar")
    busqueda = s.get("_busqueda")
    if not busqueda:
        st.caption("Escriba el lugar y pulse Enter o «Buscar». Usa OpenStreetMap (gratis) y necesita internet.")
        return
    if busqueda["error"]:
        st.error(busqueda["error"])
    elif not busqueda["resultados"]:
        st.info("No encontré ese lugar. Pruebe con otra dirección o agregue la ciudad.")
    else:
        res = busqueda["resultados"]
        st.selectbox("Resultados (elija el correcto)", list(range(len(res))), key="f_resultado", index=0,
                     format_func=lambda i: res[i]["texto"])
        st.button("Usar este lugar", on_click=_usar_resultado, args=(estados,), type="primary")


def _metodo_mapa():
    s = st.session_state
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.info("El mapa necesita dos paquetes pequeños. Instálelos con `python -m pip install folium "
                "streamlit-folium` y reinicie la app (`iniciar_app.bat` lo hace solo). Mientras tanto use "
                "«Ciudad», «Buscar» o «Coordenadas».")
        return
    estado, lat, lng = s.get("f_estado"), s.get("f_lat"), s.get("f_lng")
    vista = s.get("_vista_mapa")
    if vista:
        centro, zoom = vista["centro"], vista["zoom"]
    elif lat is not None:
        centro, zoom = (lat, lng), 12
    elif estado and lugares.centro_del_estado(estado):
        centro, zoom = lugares.centro_del_estado(estado), 6
    else:
        centro, zoom = lugares.CENTRO_EEUU, 4
    mapa = folium.Map(location=list(centro), zoom_start=zoom, control_scale=True)
    if lat is not None:
        folium.Marker([lat, lng], tooltip=s.get("f_lugar") or "Lugar elegido",
                      icon=folium.Icon(color="red", icon="info-sign")).add_to(mapa)
    st.caption("**Haga clic en el lugar del accidente.** Acerque con los botones + / − o con la rueda del ratón. "
               "(El mapa necesita internet para dibujarse.)")
    salida = st_folium(mapa, height=380, use_container_width=True, key="f_mapa",
                       returned_objects=["last_clicked", "zoom", "center"])
    if not salida:
        return
    if salida.get("zoom") and salida.get("center"):
        s["_vista_mapa"] = {"centro": (salida["center"]["lat"], salida["center"]["lng"]), "zoom": int(salida["zoom"])}
    clic = salida.get("last_clicked")
    if clic and (clic["lat"], clic["lng"]) != s.get("_ultimo_clic"):
        s["_ultimo_clic"] = (clic["lat"], clic["lng"])
        _poner_lugar(round(clic["lat"], 5), round(clic["lng"], 5), "Punto marcado en el mapa")


def _metodo_coordenadas():
    st.text_input("Coordenadas o enlace de Google Maps", key="f_coords_texto", on_change=_usar_coordenadas,
                  placeholder="Ej.: 40.4103, -79.6192", help=AYUDA["f_coords_texto"])
    st.caption("Pulse Enter para aplicar. En Google Maps: clic derecho sobre el lugar → toque los números de arriba "
               "(se copian) → péguelos aquí. También sirve pegar el enlace del lugar.")


def _resumen_ubicacion(estados):
    """Tarjeta con el lugar que se usara y avisos si no cuadra con el estado."""
    s = st.session_state
    aviso = s.pop("_aviso_ubic", None)
    if aviso:
        st.warning(aviso)
    estado, lat, lng = s.get("f_estado"), s.get("f_lat"), s.get("f_lng")
    if lat is not None:
        aprox = lugares.es_centro_del_estado(estado, lat, lng)
        estilo.tarjeta_ubicacion(s.get("f_lugar") or "Lugar elegido", lat, lng, aproximada=aprox)
        if estado and lugares.dentro_del_estado(estado, lat, lng) is False:
            sug = lugares.estado_probable(lat, lng, entre=estados)
            texto = f"Ese punto queda fuera de {lugares.nombre_estado(estado)}, el estado que eligió."
            if sug:
                texto += f" Parece estar en {lugares.nombre_estado(sug)}."
            st.warning(texto + " Una ubicación que no cuadra con el estado empeora la estimación.")
            c1, c2, _ = st.columns([2, 2, 3])
            if sug:
                c1.button(f"Cambiar el estado a {sug}", on_click=_cambiar_estado_a, args=(sug,), key="btn_cambiar_estado")
            c2.button("Quitar el lugar", on_click=_quitar_lugar, key="btn_quitar_lugar_aviso")
        else:
            st.button("Quitar el lugar", on_click=_quitar_lugar, key="btn_quitar_lugar")
    elif estado:
        centro = lugares.centro_del_estado(estado)
        if centro:
            estilo.tarjeta_ubicacion(f"Sin lugar exacto: se usará el centro de {lugares.nombre_estado(estado)}",
                                     centro[0], centro[1], aproximada=True)
            st.caption("Es una ubicación aproximada, así que la estimación será menos precisa. "
                       "Para mejorarla, elija una ciudad, busque la dirección o márquela en el mapa.")
        else:
            st.warning("No tengo un punto de referencia para ese estado: elija una ciudad, busque el lugar o "
                       "pegue las coordenadas.")


def dibujar(opciones):
    """Dibuja los campos. `opciones` = predictor.opciones_formulario()."""
    s = st.session_state
    if "f_fecha" not in s:
        vaciar()
    s.setdefault("f_metodo_ubic", CIUDAD)
    estados = sorted((o for o in opciones["State"] if o != "Desconocido"), key=lugares.nombre_estado)
    sin_desc = lambda lista: [o for o in lista if o != "Desconocido"]

    with st.container(border=True):
        estilo.titulo_de_paso(1, "Cuándo y dónde", "lo mínimo para analizar el caso", obligatorio=True)
        a, b, c = st.columns(3)
        a.date_input("Fecha del reporte", key="f_fecha", help=AYUDA["f_fecha"])
        b.time_input("Hora del reporte", key="f_hora", step=60, help=AYUDA["f_hora"])
        c.selectbox("Estado", estados, index=None, placeholder="Elija el estado", key="f_estado",
                    format_func=lugares.etiqueta_estado, on_change=_al_cambiar_estado, help=AYUDA["f_estado"])
        st.markdown("**Lugar del incidente** <span class='etiqueta-opcional'>opcional · mejora la precisión</span>",
                    unsafe_allow_html=True)
        ui.selector("¿Cómo prefiere indicar el lugar?", METODOS, key="f_metodo_ubic", help=AYUDA["f_metodo_ubic"])
        metodo = s.get("f_metodo_ubic") or CIUDAD
        if metodo == CIUDAD:
            _metodo_ciudad()
        elif metodo == BUSCAR:
            _metodo_buscar(estados)
        elif metodo == MAPA:
            _metodo_mapa()
        else:
            _metodo_coordenadas()
        _resumen_ubicacion(estados)

    with st.expander("**2 · Clima y visibilidad** — opcional, mejora la precisión"):
        st.caption("Si no conoce un dato, déjelo vacío: el sistema usa un valor típico y lo avisará en el resultado. "
                   "Pase el cursor por el «?» de cada campo para ver cómo llenarlo.")
        cols = st.columns(3)
        for i, (clave, (col, mn, mx, paso, fmt)) in enumerate(NUMERICOS.items()):
            cols[i % 3].number_input(VARIABLE[col], value=None, min_value=mn, max_value=mx, step=paso,
                                     format=fmt, key=clave, placeholder=NO_SE, help=AYUDA[clave])
        c1, c2, c3 = st.columns(3)
        c1.selectbox(VARIABLE["Weather_Condition"], sin_desc(opciones["Weather_Condition"]), index=None,
                     placeholder=NO_SE, key="f_clima", help=AYUDA["f_clima"])
        c2.selectbox(VARIABLE["Wind_Direction"], sin_desc(opciones["Wind_Direction"]), index=None,
                     placeholder=NO_SE, key="f_dirviento", help=AYUDA["f_dirviento"],
                     format_func=lambda x: VIENTO_TEXTO.get(x, x))
        c3.selectbox(VARIABLE["Sunrise_Sunset"], sin_desc(opciones["Sunrise_Sunset"]), index=None,
                     placeholder=NO_SE, key="f_dianoche", help=AYUDA["f_dianoche"],
                     format_func=lambda x: DIA_NOCHE_TEXTO.get(x, x))

    with st.expander("**3 · Vía e infraestructura** — opcional, mejora la precisión"):
        v1, v2 = st.columns(2)
        v1.selectbox(VARIABLE["Tipo_via"], sin_desc(opciones["Tipo_via"]), index=None, placeholder=NO_SE,
                     key="f_tipovia", help=AYUDA["f_tipovia"], format_func=lambda x: TIPO_VIA_TEXTO.get(x, x))
        v2.text_input("Nombre de la calle", key="f_calle", placeholder="Ej.: I-95 N", help=AYUDA["f_calle"])
        st.markdown("**¿Hay esto en el lugar del incidente?**")
        st.caption(AYUDA_BANDERA)
        cols = st.columns(4)
        for i, (clave, col) in enumerate(BANDERAS.items()):
            cols[i % 4].radio(VARIABLE[col], [NO_SE, "Sí", "No"], horizontal=True, key=clave, help=AYUDA_INFRA[col])

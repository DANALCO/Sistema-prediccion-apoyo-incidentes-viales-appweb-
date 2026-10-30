r"""
Pruebas de la app sin abrir el navegador (streamlit.testing.v1.AppTest).

Necesitan el modelo dentro de la carpeta de la app (lo copia `python sincronizar_modelo.py RUTA`):
    python -m pytest tests -q
(Para probar con otra carpeta que contenga models/ y src/: set INCIDENTES_REPO=C:\ruta\a\esa\carpeta)
Cada prueba usa una carpeta temporal para el historial, asi que no toca el historial real.
"""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
TIEMPO = 240


@pytest.fixture(autouse=True)
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("INCIDENTES_DATOS", str(tmp_path))
    import sys
    sys.path.insert(0, str(RAIZ))
    from incidentes_app import config
    if config.problemas_de_instalacion():
        pytest.skip("Falta el modelo en la app: ejecute `python sincronizar_modelo.py RUTA` (ver README).")


def pagina(nombre):
    at = AppTest.from_file(str(RAIZ / "paginas" / nombre), default_timeout=TIEMPO)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def boton(at, etiqueta):
    return next(b for b in at.button if b.label.startswith(etiqueta))


def analizar_ejemplo(at):
    boton(at, "Cargar ejemplo").click().run()
    assert not at.exception, [e.value for e in at.exception]
    boton(at, "Analizar incidente").click().run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def test_analizar_sin_datos_pide_obligatorios():
    at = pagina("analizar.py")
    boton(at, "Vaciar").click().run()
    boton(at, "Analizar incidente").click().run()
    assert not at.exception
    assert any("estado" in e.value.lower() and "obligatorio" in e.value for e in at.error)


def test_analizar_ejemplo_muestra_zona_recomendacion_y_pestanas():
    at = analizar_ejemplo(pagina("analizar.py"))
    assert "ultimo" in at.session_state
    u = at.session_state["ultimo"]
    assert u["resultado"]["Nivel"] in ("Normal", "Vigilancia (bajo el umbral)", "Vigilancia (sobre el umbral)", "Critico")
    assert 0 < u["resultado"]["Probabilidad"] < 1
    assert u["aportes"] is not None and abs(sum(u["aportes"].values()) + u["base"] - _logit(u["resultado"]["Probabilidad"])) < 1e-3
    assert [t.label for t in at.tabs] == ["Por qué este resultado", "Qué pasaría si…", "Cómo se calculó (técnico)", "Descargar"]
    assert any(m.value.startswith("### Qué hacer") for m in at.markdown)


def test_que_pasaria_si_recorre_todos_los_campos():
    from incidentes_app import analisis
    at = analizar_ejemplo(pagina("analizar.py"))
    for campo in analisis.CAMPOS_WHATIF:
        sel = next(s for s in at.selectbox if s.key == "whatif_campo")
        sel.select(campo).run()
        assert not at.exception, (campo, [e.value for e in at.exception])


def test_historial_registra_y_permite_reabrir():
    at = analizar_ejemplo(pagina("analizar.py"))
    from incidentes_app import historial
    h = historial.leer()
    assert len(h) == 1 and h.loc[0, "State"] == "PA"
    entrada = historial.deserializar(h.loc[0, "Entrada_json"])
    assert entrada["Stop"] is True and entrada["Start_Time"].year == 2022
    pag = pagina("historial.py")
    assert any("1" in m.value for m in pag.metric) or pag.metric


def test_explorador_tiempo_real_umbral_y_acerca_cargan():
    for nombre in ("explorador.py", "tiempo_real_vs_completa.py", "umbral.py", "acerca.py"):
        pagina(nombre)


def test_umbral_cambia_el_umbral_activo():
    at = pagina("umbral.py")
    sl = at.select_slider[0]
    oficial = sl.value                                    # sin umbral activo, el control arranca en el oficial
    sl.set_value(oficial + 5).run()
    assert not at.exception
    boton(at, "Usar este umbral").click().run()
    assert not at.exception
    assert at.session_state["umbral_activo"] is not None
    boton(at, "Volver al umbral oficial").click().run()
    assert not at.exception, [e.value for e in at.exception]   # antes: StreamlitAPIException (widget ya creado)
    assert at.session_state["umbral_activo"] is None
    assert at.select_slider[0].value == oficial           # y el control vuelve a la posicion oficial


def test_etiquetas_coinciden_con_el_modelo():
    from incidentes_app import config
    from incidentes_app.etiquetas import INFRAESTRUCTURA, VARIABLE
    config.preparar_importacion()
    from accidentes import config as cfg
    assert INFRAESTRUCTURA == cfg.INFRAESTRUCTURA
    faltan = [v for v in cfg.GRUPOS_TEMATICOS["Clima"] + cfg.GRUPOS_TEMATICOS["Tiempo"]
              + cfg.GRUPOS_TEMATICOS["Infraestructura"] + cfg.GRUPOS_TEMATICOS["Ubicacion"] if v not in VARIABLE]
    assert not faltan, f"sin etiqueta en espanol: {faltan}"


def _logit(p):
    import math
    return math.log(p / (1 - p))


def test_reabrir_un_caso_del_historial_llena_el_formulario():
    from incidentes_app import formulario, historial
    at = analizar_ejemplo(pagina("analizar.py"))
    entrada = historial.deserializar(historial.leer().loc[0, "Entrada_json"])
    nuevo = AppTest.from_file(str(RAIZ / "paginas" / "analizar.py"), default_timeout=TIEMPO)
    nuevo.session_state["_cargar"] = entrada
    nuevo.run()
    assert not nuevo.exception, [e.value for e in nuevo.exception]
    assert nuevo.session_state["f_estado"] == "PA"
    assert nuevo.session_state["f_i_Stop"] == "Sí" and nuevo.session_state["f_i_Junction"] == "No"
    assert nuevo.session_state["f_precip"] is None            # el dato que faltaba sigue faltando
    assert formulario.leer_estado is not None


def test_recomendacion_en_singular_y_plural():
    from incidentes_app import reglas
    assert reglas.recomendar("Critico", "Clima", 1)["nota_datos"].startswith("Faltó 1 campo")
    assert reglas.recomendar("Critico", "Clima", 3)["nota_datos"].startswith("Faltaron 3 campos")
    assert reglas.recomendar("Normal", "Clima", 0)["nota_datos"] is None
    assert reglas.recomendar("Normal", "Clima", 0)["nota_factor"] is None          # sin nota de factor en Normal
    assert reglas.recomendar("Critico", "Clima", 0)["nota_factor"].startswith("El factor")


def test_caso_critico_con_umbral_bajo_y_exportaciones():
    from incidentes_app import exportar
    at = pagina("analizar.py")
    at.session_state["umbral_activo"] = 0.02            # umbral bajo: el ejemplo cae en la zona Critico
    analizar_ejemplo(at)
    u = at.session_state["ultimo"]
    assert u["resultado"]["Nivel"] == "Critico" and u["resultado"]["Es_critico"]
    assert abs(u["umbral_usado"] - 0.02) < 1e-12
    assert any("Qué hacer: Respuesta prioritaria" in m.value for m in at.markdown)
    assert any(i.value.startswith("El factor") for i in at.info)             # nota del grupo dominante
    rec = u["recomendacion"]
    oficial = 0.137
    assert exportar.csv_bytes(__import__("pandas").DataFrame([exportar.fila_plana(
        u["entrada"], u["resultado"], u["umbral_usado"], rec)])).startswith(b"\xef\xbb\xbf")
    assert b"Respuesta prioritaria" in exportar.ficha_json(u["entrada"], u["resultado"], u["umbral_usado"], rec,
                                                           u["aportes"], u["base"], u["grupos"], oficial)
    html = exportar.ficha_html(u["entrada"], u["resultado"], u["umbral_usado"], rec, u["aportes"], u["grupos"],
                               oficial).decode("utf-8")
    assert "Respuesta prioritaria" in html and "Cr" in html and "(el oficial es" in html


def test_casos_reales_de_validacion_cargan_y_se_comparan_con_la_realidad():
    from incidentes_app import datos
    at = pagina("analizar.py")
    casos = datos.ejemplos()
    if not casos:
        pytest.skip("Falta models/reportes/ejemplos_app.json (eda/ejemplos_para_app.py en el repo del modelo + sincronizar_modelo.py).")
    vistos = set()
    for caso in casos:
        at = pagina("analizar.py")
        next(s for s in at.selectbox if s.key == "sel_ejemplo_real").select(caso["id"]).run()
        boton(at, "Cargar este caso").click().run()
        assert not at.exception, [e.value for e in at.exception]
        boton(at, "Analizar incidente").click().run()
        assert not at.exception, [e.value for e in at.exception]
        u = at.session_state["ultimo"]
        assert abs(u["resultado"]["Probabilidad"] - caso["probabilidad"]) < 2e-3        # el formulario reproduce el caso
        assert u["resultado"]["Nivel"] == caso["zona"]
        assert u["ejemplo_real"] is not None and u["ejemplo_real"]["id"] == caso["id"]
        vistos.add(u["resultado"]["Nivel"])
        textos = [s.value for s in list(at.success) + list(at.warning) + list(at.info)]
        assert any("Caso real de validación" in t for t in textos)
    assert len(vistos) >= 3                              # el recorrido toca varias zonas


# ---------------------------------------------------------------- ubicacion facil (sin escribir coordenadas)
def _sel(at, clave):
    return next(s for s in at.selectbox if s.key == clave)


def _texto(at, clave):
    return next(x for x in at.text_input if x.key == clave)


def test_sin_lugar_usa_el_centro_del_estado_y_avisa():
    from incidentes_app import lugares
    at = pagina("analizar.py")
    boton(at, "Vaciar").click().run()
    _sel(at, "f_estado").select("PA").run()
    assert not at.exception, [e.value for e in at.exception]
    boton(at, "Analizar incidente").click().run()
    assert not at.exception, [e.value for e in at.exception]
    u = at.session_state["ultimo"]
    assert (u["entrada"]["Start_Lat"], u["entrada"]["Start_Lng"]) == lugares.centro_del_estado("PA")
    assert u["ubicacion_aproximada"] is True
    assert any("Ubicación aproximada" in w.value for w in at.warning)


def test_elegir_una_ciudad_pone_el_lugar_y_cambiar_de_estado_lo_quita():
    at = pagina("analizar.py")
    boton(at, "Vaciar").click().run()
    _sel(at, "f_estado").select("PA").run()
    _sel(at, "f_ciudad").select("Pittsburgh").run()
    assert not at.exception, [e.value for e in at.exception]
    assert abs(at.session_state["f_lat"] - 40.44) < 1e-9 and at.session_state["f_lugar"] == "Pittsburgh, PA"
    boton(at, "Analizar incidente").click().run()
    assert at.session_state["ultimo"]["ubicacion_aproximada"] is False
    _sel(at, "f_estado").select("TX").run()                       # Pittsburgh no esta en Texas
    assert at.session_state["f_lat"] is None
    assert any("quité el lugar anterior" in w.value for w in at.warning)


def test_coordenadas_pegadas_y_enlace_de_google_maps():
    from incidentes_app import formulario
    at = pagina("analizar.py")
    boton(at, "Vaciar").click().run()
    _sel(at, "f_estado").select("PA").run()
    at.session_state["f_metodo_ubic"] = formulario.COORD
    at.run()
    _texto(at, "f_coords_texto").input("https://www.google.com/maps/place/X/@40.4406,-79.9959,12z").run()
    assert not at.exception, [e.value for e in at.exception]
    assert (at.session_state["f_lat"], at.session_state["f_lng"]) == (40.4406, -79.9959)
    _texto(at, "f_coords_texto").input("19.43, -99.13").run()          # Ciudad de Mexico: fuera de EE. UU.
    assert any("fuera de Estados Unidos" in w.value for w in at.warning)
    assert (at.session_state["f_lat"], at.session_state["f_lng"]) == (40.4406, -79.9959)    # no cambio


def test_lugar_que_no_cuadra_con_el_estado_avisa_y_sugiere_el_correcto():
    from incidentes_app import formulario
    at = pagina("analizar.py")
    boton(at, "Vaciar").click().run()
    _sel(at, "f_estado").select("TX").run()
    at.session_state["f_metodo_ubic"] = formulario.COORD
    at.run()
    _texto(at, "f_coords_texto").input("40.4103, -79.6192").run()          # Pensilvania
    assert any("fuera de Texas" in w.value and "Pennsylvania" in w.value for w in at.warning)
    boton(at, "Cambiar el estado a").click().run()
    assert at.session_state["f_estado"] == "PA" and not at.exception


def test_busqueda_de_direccion_con_respuesta_simulada(monkeypatch):
    import io
    import json
    import urllib.request
    from incidentes_app import formulario

    class Respuesta(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    cuerpo = json.dumps([{"lat": "40.4406248", "lon": "-79.9958864", "display_name": "Pittsburgh, Allegheny County, "
                          "Pennsylvania, United States", "address": {"ISO3166-2-lvl4": "US-PA", "state": "Pennsylvania"}},
                         {"lat": "19.4", "lon": "-99.1", "display_name": "Mexico", "address": {}}]).encode()
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Respuesta(cuerpo))
    at = pagina("analizar.py")
    boton(at, "Vaciar").click().run()
    at.session_state["f_metodo_ubic"] = formulario.BUSCAR
    at.run()
    _texto(at, "f_busqueda").input("pittsburgh prueba unica").run()
    assert not at.exception, [e.value for e in at.exception]
    res = _sel(at, "f_resultado")
    assert len(res.options) == 1                                        # el resultado de Mexico se descarta
    boton(at, "Usar este lugar").click().run()
    assert at.session_state["f_estado"] == "PA"                         # la busqueda tambien elige el estado
    assert abs(at.session_state["f_lat"] - 40.44062) < 1e-4


def test_busqueda_sin_internet_explica_que_hacer(monkeypatch):
    import urllib.request
    from incidentes_app import formulario

    def sin_red(*a, **k):
        raise OSError("sin red")
    monkeypatch.setattr(urllib.request, "urlopen", sin_red)
    at = pagina("analizar.py")
    at.session_state["f_metodo_ubic"] = formulario.BUSCAR
    at.run()
    _texto(at, "f_busqueda").input("sitio sin red unico").run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("No pude conectarme" in e.value for e in at.error)


def test_clic_en_el_mapa_pone_el_lugar(monkeypatch):
    streamlit_folium = pytest.importorskip("streamlit_folium")
    from incidentes_app import formulario
    monkeypatch.setattr(streamlit_folium, "st_folium", lambda *a, **k: {
        "last_clicked": {"lat": 40.0123456, "lng": -83.0123456}, "zoom": 9, "center": {"lat": 40.0, "lng": -83.0}})
    at = pagina("analizar.py")
    boton(at, "Vaciar").click().run()
    _sel(at, "f_estado").select("OH").run()
    at.session_state["f_metodo_ubic"] = formulario.MAPA
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert (at.session_state["f_lat"], at.session_state["f_lng"]) == (40.01235, -83.01235)
    assert at.session_state["f_lugar"] == "Punto marcado en el mapa"


def test_cada_campo_del_formulario_tiene_su_ayuda():
    at = pagina("analizar.py")
    sin_ayuda = []
    for w in (list(at.number_input) + list(at.selectbox) + list(at.text_input) + list(at.date_input)
              + list(at.time_input) + list(at.radio)):
        if w.key in ("sel_ejemplo_real", "f_resultado") or w.key is None:
            continue
        if not getattr(w, "help", None):
            sin_ayuda.append(w.key or w.label)
    assert not sin_ayuda, f"campos sin «?»: {sin_ayuda}"
    selector = next(w for w in at.get("segmented_control")) if at.get("segmented_control") else None
    assert selector is None or selector.proto.help

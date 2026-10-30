"""Pruebas del modulo de lugares (no necesitan el modelo ni internet)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from incidentes_app import lugares as L


def test_centros_y_ciudades_estan_dentro_de_su_estado():
    assert len(L.ESTADOS) == 51
    for cod in L.ESTADOS:
        assert L.dentro_del_estado(cod, *L.centro_del_estado(cod), tolerancia=0), cod
        for ciudad, lat, lng in L.ciudades(cod):
            assert L.dentro_del_estado(cod, lat, lng, tolerancia=0), (cod, ciudad)


@pytest.mark.parametrize("texto,esperado", [
    ("40.4103, -79.6192", (40.4103, -79.6192)),
    ("40.4103 -79.6192", (40.4103, -79.6192)),
    ("40.4103°N 79.6192°W", (40.4103, -79.6192)),
    ("34.05N 118.24O", (34.05, -118.24)),
    ("https://www.google.com/maps/place/Pittsburgh/@40.4406248,-79.9958864,12z/data=!3m1", (40.44062, -79.99589)),
    ("https://maps.google.com/?q=40.44,-79.99", (40.44, -79.99)),
    ("https://www.google.com/maps/place/X/data=!3d40.4406!4d-79.9959", (40.4406, -79.9959)),
])
def test_leer_coordenadas_formatos(texto, esperado):
    lat, lng, _ = L.leer_coordenadas(texto)
    assert (lat, lng) == esperado


def test_leer_coordenadas_corrige_orden_y_signo_y_rechaza_lo_imposible():
    assert L.leer_coordenadas("-79.6192, 40.4103")[:2] == (40.4103, -79.6192)      # invertidas
    lat, lng, nota = L.leer_coordenadas("40.4103, 79.6192")                          # falta el signo
    assert (lat, lng) == (40.4103, -79.6192) and "signo" in nota
    for malo in ("", "hola", "91, 10", "19.43, -99.13", "4.71, -74.07"):             # vacio, texto, rango, Mexico, Bogota
        assert L.leer_coordenadas(malo)[0] is None, malo


def test_estado_probable_y_es_centro():
    assert L.estado_probable(40.4103, -79.6192) == "PA"
    assert L.estado_probable(40.4103, -79.6192, entre=["TX"]) is None
    assert L.es_centro_del_estado("PA", *L.centro_del_estado("PA"))
    assert not L.es_centro_del_estado("PA", 40.44, -79.99)


def test_interpretar_respuesta_de_nominatim():
    r = L.interpretar_resultados([
        {"lat": "40.44", "lon": "-79.99", "display_name": "Pittsburgh, Pennsylvania, United States",
         "address": {"ISO3166-2-lvl4": "US-PA"}},
        {"lat": "19.4", "lon": "-99.1", "display_name": "Mexico", "address": {}}, {"sin": "datos"}])
    assert len(r) == 1 and r[0]["estado"] == "PA" and r[0]["texto"] == "Pittsburgh, Pennsylvania"

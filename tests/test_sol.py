"""Pruebas del calculo de dia y noche (sol.py). No necesitan el modelo."""

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from incidentes_app import sol  # noqa: E402

NASHVILLE = (36.16, -86.78, "TN")


def _minutos(texto):
    h, m = texto.split(":")
    return int(h) * 60 + int(m)


def test_salida_y_puesta_coinciden_con_valores_de_referencia():
    # Valores de la libreria astral (error maximo medido en 400 casos: 2.5 minutos).
    casos = [((36.16, -86.78, "TN"), dt.date(2025, 11, 14), "06:23", "16:39"),
             ((33.45, -112.07, "AZ"), dt.date(2025, 7, 4), "05:23", "19:41"),       # Arizona no cambia la hora
             ((47.61, -122.33, "WA"), dt.date(2025, 6, 21), "05:11", "21:10")]
    for (lat, lng, estado), fecha, salida, puesta in casos:
        sal, pue = sol.salida_y_puesta(fecha, lat, lng, estado)
        assert abs(sal - _minutos(salida)) <= 3 and abs(pue - _minutos(puesta)) <= 3, (estado, sol.hora_texto(sal))


def test_horario_de_verano_de_eeuu():
    assert sol.horario_de_verano(dt.date(2025, 3, 9), "TN") and not sol.horario_de_verano(dt.date(2025, 3, 8), "TN")
    assert sol.horario_de_verano(dt.date(2025, 11, 1), "TN") and not sol.horario_de_verano(dt.date(2025, 11, 2), "TN")
    assert not sol.horario_de_verano(dt.date(2025, 7, 4), "AZ")


def test_mediodia_es_dia_y_medianoche_es_noche():
    lat, lng, estado = NASHVILLE
    assert sol.dia_o_noche(dt.date(2025, 11, 14), dt.time(12, 0), lat, lng, estado) == "Day"
    assert sol.dia_o_noche(dt.date(2025, 11, 14), dt.time(22, 40), lat, lng, estado) == "Night"
    assert sol.dia_o_noche(dt.date(2025, 11, 14), dt.time(3, 0), lat, lng, estado) == "Night"


def test_amanecer_y_atardecer_son_dudosos():
    lat, lng, estado = NASHVILLE
    assert sol.dia_o_noche(dt.date(2025, 11, 14), dt.time(17, 0), lat, lng, estado) is None    # 20 min tras la puesta
    assert sol.dia_o_noche(dt.date(2025, 11, 14), dt.time(6, 40), lat, lng, estado) is None
    assert sol.dia_o_noche(dt.date(2025, 7, 4), dt.time(20, 30), lat, lng, estado) is None


def test_sin_datos_del_estado_o_sin_sol_no_responde():
    assert sol.dia_o_noche(dt.date(2025, 7, 4), dt.time(12, 0), 36.16, -86.78, "XX") is None
    assert sol.dia_o_noche(dt.date(2025, 6, 21), dt.time(12, 0), 80.0, -86.78, "AK") is None  # sol de medianoche

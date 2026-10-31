"""
SOL: ¿es de dia o de noche a esa hora, en ese lugar y en esa fecha?

Sirve para una sola cosa: avisar cuando el campo «Día o noche» del formulario no cuadra con la hora del reporte
(por ejemplo, «Noche» a las 12:00). El modelo usa los dos datos tal como llegan; si se contradicen, la estimacion
empeora sin que nadie lo note.

No es astronomia de precision. La salida y la puesta del sol se calculan con la formula aproximada de la NOAA
(error de un par de minutos) y la hora del reloj se pasa a hora solar con el huso tipico del estado y el horario de
verano de EE. UU. En los estados partidos en dos husos el huso puede fallar por una hora, asi que solo se
responde «dia» o «noche» cuando la hora cae a mas de MARGEN_MIN minutos de la salida o la puesta del sol;
en el resto (amanecer y atardecer) se responde None y la app no avisa de nada.
"""

import datetime as dt
import math

MARGEN_MIN = 90

# Huso estandar tipico de cada estado, en horas respecto de UTC (-5 este, -6 centro, -7 montaña, -8 pacifico).
# Los estados partidos en dos husos llevan el de la mayor parte de su territorio (el margen cubre la diferencia).
_HUSO = {
    **dict.fromkeys(["CT", "DE", "DC", "FL", "GA", "IN", "KY", "ME", "MD", "MA", "MI", "NH", "NJ", "NY", "NC",
                     "OH", "PA", "RI", "SC", "VT", "VA", "WV"], -5),
    **dict.fromkeys(["AL", "AR", "IL", "IA", "KS", "LA", "MN", "MS", "MO", "NE", "ND", "OK", "SD", "TN", "TX",
                     "WI"], -6),
    **dict.fromkeys(["AZ", "CO", "ID", "MT", "NM", "UT", "WY"], -7),
    **dict.fromkeys(["CA", "NV", "OR", "WA"], -8),
    "AK": -9, "HI": -10,
}
_SIN_HORARIO_DE_VERANO = {"AZ", "HI"}


def _domingo(año, mes, n):
    """Fecha del n-esimo domingo del mes."""
    d = dt.date(año, mes, 1)
    primero = d + dt.timedelta(days=(6 - d.weekday()) % 7)
    return primero + dt.timedelta(weeks=n - 1)


def horario_de_verano(fecha, estado):
    """True si en ese estado rige el horario de verano de EE. UU. (2.º domingo de marzo al 1.º de noviembre)."""
    if estado in _SIN_HORARIO_DE_VERANO:
        return False
    return _domingo(fecha.year, 3, 2) <= fecha < _domingo(fecha.year, 11, 1)


def _salida_y_puesta_utc(fecha, lat, lng):
    """Minutos desde las 00:00 UTC del dia `fecha` para la salida y la puesta del sol (None si no hay)."""
    dia_juliano = fecha.toordinal() + 1721424.5
    t = (dia_juliano - 2451545.0) / 36525.0
    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    mr = math.radians(m)
    c = (math.sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t))
         + math.sin(2 * mr) * (0.019993 - 0.000101 * t) + math.sin(3 * mr) * 0.000289)
    lon_ver = l0 + c - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * t))
    oblicuidad = (23 + (26 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60) / 60
                  + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * t)))
    decl = math.asin(math.sin(math.radians(oblicuidad)) * math.sin(math.radians(lon_ver)))
    y = math.tan(math.radians(oblicuidad) / 2) ** 2
    l0r = math.radians(l0)
    ecuacion_tiempo = 4 * math.degrees(y * math.sin(2 * l0r) - 2 * e * math.sin(mr)
                                       + 4 * e * y * math.sin(mr) * math.cos(2 * l0r)
                                       - 0.5 * y * y * math.sin(4 * l0r) - 1.25 * e * e * math.sin(2 * mr))
    cos_h = (math.cos(math.radians(90.833)) / (math.cos(math.radians(lat)) * math.cos(decl))
             - math.tan(math.radians(lat)) * math.tan(decl))
    if not -1 <= cos_h <= 1:                       # sol de medianoche o noche polar
        return None, None
    h = math.degrees(math.acos(cos_h))
    mediodia = 720 - 4 * lng - ecuacion_tiempo     # lng positiva al este
    return mediodia - 4 * h, mediodia + 4 * h


def salida_y_puesta(fecha, lat, lng, estado):
    """(salida, puesta) en minutos del reloj local de ese dia, o (None, None) si no se puede calcular."""
    huso = _HUSO.get(estado)
    if huso is None:
        return None, None
    sal, pue = _salida_y_puesta_utc(fecha, lat, lng)
    if sal is None:
        return None, None
    desfase = 60 * (huso + (1 if horario_de_verano(fecha, estado) else 0))
    return (sal + desfase) % 1440, (pue + desfase) % 1440


def dia_o_noche(fecha, hora, lat, lng, estado):
    """'Day' o 'Night' si la hora cae claramente de dia o de noche; None si es dudoso (amanecer, atardecer, sin datos)."""
    sal, pue = salida_y_puesta(fecha, lat, lng, estado)
    if sal is None or not (0 <= sal < pue <= 1440):
        return None
    minuto = hora.hour * 60 + hora.minute
    if sal + MARGEN_MIN <= minuto <= pue - MARGEN_MIN:
        return "Day"
    if minuto <= sal - MARGEN_MIN or minuto >= pue + MARGEN_MIN:
        return "Night"
    return None


def hora_texto(minutos):
    m = int(round(minutos)) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"

"""
LUGARES: formas faciles de decir DONDE ocurrio el incidente, sin escribir latitud y longitud a mano.

El modelo necesita coordenadas (la ubicacion es su señal mas fuerte), pero el operador casi nunca las conoce.
Este modulo las obtiene de cuatro maneras, de la mas simple a la mas tecnica:

  1. Ciudad de una lista (sin internet) o «centro del estado» si no se sabe el lugar (ubicacion aproximada).
  2. Buscar una direccion o un lugar por nombre (servicio gratuito OpenStreetMap/Nominatim; necesita internet).
  3. Hacer clic en un mapa (necesita internet para dibujar el mapa; ver formulario.py).
  4. Pegar coordenadas o un enlace de Google Maps (`leer_coordenadas`).

Las coordenadas de ciudades y los rectangulos de cada estado son aproximados (sirven para ubicar y para avisar
cuando un punto no cuadra con el estado elegido; no son datos del modelo).
"""

import json
import re
import urllib.parse
import urllib.request

# codigo: (nombre, (lat, lng) del centro, (lat_min, lat_max, lng_min, lng_max), [(ciudad, lat, lng), ...])
ESTADOS = {
    "AL": ("Alabama", (32.81, -86.79), (30.2, 35.0, -88.5, -84.9),
           [("Birmingham", 33.52, -86.80), ("Montgomery", 32.38, -86.30), ("Huntsville", 34.73, -86.59), ("Mobile", 30.69, -88.04)]),
    "AK": ("Alaska", (63.35, -152.0), (51.2, 71.5, -180.0, -129.9),
           [("Anchorage", 61.22, -149.90), ("Fairbanks", 64.84, -147.72), ("Juneau", 58.30, -134.42)]),
    "AZ": ("Arizona", (34.29, -111.66), (31.3, 37.0, -114.9, -109.0),
           [("Phoenix", 33.45, -112.07), ("Tucson", 32.22, -110.97), ("Mesa", 33.42, -111.83), ("Flagstaff", 35.20, -111.65)]),
    "AR": ("Arkansas", (34.97, -92.37), (33.0, 36.5, -94.7, -89.6),
           [("Little Rock", 34.75, -92.29), ("Fayetteville", 36.06, -94.16), ("Fort Smith", 35.39, -94.40)]),
    "CA": ("California", (37.18, -119.47), (32.5, 42.0, -124.5, -114.1),
           [("Los Angeles", 34.05, -118.24), ("San Francisco", 37.77, -122.42), ("San Diego", 32.72, -117.16),
            ("Sacramento", 38.58, -121.49), ("San José", 37.34, -121.89), ("Fresno", 36.74, -119.79)]),
    "CO": ("Colorado", (38.99, -105.55), (36.99, 41.0, -109.1, -102.0),
           [("Denver", 39.74, -104.99), ("Colorado Springs", 38.83, -104.82), ("Fort Collins", 40.59, -105.08)]),
    "CT": ("Connecticut", (41.62, -72.73), (40.95, 42.05, -73.73, -71.78),
           [("Hartford", 41.76, -72.67), ("New Haven", 41.31, -72.92), ("Stamford", 41.05, -73.54), ("Bridgeport", 41.19, -73.20)]),
    "DE": ("Delaware", (39.00, -75.50), (38.45, 39.84, -75.79, -75.04),
           [("Wilmington", 39.74, -75.55), ("Dover", 39.16, -75.52)]),
    "DC": ("District of Columbia", (38.90, -77.04), (38.79, 38.995, -77.12, -76.91),
           [("Washington", 38.91, -77.04)]),
    "FL": ("Florida", (28.63, -82.45), (24.4, 31.0, -87.7, -80.0),
           [("Miami", 25.76, -80.19), ("Orlando", 28.54, -81.38), ("Tampa", 27.95, -82.46),
            ("Jacksonville", 30.33, -81.66), ("Tallahassee", 30.44, -84.28)]),
    "GA": ("Georgia", (32.64, -83.44), (30.35, 35.0, -85.65, -80.8),
           [("Atlanta", 33.75, -84.39), ("Savannah", 32.08, -81.09), ("Augusta", 33.47, -81.97), ("Columbus", 32.46, -84.99)]),
    "HI": ("Hawaii", (20.29, -156.37), (18.9, 22.3, -160.3, -154.8),
           [("Honolulu", 21.31, -157.86), ("Hilo", 19.71, -155.09)]),
    "ID": ("Idaho", (44.35, -114.61), (42.0, 49.0, -117.25, -111.0),
           [("Boise", 43.62, -116.20), ("Idaho Falls", 43.49, -112.04), ("Coeur d'Alene", 47.68, -116.78)]),
    "IL": ("Illinois", (40.04, -89.20), (36.97, 42.51, -91.52, -87.0),
           [("Chicago", 41.88, -87.63), ("Springfield", 39.80, -89.64), ("Peoria", 40.69, -89.59), ("Rockford", 42.27, -89.09)]),
    "IN": ("Indiana", (39.89, -86.28), (37.77, 41.77, -88.1, -84.78),
           [("Indianapolis", 39.77, -86.16), ("Fort Wayne", 41.08, -85.14), ("Evansville", 37.97, -87.57), ("South Bend", 41.68, -86.25)]),
    "IA": ("Iowa", (42.07, -93.50), (40.37, 43.5, -96.65, -90.14),
           [("Des Moines", 41.59, -93.62), ("Cedar Rapids", 41.98, -91.67), ("Davenport", 41.52, -90.58)]),
    "KS": ("Kansas", (38.49, -98.38), (36.99, 40.0, -102.05, -94.59),
           [("Wichita", 37.69, -97.34), ("Topeka", 39.05, -95.68), ("Kansas City", 39.11, -94.63)]),
    "KY": ("Kentucky", (37.53, -85.30), (36.5, 39.15, -89.57, -81.96),
           [("Louisville", 38.25, -85.76), ("Lexington", 38.04, -84.50), ("Bowling Green", 36.99, -86.44)]),
    "LA": ("Louisiana", (31.07, -91.99), (28.9, 33.02, -94.04, -88.8),
           [("New Orleans", 29.95, -90.07), ("Baton Rouge", 30.45, -91.15), ("Shreveport", 32.53, -93.75), ("Lafayette", 30.22, -92.02)]),
    "ME": ("Maine", (45.25, -69.23), (43.06, 47.46, -71.08, -66.95),
           [("Portland", 43.66, -70.26), ("Bangor", 44.80, -68.77), ("Augusta", 44.31, -69.78)]),
    "MD": ("Maryland", (39.06, -76.80), (37.9, 39.72, -79.49, -75.05),
           [("Baltimore", 39.29, -76.61), ("Annapolis", 38.98, -76.49), ("Rockville", 39.08, -77.15), ("Frederick", 39.41, -77.41)]),
    "MA": ("Massachusetts", (42.26, -71.81), (41.24, 42.89, -73.51, -69.93),
           [("Boston", 42.36, -71.06), ("Worcester", 42.26, -71.80), ("Springfield", 42.10, -72.59), ("Cambridge", 42.37, -71.11)]),
    "MI": ("Michigan", (44.35, -85.41), (41.7, 48.3, -90.42, -82.41),
           [("Detroit", 42.33, -83.05), ("Grand Rapids", 42.96, -85.67), ("Lansing", 42.73, -84.55), ("Ann Arbor", 42.28, -83.74)]),
    "MN": ("Minnesota", (46.28, -94.31), (43.5, 49.4, -97.24, -89.49),
           [("Minneapolis", 44.98, -93.27), ("Saint Paul", 44.95, -93.09), ("Duluth", 46.79, -92.10), ("Rochester", 44.02, -92.47)]),
    "MS": ("Mississippi", (32.74, -89.67), (30.17, 35.0, -91.66, -88.1),
           [("Jackson", 32.30, -90.18), ("Gulfport", 30.37, -89.09), ("Hattiesburg", 31.33, -89.29)]),
    "MO": ("Missouri", (38.46, -92.29), (35.99, 40.61, -95.77, -89.1),
           [("Kansas City", 39.10, -94.58), ("St. Louis", 38.63, -90.20), ("Springfield", 37.21, -93.29), ("Columbia", 38.95, -92.33)]),
    "MT": ("Montana", (47.05, -109.63), (44.36, 49.0, -116.05, -104.04),
           [("Billings", 45.78, -108.50), ("Missoula", 46.87, -114.00), ("Bozeman", 45.68, -111.04)]),
    "NE": ("Nebraska", (41.54, -99.80), (40.0, 43.0, -104.05, -95.31),
           [("Omaha", 41.26, -95.93), ("Lincoln", 40.81, -96.70)]),
    "NV": ("Nevada", (39.33, -116.63), (35.0, 42.0, -120.0, -114.04),
           [("Las Vegas", 36.17, -115.14), ("Reno", 39.53, -119.81), ("Henderson", 36.04, -114.98)]),
    "NH": ("New Hampshire", (43.68, -71.58), (42.7, 45.31, -72.56, -70.7),
           [("Manchester", 42.99, -71.46), ("Concord", 43.21, -71.54), ("Nashua", 42.77, -71.47)]),
    "NJ": ("New Jersey", (40.19, -74.67), (38.93, 41.36, -75.56, -73.89),
           [("Newark", 40.74, -74.17), ("Jersey City", 40.73, -74.06), ("Trenton", 40.22, -74.76), ("Atlantic City", 39.36, -74.42)]),
    "NM": ("New Mexico", (34.41, -106.11), (31.33, 37.0, -109.05, -103.0),
           [("Albuquerque", 35.08, -106.65), ("Santa Fe", 35.69, -105.94), ("Las Cruces", 32.32, -106.76)]),
    "NY": ("New York", (42.95, -75.53), (40.5, 45.02, -79.76, -71.86),
           [("New York City", 40.71, -74.01), ("Buffalo", 42.89, -78.88), ("Albany", 42.65, -73.76),
            ("Rochester", 43.16, -77.61), ("Syracuse", 43.05, -76.15)]),
    "NC": ("North Carolina", (35.56, -79.39), (33.84, 36.59, -84.32, -75.46),
           [("Charlotte", 35.23, -80.84), ("Raleigh", 35.78, -78.64), ("Greensboro", 36.07, -79.79), ("Asheville", 35.60, -82.55)]),
    "ND": ("North Dakota", (47.45, -100.47), (45.93, 49.0, -104.05, -96.55),
           [("Fargo", 46.88, -96.79), ("Bismarck", 46.81, -100.78)]),
    "OH": ("Ohio", (40.29, -82.79), (38.4, 41.98, -84.82, -80.52),
           [("Columbus", 39.96, -83.00), ("Cleveland", 41.50, -81.69), ("Cincinnati", 39.10, -84.51),
            ("Toledo", 41.65, -83.54), ("Akron", 41.08, -81.52)]),
    "OK": ("Oklahoma", (35.59, -97.49), (33.62, 37.0, -103.0, -94.43),
           [("Oklahoma City", 35.47, -97.52), ("Tulsa", 36.15, -95.99)]),
    "OR": ("Oregon", (43.94, -120.56), (41.99, 46.3, -124.6, -116.46),
           [("Portland", 45.52, -122.68), ("Salem", 44.94, -123.04), ("Eugene", 44.05, -123.09), ("Bend", 44.06, -121.31)]),
    "PA": ("Pennsylvania", (40.88, -77.80), (39.72, 42.27, -80.52, -74.69),
           [("Philadelphia", 39.95, -75.17), ("Pittsburgh", 40.44, -79.99), ("Harrisburg", 40.27, -76.88),
            ("Allentown", 40.60, -75.47), ("Erie", 42.13, -80.09)]),
    "RI": ("Rhode Island", (41.68, -71.51), (41.15, 42.02, -71.86, -71.12),
           [("Providence", 41.82, -71.41), ("Warwick", 41.70, -71.42)]),
    "SC": ("South Carolina", (33.92, -80.90), (32.03, 35.22, -83.35, -78.54),
           [("Columbia", 34.00, -81.03), ("Charleston", 32.78, -79.93), ("Greenville", 34.85, -82.40)]),
    "SD": ("South Dakota", (44.44, -100.23), (42.48, 45.95, -104.06, -96.44),
           [("Sioux Falls", 43.55, -96.73), ("Rapid City", 44.08, -103.23)]),
    "TN": ("Tennessee", (35.86, -86.35), (34.98, 36.68, -90.31, -81.65),
           [("Nashville", 36.16, -86.78), ("Memphis", 35.15, -90.05), ("Knoxville", 35.96, -83.92), ("Chattanooga", 35.05, -85.31)]),
    "TX": ("Texas", (31.47, -99.33), (25.84, 36.5, -106.65, -93.51),
           [("Houston", 29.76, -95.37), ("Dallas", 32.78, -96.80), ("Austin", 30.27, -97.74),
            ("San Antonio", 29.42, -98.49), ("Fort Worth", 32.75, -97.33), ("El Paso", 31.76, -106.49)]),
    "UT": ("Utah", (39.32, -111.68), (37.0, 42.0, -114.05, -109.04),
           [("Salt Lake City", 40.76, -111.89), ("Provo", 40.23, -111.66), ("St. George", 37.10, -113.58)]),
    "VT": ("Vermont", (44.07, -72.67), (42.73, 45.02, -73.44, -71.46),
           [("Burlington", 44.48, -73.21), ("Montpelier", 44.26, -72.58)]),
    "VA": ("Virginia", (37.52, -78.85), (36.54, 39.47, -83.68, -75.24),
           [("Richmond", 37.54, -77.44), ("Virginia Beach", 36.85, -75.98), ("Arlington", 38.88, -77.10),
            ("Norfolk", 36.85, -76.29), ("Roanoke", 37.27, -79.94)]),
    "WA": ("Washington", (47.38, -120.45), (45.54, 49.0, -124.85, -116.92),
           [("Seattle", 47.61, -122.33), ("Spokane", 47.66, -117.43), ("Tacoma", 47.25, -122.44), ("Vancouver", 45.64, -122.66)]),
    "WV": ("West Virginia", (38.64, -80.62), (37.2, 40.64, -82.64, -77.72),
           [("Charleston", 38.35, -81.63), ("Morgantown", 39.63, -79.96), ("Huntington", 38.42, -82.45)]),
    "WI": ("Wisconsin", (44.62, -89.99), (42.49, 47.31, -92.89, -86.25),
           [("Milwaukee", 43.04, -87.91), ("Madison", 43.07, -89.40), ("Green Bay", 44.52, -88.02)]),
    "WY": ("Wyoming", (42.99, -107.55), (40.99, 45.01, -111.06, -104.05),
           [("Cheyenne", 41.14, -104.82), ("Casper", 42.87, -106.31), ("Jackson", 43.48, -110.76)]),
}

TOLERANCIA_GRADOS = 0.3      # margen al comprobar si un punto cae dentro del rectangulo del estado
CENTRO_EEUU = (39.5, -98.35)


def nombre_estado(codigo):
    return ESTADOS[codigo][0] if codigo in ESTADOS else str(codigo)


def etiqueta_estado(codigo):
    """'PA' -> 'Pennsylvania (PA)'."""
    return f"{nombre_estado(codigo)} ({codigo})" if codigo in ESTADOS else str(codigo)


def centro_del_estado(codigo):
    """(lat, lng) del centro del estado o None si no esta en la tabla."""
    return ESTADOS[codigo][1] if codigo in ESTADOS else None


def ciudades(codigo):
    """Lista [(nombre, lat, lng)] de las ciudades principales del estado."""
    return list(ESTADOS[codigo][3]) if codigo in ESTADOS else []


def es_centro_del_estado(codigo, lat, lng):
    c = centro_del_estado(codigo)
    return c is not None and lat is not None and abs(c[0] - lat) < 1e-6 and abs(c[1] - lng) < 1e-6


def dentro_del_estado(codigo, lat, lng, tolerancia=TOLERANCIA_GRADOS):
    """True/False si el punto cae en el rectangulo (aproximado) del estado; None si no hay datos del estado."""
    if codigo not in ESTADOS:
        return None
    la0, la1, lo0, lo1 = ESTADOS[codigo][2]
    return (la0 - tolerancia <= lat <= la1 + tolerancia) and (lo0 - tolerancia <= lng <= lo1 + tolerancia)


def estado_probable(lat, lng, entre=None):
    """Codigo del estado cuyo rectangulo contiene el punto (el de centro mas cercano si hay varios) o None."""
    candidatos = []
    for cod, (_n, (clat, clng), (la0, la1, lo0, lo1), _c) in ESTADOS.items():
        if entre is not None and cod not in entre:
            continue
        if la0 <= lat <= la1 and lo0 <= lng <= lo1:
            candidatos.append(((lat - clat) ** 2 + (lng - clng) ** 2, cod))
    return min(candidatos)[1] if candidatos else None


# ----------------------------------------------------------------------------
# Coordenadas escritas o pegadas
# ----------------------------------------------------------------------------
_NUM = r"[-+]?\d{1,3}(?:\.\d+)?"
_PATRONES_ENLACE = [
    re.compile(rf"@({_NUM}),({_NUM})"),                       # google.com/maps/@40.41,-79.61,15z
    re.compile(rf"!3d({_NUM})!4d({_NUM})"),                   # .../data=!3d40.41!4d-79.61
    re.compile(rf"[?&](?:q|ll|query|destination)=({_NUM})(?:,|%2C)\s*({_NUM})", re.I),
]
_GRADOS = re.compile(rf"({_NUM})\s*°?\s*([NSns])?\s*[,;\s]\s*({_NUM})\s*°?\s*([EWOewo])?")


def _plausible_eeuu(lat, lng):
    """El punto cae en (o muy cerca de) algun estado de EE. UU., segun los rectangulos aproximados."""
    return any(dentro_del_estado(c, lat, lng, 0.5) for c in ESTADOS)


def leer_coordenadas(texto):
    """Interpreta lo que pega el usuario. Devuelve (lat, lng, nota) o (None, None, mensaje_de_error).

    Acepta: «40.4103, -79.6192», «40.4103 -79.6192», «40.4103°N 79.6192°W», y enlaces de Google Maps con
    @lat,lng, !3dlat!4dlng, ?q=lat,lng. Si vienen invertidas (longitud primero) las corrige y lo avisa.
    """
    if not texto or not str(texto).strip():
        return None, None, "Escriba o pegue las coordenadas."
    t = urllib.parse.unquote(str(texto).strip())
    par = None
    for patron in _PATRONES_ENLACE:
        m = patron.search(t)
        if m:
            par = (float(m.group(1)), float(m.group(2)))
            break
    if par is None:
        m = _GRADOS.search(t)
        if not m:
            return None, None, ("No reconozco coordenadas ahí. Ejemplo: 40.4103, -79.6192 "
                                "(o pegue el enlace de Google Maps del lugar).")
        a, ha, b, hb = float(m.group(1)), (m.group(2) or "").upper(), float(m.group(3)), (m.group(4) or "").upper()
        if ha == "S":
            a = -abs(a)
        if hb in ("W", "O"):                                  # oeste (O en español)
            b = -abs(b)
        par = (a, b)
    lat, lng = par
    nota = None
    if abs(lat) > 90 or abs(lng) > 180:
        return None, None, "Esos números no son coordenadas válidas (latitud entre −90 y 90, longitud entre −180 y 180)."
    if not _plausible_eeuu(lat, lng) and _plausible_eeuu(lng, lat):
        lat, lng, nota = lng, lat, "Parecían estar al revés (longitud primero); las invertí."
    elif lng > 0 and _plausible_eeuu(lat, -lng):
        lng, nota = -lng, "En EE. UU. la longitud es negativa (oeste); le cambié el signo."
    if not _plausible_eeuu(lat, lng):
        return None, None, "Ese punto queda fuera de Estados Unidos, que es donde se entrenó el modelo."
    return round(lat, 5), round(lng, 5), nota


# ----------------------------------------------------------------------------
# Busqueda por nombre o direccion (OpenStreetMap / Nominatim, gratis, necesita internet)
# ----------------------------------------------------------------------------
URL_BUSQUEDA = "https://nominatim.openstreetmap.org/search"
AGENTE = "incidentes-viales-app/1.0 (proyecto academico, uso local)"


class BusquedaNoDisponible(Exception):
    """No hubo conexion con el servicio de busqueda."""


def _codigo_de_resultado(item):
    """Codigo de estado (PA) de un resultado de Nominatim, o None."""
    direccion = item.get("address", {}) or {}
    iso = direccion.get("ISO3166-2-lvl4", "")
    if iso.startswith("US-") and iso[3:] in ESTADOS:
        return iso[3:]
    nombre = direccion.get("state")
    for cod, (n, *_r) in ESTADOS.items():
        if n == nombre:
            return cod
    return None


def interpretar_resultados(respuesta):
    """Convierte la respuesta JSON de Nominatim en [{texto, lat, lng, estado}] (solo EE. UU.)."""
    salida = []
    for item in respuesta or []:
        try:
            lat, lng = float(item["lat"]), float(item["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        if not _plausible_eeuu(lat, lng):
            continue
        texto = str(item.get("display_name", "")).replace(", United States", "")
        salida.append({"texto": texto, "lat": round(lat, 5), "lng": round(lng, 5), "estado": _codigo_de_resultado(item)})
    return salida


def buscar(texto, estado=None, limite=6, tiempo_max=8):
    """Busca un lugar. Devuelve [{texto, lat, lng, estado}]. BusquedaNoDisponible si no hay conexion."""
    consulta = str(texto).strip()
    if not consulta:
        return []
    if estado in ESTADOS and nombre_estado(estado).lower() not in consulta.lower():
        consulta = f"{consulta}, {nombre_estado(estado)}"
    url = URL_BUSQUEDA + "?" + urllib.parse.urlencode({
        "q": consulta, "format": "jsonv2", "limit": limite, "addressdetails": 1, "countrycodes": "us"})
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept-Language": "es,en"})
    try:
        with urllib.request.urlopen(peticion, timeout=tiempo_max) as r:
            return interpretar_resultados(json.loads(r.read().decode("utf-8")))
    except (OSError, ValueError) as e:          # URLError, timeout y JSON invalido
        raise BusquedaNoDisponible(str(e)) from e

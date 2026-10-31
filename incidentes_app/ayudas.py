"""
TEXTOS DE AYUDA para personas sin conocimientos de transito ni de datos.

Cada campo del formulario tiene un «?» (parametro `help` de Streamlit) que dice, en palabras sencillas,
QUE es el dato, COMO escribirlo y QUE hacer si no se sabe. Los valores de referencia ayudan a quien no
conoce las unidades de EE. UU. (grados Fahrenheit, millas, pulgadas).
"""

AYUDA = {
    "f_fecha": "El día en que se recibió el reporte del accidente. Por defecto aparece hoy; cámbielo si está "
               "analizando un caso de otro día.",
    "f_hora": "La hora local en que se recibió el reporte, en formato de 24 horas (por ejemplo 17:30 son las 5:30 de la "
              "tarde). La hora importa: en las horas de más tráfico los accidentes tienen otro patrón.",
    "f_estado": "El estado de EE. UU. donde ocurrió el accidente. **Es obligatorio** porque el riesgo cambia mucho de un "
                "estado a otro. Puede escribir las primeras letras para buscarlo.",
    "f_metodo_ubic": "Elija la forma que le resulte más fácil. **Nadie tiene que saber latitud y longitud**: basta con "
                     "elegir una ciudad, buscar la dirección o marcar el lugar en el mapa. Si no sabe el lugar exacto, "
                     "no pasa nada: el sistema usa el centro del estado y avisa que el resultado es más aproximado.",
    "f_ciudad": "Ciudad principal más cercana al accidente. Es una ubicación aproximada (el centro de la ciudad). "
                "Para más precisión use «Buscar» o «Mapa».",
    "f_busqueda": "Escriba una dirección, una calle, una ciudad o un lugar conocido (por ejemplo «I-95 y Broad St, "
                  "Philadelphia» o «aeropuerto de Dallas»). Necesita conexión a internet.",
    "f_coords_texto": "Si ya tiene las coordenadas, péguelas aquí. **Truco con Google Maps:** haga clic derecho sobre "
                      "el lugar y toque los dos números que aparecen arriba del menú (se copian solos); péguelos aquí. "
                      "También sirve pegar el enlace del lugar.",
    "f_temp": "Temperatura del aire en **grados Fahrenheit (°F)**, como se usa en EE. UU. Referencias: 32 °F = 0 °C "
              "(hielo), 68 °F = 20 °C, 95 °F = 35 °C. Si solo conoce los °C: multiplique por 1,8 y sume 32. "
              "Si no lo sabe, déjelo vacío.",
    "f_hum": "Cuánta humedad hay en el aire, de 0 a 100 %. Día seco: 20 a 40 %. Lluvia o niebla: 80 a 100 %. "
             "Si no lo sabe, déjelo vacío.",
    "f_pres": "Presión del aire en **pulgadas de mercurio**. Lo normal está entre 29 y 31 (por ejemplo 29,92). "
              "Casi nadie lo conoce: déjelo vacío y el sistema usa un valor típico; casi no cambia el resultado.",
    "f_vis": "Hasta qué distancia se ve con claridad, en **millas** (1 milla ≈ 1,6 km). 10 = día despejado; "
             "1 o menos = niebla densa o tormenta fuerte. Si no lo sabe, déjelo vacío.",
    "f_viento": "Velocidad del viento en **millas por hora** (1 mph ≈ 1,6 km/h). 0 a 5 = casi sin viento; "
                "20 o más = ventoso; 40 o más = temporal. Si no lo sabe, déjelo vacío.",
    "f_precip": "Lluvia o nieve caída, en **pulgadas** (1 pulgada ≈ 25 mm). 0 = no llueve; 0,1 = llovizna; "
                "0,3 o más = lluvia fuerte. Si no sabe, déjelo vacío.",
    "f_clima": "El tipo de tiempo que hay en el lugar: despejado, nublado, lluvia, tormenta, nieve o niebla. "
               "Elija el que más se parezca.",
    "f_dirviento": "De qué lado sopla el viento (N = norte, S = sur, E = este, W = oeste). «Sin viento» si está en "
                   "calma. Casi no influye: si no lo sabe, déjelo vacío.",
    "f_dianoche": "Si en ese momento hay luz del sol (día) o ya oscureció (noche) en el lugar. No es lo mismo que la hora "
                  "del reloj: a las 6 de la tarde puede ser de día en verano y de noche en invierno. Si no cuadra con la hora "
                  "del reporte, la aplicación se lo avisa.",
    "f_tipovia": "La clase de camino donde ocurrió. Si no sabe, déjelo vacío o escriba el nombre de la calle "
                 "(más abajo) y el sistema lo deduce.",
    "f_calle": "Opcional. Escríbalo como figura en el reporte (por ejemplo «I-95 N» o «Main St»). Solo se usa cuando "
               "no elige el tipo de vía: el sistema lo deduce del nombre.",
}

# «¿Hay esto en el lugar?»: que es cada elemento de la via, en palabras de todos los dias.
AYUDA_INFRA = {
    "Amenity": "Un servicio o local junto al lugar del accidente: tienda, gasolinera, restaurante, escuela, "
               "estacionamiento, hospital…",
    "Bump": "Un resalto, tope o «lomo de burro» que obliga a reducir la velocidad.",
    "Crossing": "Un cruce peatonal (paso de cebra o paso señalizado para quienes caminan).",
    "Give_Way": "Una señal de «ceda el paso» (el triángulo): quien llega debe dejar pasar al otro.",
    "Junction": "Una intersección: calles que se cruzan, un empalme, o una rampa de entrada o salida de autopista.",
    "No_Exit": "Una calle sin salida.",
    "Railway": "Un cruce con vías del tren.",
    "Roundabout": "Una rotonda o glorieta.",
    "Station": "Una estación cercana (de tren, de metro o de buses).",
    "Stop": "Una señal de PARE.",
    "Traffic_Calming": "Elementos para bajar la velocidad en la calle: reductores, estrechamientos, desvíos suaves…",
    "Traffic_Signal": "Un semáforo.",
    "Turning_Loop": "Un ensanche al final de una vía para dar la vuelta.",
}
AYUDA_BANDERA = ("**Sí** = hay uno en el lugar · **No** = no hay · **No sé** = el sistema usa lo más habitual. "
                 "Si el reporte no lo menciona, deje «No sé».")

# Como se muestran los valores que el modelo conoce con nombres tecnicos.
TIPO_VIA_TEXTO = {
    "Interestatal": "Interestatal (I-95, I-10…)",
    "Carretera_US": "Carretera federal US (US-1, US-30…)",
    "Ruta_estatal": "Ruta estatal (SR-9, PA-28…)",
    "Autopista": "Autopista o vía rápida (freeway, parkway, turnpike)",
    "Carretera": "Carretera (Highway / Hwy)",
    "Local": "Calle o camino local (St, Ave, Rd…)",
    "Otro": "Otro tipo",
}
VIENTO_TEXTO = {"Calm": "Sin viento (calma)", "VAR": "Variable", "N": "Norte (N)", "S": "Sur (S)", "E": "Este (E)",
                "W": "Oeste (W)", "NE": "Noreste (NE)", "NW": "Noroeste (NW)", "SE": "Sureste (SE)",
                "SW": "Suroeste (SW)", "NNE": "Nor-noreste (NNE)", "NNW": "Nor-noroeste (NNW)",
                "ENE": "Este-noreste (ENE)", "ESE": "Este-sureste (ESE)", "SSE": "Sur-sureste (SSE)",
                "SSW": "Sur-suroeste (SSW)", "WNW": "Oeste-noroeste (WNW)", "WSW": "Oeste-suroeste (WSW)"}
DIA_NOCHE_TEXTO = {"Day": "Día", "Night": "Noche"}

# Ayudas de la parte de resultados (palabras claras en lugar de jerga).
AYUDA_RESULTADO = {
    "riesgo": "Probabilidad estimada de que este incidente tenga un **impacto crítico** en el tráfico (vía muy "
              "afectada, cierres o demoras largas). No mide la gravedad de las personas heridas.",
    "umbral": "Riesgo mínimo a partir del cual el sistema marca el incidente como crítico. Se eligió con datos de "
              "validación para detectar bastantes críticos sin generar demasiadas falsas alarmas. "
              "Puede probar otros valores en «Umbral y costo».",
    "decision": "«Alerta crítica» = el riesgo estimado llegó al umbral de alerta y conviene activar la respuesta prioritaria. «Sin alerta crítica» = quedó por debajo (puede estar en Normal o en Vigilancia).",
    "estimados": "Datos opcionales que no se informaron: el sistema los completó con valores típicos. "
                 "Mientras más haya, menos fiable es la estimación.",
    "zonas": "**Normal**: riesgo bajo. **Vigilancia**: riesgo intermedio, cerca del umbral (por debajo o por encima). "
             "**Crítico**: el riesgo superó el umbral.",
}

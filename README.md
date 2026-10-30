# Aplicación web — Sistema de apoyo a la decisión para incidentes viales críticos

Aplicación en **Streamlit** que se ejecuta **en local** (no hay que desplegarla) y es **autónoma**: lleva dentro de su
propia carpeta el modelo (`models/`) y el código del modelo (`src/accidentes/`), así que funciona sin el repositorio
`proyecto-accidentes`. No reimplementa nada: la predicción, el stacking, el umbral y la explicación SHAP salen de
`accidentes.inference.PredictorIncidentes`, el mismo código con el que se evaluó el modelo.

## Funcionalidades y la pregunta de investigación que responden

| # | Funcionalidad | Dónde | Responde |
|---|---|---|---|
| 1 | Formulario de reporte: solo el **estado** es obligatorio; el lugar se elige por ciudad, búsqueda, mapa o coordenadas; todos los campos tienen un «?» con ayuda | Analizar incidente | Núcleo (escenario tiempo real, PI 4) |
| 2 | Predicción: riesgo estimado, decisión y zona (Normal, Vigilancia ×2, Crítico) con su evidencia en test | Analizar incidente | Núcleo |
| 3 | Recomendación de gestión según la zona, con nota del factor que más empuja el riesgo | Analizar incidente | **PI 5** |
| 4 | Explicación SHAP del caso: por variable y por grupo, más «cómo se calculó» (stacking) | Analizar incidente | Explicabilidad |
| 5 | Explorador de patrones · clima y visibilidad | Explorador de patrones | **PI 1** |
| 6 | Explorador de patrones · patrones temporales (hora, día, mes, estación) | Explorador de patrones | **PI 2** |
| 7 | Explorador de patrones · infraestructura | Explorador de patrones | **PI 3** |
| 8 | Tiempo real vs información completa (resultados precalculados) | Tiempo real vs completa | **PI 4** |
| 9 | Control de umbral con su costo (curva precisión global/recall, por cada 1,000 incidentes) | Umbral y costo | Transparencia de la decisión |
| 10 | «Qué pasaría si»: variar un campo y ver cuánto cambia el riesgo | Analizar incidente | PI 1–3 a nivel de caso |
| 11 | Historial de consultas (se guarda en tu computador; se puede reabrir un caso) | Historial y exportación | — |
| 12 | Exportar resultados: un análisis (CSV, JSON, ficha HTML imprimible) y el historial (CSV) | Analizar / Historial | — |

Además, la página **Acerca del modelo** resume qué hace, sus resultados en test, las reglas de gestión, los límites y un
glosario en palabras sencillas. Pendiente por si sobra tiempo: carga por lote (CSV).

Las tasas del explorador son **asociaciones, no causas**, y cada variable se muestra junto con su puesto en la
importancia SHAP del modelo (la ubicación domina).

## Puesta en marcha (Windows)

### 1. Poner el modelo dentro de la app (una sola vez, y de nuevo cada vez que se reexporte el modelo)

En `proyecto-accidentes` ya debe haber corrido `python pipeline/06_exportar_para_app.py` (crea `models/`). Después,
desde la carpeta de esta app:

```
python sincronizar_modelo.py C:\ruta\a\proyecto-accidentes
```

(si las dos carpetas están una al lado de la otra, basta `python sincronizar_modelo.py`). El script **copia** y
**verifica** (SHA-256 contra el manifiesto), y compara las versiones de las librerías:

| Se copia desde `proyecto-accidentes` | A esta app |
|---|---|
| `models\tiempo_real\*` (modelos, preprocesador, apilador, umbral…) | `models\tiempo_real\` |
| `models\reportes\*` (tablas de los paneles, `ejemplos_app.json`) | `models\reportes\` |
| `models\manifest_tiempo_real.json` | `models\` |
| `src\accidentes\` (solo 8 módulos: `__init__`, `config`, `ensemble`, `explain`, `features`, `inference`, `models`, `preprocessing`) | `src\accidentes\` |

**A mano** también sirve: copie esas carpetas con esos mismos nombres. Los `.joblib` guardan referencias a las clases de
`src\accidentes`, por eso el código y los modelos deben ser **de la misma exportación**.
Un `.joblib` de más de 50 MB queda fuera de `models/` en el modelo (va en `outputs/exportacion/`): el script lo toma de ahí.
GitHub rechaza archivos de más de 100 MB; si algún modelo los pasa, use Git LFS.

### 2. Librerías

Si ya corres el pipeline con tu Python, **solo faltan `streamlit`, `plotly` y el mapa** (`iniciar_app.bat` los instala la
primera vez). Si empiezas desde cero, instala las dependencias **con las mismas versiones de scikit-learn, xgboost y
lightgbm** con las que se entrenó (sección `versiones` de `models/manifest_tiempo_real.json`; si no coinciden, los
`.joblib` pueden no cargar):

```
cd app-accidentes
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`python sincronizar_modelo.py --solo-verificar` compara las versiones instaladas con las del entrenamiento sin copiar nada.

### 3. Iniciar

Doble clic en `iniciar_app.bat`, o `python -m streamlit run app.py`. Se abre en <http://localhost:8501>.
Si falta el modelo o el código, la app lo dice con el comando exacto para arreglarlo.

## Cómo se indica el lugar del incidente (sin escribir latitud y longitud)

El modelo necesita coordenadas, pero **solo el estado es obligatorio**. En el paso 1 del formulario hay cuatro formas:

| Forma | Qué hace | ¿Internet? |
|---|---|---|
| 📍 **Ciudad** | Lista de las ciudades principales del estado (o «centro del estado») | no |
| 🔎 **Buscar** | Busca una dirección o lugar por nombre (OpenStreetMap/Nominatim) y también elige el estado | sí |
| 🗺️ **Mapa** | Se hace clic en el lugar; el mapa necesita `folium` y `streamlit-folium` | sí (para dibujar el mapa) |
| 🧭 **Coordenadas** | Acepta `40.4103, -79.6192`, `40.41°N 79.62°W` o el **enlace de Google Maps** del lugar | no |

Si no se indica ningún lugar se usa el **centro del estado** y la app lo avisa (tarjeta amarilla y aviso en el resultado):
la estimación es entonces más aproximada. Si el punto no cuadra con el estado elegido, la app avisa y sugiere el estado
correcto; si se cambia el estado, se quita un lugar que ya no corresponde. Las coordenadas de las ciudades y los
rectángulos de cada estado (`incidentes_app/lugares.py`) son aproximados: sirven para ubicar y para detectar
incoherencias, no son datos del modelo.

## Pensada para personas sin conocimientos técnicos

- Cada campo del formulario tiene un **«?»** que explica qué es, cómo escribirlo y qué hacer si no se sabe (textos en
  `incidentes_app/ayudas.py`, con equivalencias para °F, millas y pulgadas).
- Los resultados usan palabras claras (zona, riesgo, umbral de alerta, datos que faltaban); el detalle técnico (SHAP,
  logit, apilador) queda en pestañas aparte y en el glosario de «Acerca del modelo».
- El estilo visual (colores, tarjetas, barra de riesgo con las cuatro zonas) está en `incidentes_app/estilo.py` y
  `.streamlit/config.toml`.

## Probar cada zona con casos reales

`python eda/ejemplos_para_app.py` (en el repositorio del modelo) escribe `models/reportes/ejemplos_app.json` con
8 casos reales de validación: uno por zona (Normal, Vigilancia bajo el umbral, Vigilancia sobre el umbral, Crítico), separando
los que de verdad fueron críticos de los que no. Luego `python sincronizar_modelo.py` los copia a la app. En «Analizar
incidente» están en el desplegable «¿Quiere probar con un caso real?»; al analizarlos, la app dice si el modelo acertó,
dio una falsa alarma o perdió un crítico. Un caso aislado no mide el modelo; la evaluación completa está en test.

## Estructura

```
app.py                  navegación, estilo y barra lateral
sincronizar_modelo.py   copia y verifica el modelo y su código desde proyecto-accidentes (solo biblioteca estándar)
iniciar_app.bat         instala lo que falte e inicia la app
models/                 tiempo_real/ (modelos), reportes/ (tablas), manifest_tiempo_real.json  <- los llena el script
src/accidentes/         copia del código del modelo (8 módulos)  <- lo llena el script
paginas/                una página por pantalla (analizar, explorador, tiempo_real_vs_completa, umbral, historial, acerca)
incidentes_app/         formulario, lugares, ayudas, estilo, análisis de un caso, reglas, historial, exportación, gráficos
reglas/gestion_por_zona.json   acciones de gestión por zona y notas por factor (PI 5)
assets/logo.svg         logotipo de la barra lateral
tests/                  pruebas sin navegador (AppTest) y de los módulos de lugares
datos_locales/          historial.csv (se crea solo; no se versiona)
```

## Pruebas

```
pip install pytest
python -m pytest tests -q
```
Recorren cada página, la elección del lugar por ciudad / búsqueda (simulada) / mapa (simulado) / coordenadas, un caso con
ubicación aproximada, un caso crítico con umbral bajo, el «qué pasaría si» con todos los campos, el historial, las tres
exportaciones y que **cada campo tenga su «?»**. Usan una carpeta temporal, así que no tocan tu historial real. Las
pruebas del modelo se omiten si aún no se ha sincronizado `models/`.
(Para probar con otra carpeta que contenga `models/` y `src/`: `set INCIDENTES_REPO=C:\ruta`.)

## Notas
- Los datos y el historial **no salen del computador**. Solo dos funciones usan internet, y son opcionales: la búsqueda
  de direcciones (envía el texto buscado a OpenStreetMap) y el dibujo del mapa (descarga las teselas).
- Si regeneras los reportes con la app abierta, se refrescan solos en 5 minutos (o reinicia la app). Si cambias el
  modelo, vuelve a sincronizar y reinicia la app.
- Las cifras son de una evaluación histórica con datos de EE. UU.: orientativas, no una garantía.

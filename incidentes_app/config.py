"""
CONFIGURACION: donde estan el modelo, los reportes y los datos locales de la app.

La app es AUTONOMA: lleva dentro de su propia carpeta todo lo que necesita del modelo.

    app-accidentes/
    ├── src/accidentes/        codigo del modelo (copia de proyecto-accidentes/src/accidentes)
    └── models/
        ├── tiempo_real/       modelos, preprocesador, apilador, umbral (decision.json)
        ├── reportes/          tablas de los paneles (curva de umbral, patrones, ejemplos...)
        └── manifest_tiempo_real.json

`sincronizar_modelo.py` copia y verifica todo eso desde el repositorio del modelo.
La app NO entrena ni reimplementa nada: usa `accidentes.inference.PredictorIncidentes`.

Para probar con otra carpeta (por ejemplo, el propio repositorio del modelo) se puede definir la
variable de entorno INCIDENTES_REPO con la ruta de una carpeta que contenga `models/` (y, si
quiere usar su codigo, `src/`). Sin esa variable se usa siempre la carpeta de la app.
"""

import os
import sys
from importlib import metadata
from pathlib import Path

RAIZ_APP = Path(__file__).resolve().parents[1]
ESCENARIO = "tiempo_real"                       # el escenario que opera la app (informacion al reportar)
ARCHIVO_REGLAS = RAIZ_APP / "reglas" / "gestion_por_zona.json"
MODULOS_DEL_MODELO = ["__init__", "config", "ensemble", "explain", "features", "inference", "models", "preprocessing"]


def dir_datos_locales():
    """Carpeta donde la app guarda el historial. INCIDENTES_DATOS permite cambiarla (pruebas)."""
    ruta = Path(os.environ.get("INCIDENTES_DATOS", RAIZ_APP / "datos_locales"))
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def raiz_del_modelo():
    """Carpeta que contiene models/ (y src/): la de la app, o INCIDENTES_REPO si se definio."""
    if os.environ.get("INCIDENTES_REPO"):
        return Path(os.environ["INCIDENTES_REPO"]).resolve()
    return RAIZ_APP


def dir_modelos():
    return raiz_del_modelo() / "models"


def dir_codigo():
    """Carpeta `src` con el paquete `accidentes`: la de la raiz del modelo y, si no tiene, la de la app."""
    for base in (raiz_del_modelo(), RAIZ_APP):
        if (base / "src" / "accidentes" / "inference.py").exists():
            return base / "src"
    return None


def problemas_de_instalacion():
    """Lista de textos con lo que falta para que la app funcione (vacia si todo esta en su sitio)."""
    problemas = []
    if dir_codigo() is None:
        problemas.append("Falta el código del modelo: la carpeta `src/accidentes/` dentro de la app.")
    modelos = dir_modelos() / ESCENARIO
    if not (modelos / "decision.json").exists():
        problemas.append(f"Faltan los archivos del modelo en `{modelos}`.")
    return problemas


def aviso_de_instalacion():
    """Texto con lo que debe hacer el usuario cuando falta algo (o None si esta completo)."""
    problemas = problemas_de_instalacion()
    if not problemas:
        return None
    return (
        "**La app todavía no tiene el modelo dentro de su carpeta.**\n\n"
        + "\n".join(f"- {p}" for p in problemas)
        + "\n\nSe soluciona con un solo comando, desde la carpeta de la app "
        "(la ruta es la carpeta `proyecto-accidentes`, donde ya corrió `pipeline/06_exportar_para_app.py`):\n\n"
        "```\npython sincronizar_modelo.py C:\\ruta\\a\\proyecto-accidentes\n```\n\n"
        "O copie a mano `proyecto-accidentes\\models` → `app-accidentes\\models` y "
        "`proyecto-accidentes\\src\\accidentes` → `app-accidentes\\src\\accidentes`. "
        "Después reinicie la app."
    )


def preparar_importacion():
    """Hace importable el paquete `accidentes` de la app (su copia local va PRIMERO en el path).

    Asi la app usa su propia copia del codigo aunque en el computador este instalado el paquete
    del otro repositorio. `origen_del_codigo()` dice cual se esta usando de verdad.
    """
    codigo = dir_codigo()
    if codigo is not None and str(codigo) not in sys.path:
        sys.path.insert(0, str(codigo))


def origen_del_codigo():
    """Ruta real del paquete `accidentes` que se esta usando (para mostrarla en «Acerca»)."""
    try:
        import accidentes
        return Path(accidentes.__file__).resolve().parent
    except ImportError:
        return None


# Librerias cuya version importa para que los .joblib carguen igual que al exportar.
LIBRERIAS_CLAVE = ["scikit-learn", "xgboost", "lightgbm", "numpy", "pandas", "joblib", "shap"]
LIBRERIAS_CRITICAS = ["scikit-learn", "xgboost", "lightgbm"]       # si difieren, el modelo puede no cargar


def comparar_versiones(manifiesto):
    """Compara las versiones con las que se exporto el modelo y las instaladas.

    Devuelve una lista de dicts: libreria, exportado, instalado, coincide, critica.
    """
    exportadas = (manifiesto or {}).get("versiones", {})
    filas = []
    for lib in LIBRERIAS_CLAVE:
        try:
            instalada = metadata.version(lib)
        except metadata.PackageNotFoundError:
            instalada = "no instalada"
        exportada = exportadas.get(lib, "—")
        filas.append({"libreria": lib, "exportado": exportada, "instalado": instalada,
                      "coincide": exportada == "—" or exportada == instalada,
                      "critica": lib in LIBRERIAS_CRITICAS})
    return filas

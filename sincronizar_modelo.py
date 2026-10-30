"""
SINCRONIZAR EL MODELO: copia a esta app lo que necesita del repositorio del modelo.
=============================================================================
Hace que la app funcione SOLA, sin depender de la carpeta `proyecto-accidentes`
(esa carpeta solo hace falta cuando se vuelve a entrenar el modelo).

Copia, desde el repositorio del modelo:
  models/tiempo_real/*            -> app/models/tiempo_real/    (modelos, preprocesador, umbral)
  models/reportes/*               -> app/models/reportes/       (tablas de los paneles y casos de ejemplo)
  models/manifest_tiempo_real.json-> app/models/
  src/accidentes/<8 modulos>      -> app/src/accidentes/        (el codigo que cargan los .joblib)

Si algun .joblib pesa demasiado para GitHub y quedo fuera de models/, lo toma de
outputs/exportacion/tiempo_real/ (el paquete completo que deja el script 06).

Despues VERIFICA: que cada archivo copiado sea identico (SHA-256) al original y al del
manifiesto, y compara las versiones de las librerias instaladas con las del entrenamiento.

Uso (desde la carpeta de la app; no necesita instalar nada):
    python sincronizar_modelo.py C:\\ruta\\a\\proyecto-accidentes
    python sincronizar_modelo.py                 # busca ..\\proyecto-accidentes
    python sincronizar_modelo.py RUTA --solo-verificar     # no copia; solo comprueba lo que ya hay

Repitalo cada vez que vuelva a ejecutar pipeline/06_exportar_para_app.py (y reinicie la app).
=============================================================================
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

RAIZ_APP = Path(__file__).resolve().parent
ESCENARIO = "tiempo_real"
MODULOS = ["__init__", "config", "ensemble", "explain", "features", "inference", "models", "preprocessing"]
LIBRERIAS = ["scikit-learn", "xgboost", "lightgbm", "numpy", "pandas", "joblib", "shap"]
CRITICAS = {"scikit-learn", "xgboost", "lightgbm"}
LIMITE_GITHUB_MB = 100


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def fallar(texto):
    print(f"\nERROR: {texto}")
    sys.exit(1)


def ubicar_origen(argumento):
    candidatos = [Path(argumento)] if argumento else [RAIZ_APP.parent / "proyecto-accidentes"]
    for c in candidatos:
        if (c / "models" / ESCENARIO / "decision.json").exists() and (c / "src" / "accidentes" / "inference.py").exists():
            return c.resolve()
    if argumento:
        c = Path(argumento)
        if not c.exists():
            fallar(f"No existe la carpeta {c}")
        if not (c / "models" / ESCENARIO / "decision.json").exists():
            fallar(f"En {c} no esta models/{ESCENARIO}/decision.json. Ejecute alli: python pipeline/06_exportar_para_app.py")
        fallar(f"En {c} no esta src/accidentes/inference.py: no parece la carpeta del repositorio del modelo.")
    fallar("No encuentro el repositorio del modelo al lado de esta carpeta.\n"
           "Indique su ruta:  python sincronizar_modelo.py C:\\ruta\\a\\proyecto-accidentes")


def copiar(origen, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)


def main():
    ap = argparse.ArgumentParser(description="Copia el modelo y su codigo del repositorio del modelo a esta app.")
    ap.add_argument("repositorio", nargs="?", help="ruta de la carpeta proyecto-accidentes (por defecto ..\\proyecto-accidentes)")
    ap.add_argument("--solo-verificar", action="store_true", help="no copia nada; comprueba lo que ya hay en la app")
    args = ap.parse_args()

    origen = ubicar_origen(args.repositorio) if not args.solo_verificar else None
    destino_modelos = RAIZ_APP / "models"
    destino_tr = destino_modelos / ESCENARIO
    destino_codigo = RAIZ_APP / "src" / "accidentes"

    print("=" * 70)
    print("SINCRONIZAR EL MODELO CON LA APP")
    print("=" * 70)
    manifiesto_destino = destino_modelos / f"manifest_{ESCENARIO}.json"

    if origen:
        print(f"Origen : {origen}")
        print(f"Destino: {RAIZ_APP}\n")
        with open(origen / "models" / f"manifest_{ESCENARIO}.json", encoding="utf-8") as f:
            manifiesto = json.load(f)
        faltan = []

        print("[1] Modelos (models/tiempo_real)")
        pesados = []
        for ficha in manifiesto["archivos"]:
            nombre = ficha["archivo"]
            if nombre == manifiesto_destino.name:
                continue
            fuente = origen / "models" / ESCENARIO / nombre
            if not fuente.exists():
                fuente = origen / "outputs" / "exportacion" / ESCENARIO / nombre     # paquete completo (archivos pesados)
            if not fuente.exists():
                faltan.append(nombre)
                continue
            copiar(fuente, destino_tr / nombre)
            mb = fuente.stat().st_size / 1024 ** 2
            if mb > LIMITE_GITHUB_MB:
                pesados.append((nombre, mb))
            print(f"    {nombre:<36} {mb:8.2f} MB")
        if faltan:
            fallar("Faltan estos archivos del modelo, ni en models/ ni en outputs/exportacion/:\n    "
                   + "\n    ".join(faltan) + "\nVuelva a ejecutar pipeline/06_exportar_para_app.py en el repositorio del modelo.")

        print("\n[2] Tablas de los paneles (models/reportes)")
        n = 0
        carpeta_rep = origen / "models" / "reportes"
        for ruta in sorted(carpeta_rep.glob("*")) if carpeta_rep.exists() else []:
            if ruta.is_file():
                copiar(ruta, destino_modelos / "reportes" / ruta.name)
                n += 1
        print(f"    {n} archivos")
        if not (destino_modelos / "reportes" / "ejemplos_app.json").exists():
            print("    (no hay ejemplos_app.json: para tener casos de prueba, ejecute en el repositorio del modelo "
                  "`python eda/ejemplos_para_app.py` y repita esta sincronizacion)")

        copiar(origen / "models" / f"manifest_{ESCENARIO}.json", manifiesto_destino)

        print("\n[3] Codigo del modelo (src/accidentes)")
        for m in MODULOS:
            copiar(origen / "src" / "accidentes" / f"{m}.py", destino_codigo / f"{m}.py")
            print(f"    {m}.py")
        # Si quedo una copia antigua de otro modulo, no estorba, pero se avisa de lo que sobra.
        sobrantes = sorted(p.name for p in destino_codigo.glob("*.py") if p.stem not in MODULOS)
        if sobrantes:
            print(f"    (sobran en la app, no se usan: {', '.join(sobrantes)})")
    else:
        if not manifiesto_destino.exists():
            fallar("No hay models/manifest_tiempo_real.json en la app: todavia no se ha sincronizado.")
        with open(manifiesto_destino, encoding="utf-8") as f:
            manifiesto = json.load(f)
        pesados = []

    print("\n[4] Verificacion")
    errores = []
    for ficha in manifiesto["archivos"]:
        nombre = ficha["archivo"]
        ruta = destino_tr / nombre
        if not ruta.exists():
            errores.append(f"falta {nombre}")
        elif sha256(ruta) != ficha["sha256"]:
            errores.append(f"{nombre} no coincide con el manifiesto (copia dañada o de otra exportacion)")
    if origen:
        for m in MODULOS:
            if sha256(origen / "src" / "accidentes" / f"{m}.py") != sha256(destino_codigo / f"{m}.py"):
                errores.append(f"src/accidentes/{m}.py no es identico al original")
    for m in MODULOS:
        if not (destino_codigo / f"{m}.py").exists():
            errores.append(f"falta src/accidentes/{m}.py")
    if errores:
        print("    PROBLEMAS:\n      - " + "\n      - ".join(errores))
        sys.exit(1)
    print(f"    {len(manifiesto['archivos'])} archivos del modelo = manifiesto (SHA-256 correcto)")
    if origen:
        print(f"    {len(MODULOS)} modulos de codigo identicos al repositorio del modelo")

    print("\n[5] Librerias: versiones del entrenamiento vs instaladas en este Python")
    exportadas = manifiesto.get("versiones", {})
    hay_critica = False
    for lib in LIBRERIAS:
        try:
            inst = metadata.version(lib)
        except metadata.PackageNotFoundError:
            inst = "NO INSTALADA"
        exp = exportadas.get(lib, "?")
        igual = inst == exp
        marca = "ok " if igual else ("!! " if lib in CRITICAS else "~  ")
        hay_critica |= (not igual and lib in CRITICAS)
        print(f"    {marca}{lib:<14} entrenamiento {exp:<10} instalada {inst}")
    if hay_critica:
        print("\n    ATENCION: scikit-learn, xgboost y lightgbm deben ser EXACTAMENTE las del entrenamiento o el modelo\n"
              "    puede no cargar (o predecir distinto). Instale esas versiones, por ejemplo:")
        pedido = " ".join(f"{lib}=={exportadas[lib]}" for lib in sorted(CRITICAS) if lib in exportadas)
        print(f"        python -m pip install {pedido}")

    if origen:
        constancia = {
            "sincronizado": datetime.now().isoformat(timespec="seconds"),
            "origen": str(origen),
            "exportado_el": manifiesto.get("creado"),
            "archivos_modelo": len(manifiesto["archivos"]),
            "modulos_codigo": MODULOS,
        }
        with open(destino_modelos / "sincronizado.json", "w", encoding="utf-8") as f:
            json.dump(constancia, f, indent=2, ensure_ascii=False)

    if pesados:
        print("\nAVISO: estos archivos pesan mas de 100 MB y GitHub no los acepta en un commit normal:")
        for nombre, mb in pesados:
            print(f"    {nombre}  ({mb:.0f} MB)  -> use Git LFS o no suba esa carpeta")
    print("\nListo. Inicie la app con iniciar_app.bat (o: python -m streamlit run app.py).")
    print("La app ya no necesita la carpeta proyecto-accidentes para funcionar.")


if __name__ == "__main__":
    main()

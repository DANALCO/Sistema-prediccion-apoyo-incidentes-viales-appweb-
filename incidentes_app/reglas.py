"""
MOTOR DE REGLAS (pregunta de investigacion 5): de la zona predicha a la accion de gestion.

La regla es sistematica y transparente: la zona fija las acciones (reglas/gestion_por_zona.json); en
Vigilancia y Critico se anade una nota segun el grupo de variables que mas empuja el riesgo de ESE caso
(aporte SHAP neto positivo mayor). Las acciones son reglas de diseno; la evidencia de cada zona sale de los
datos (porcentaje de criticos en test, tabla zonas_vigilancia).
"""

import json
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def cargar_reglas():
    with open(config.ARCHIVO_REGLAS, encoding="utf-8") as f:
        return json.load(f)


def grupo_dominante(aportes_por_grupo):
    """Grupo con mayor aporte neto POSITIVO (hacia critico) o None si ninguno empuja hacia critico."""
    if not aportes_por_grupo:
        return None
    grupo, valor = max(aportes_por_grupo.items(), key=lambda kv: kv[1])
    return grupo if valor > 0 else None


def recomendar(nivel, grupo=None, campos_estimados=0):
    """Devuelve {zona, titulo, prioridad, acciones, nota_factor, nota_datos, aviso}."""
    reglas = cargar_reglas()
    zona = reglas["zonas"][nivel]
    nota_factor = reglas["factores"].get(grupo) if nivel != "Normal" and grupo else None
    n = int(campos_estimados)
    nota_datos = None if n == 0 else (reglas["campo_estimado"] if n == 1 else reglas["campos_estimados"].format(n=n))
    return {"zona": nivel, "titulo": zona["titulo"], "prioridad": zona["prioridad"],
            "acciones": list(zona["acciones"]), "nota_factor": nota_factor,
            "nota_datos": nota_datos, "aviso": reglas["aviso"]}


def tabla_de_reglas():
    """Todas las reglas en filas (para mostrar la tabla completa y para el informe)."""
    reglas = cargar_reglas()
    return [{"Zona": z, "Titulo": r["titulo"], "Prioridad": r["prioridad"], "Acciones": r["acciones"]}
            for z, r in reglas["zonas"].items()]

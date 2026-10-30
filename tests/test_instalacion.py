"""Pruebas de que la app es autonoma y explica que hacer cuando le falta el modelo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]


def test_sin_modelo_la_app_explica_como_copiarlo(tmp_path, monkeypatch):
    monkeypatch.setenv("INCIDENTES_REPO", str(tmp_path))            # una carpeta vacia: sin models/
    monkeypatch.setenv("INCIDENTES_DATOS", str(tmp_path / "datos"))
    for pagina in ("analizar.py", "umbral.py", "acerca.py"):
        at = AppTest.from_file(str(RAIZ / "paginas" / pagina), default_timeout=60)
        at.run()
        assert not at.exception, (pagina, [e.value for e in at.exception])
        assert any("sincronizar_modelo.py" in e.value for e in at.error), pagina


def test_el_codigo_del_modelo_sale_de_la_propia_app(monkeypatch):
    from incidentes_app import config
    monkeypatch.delenv("INCIDENTES_REPO", raising=False)
    assert config.dir_codigo() == RAIZ / "src"
    assert config.dir_modelos() == RAIZ / "models"
    assert {p.stem for p in (RAIZ / "src" / "accidentes").glob("*.py")} == set(config.MODULOS_DEL_MODELO)


def test_comparar_versiones_marca_las_distintas():
    from incidentes_app import config
    filas = config.comparar_versiones({"versiones": {"scikit-learn": "0.0.1", "numpy": "no existe"}})
    por_lib = {f["libreria"]: f for f in filas}
    assert not por_lib["scikit-learn"]["coincide"] and por_lib["scikit-learn"]["critica"]
    assert por_lib["xgboost"]["coincide"]                                # sin dato exportado: no se alarma

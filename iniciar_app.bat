@echo off
rem Inicia la aplicacion web en local (doble clic o desde la consola).
rem La app es autonoma: el modelo esta en la carpeta "models" y su codigo en "src" (los copia sincronizar_modelo.py).
cd /d "%~dp0"

if not exist "models\tiempo_real\decision.json" goto sin_modelo
if not exist "src\accidentes\inference.py" goto sin_modelo

echo [1/3] Comprobando streamlit y plotly...
python -c "import streamlit, plotly" >nul 2>&1
if errorlevel 1 goto instalar
goto revisar

:instalar
echo Faltan streamlit y plotly en este Python. Instalandolos (solo la primera vez)...
python -m pip install "streamlit>=1.40" "plotly>=5.20"
if errorlevel 1 goto fallo_pip
goto revisar

:revisar
echo [2/3] Comprobando las librerias del modelo (shap, xgboost, lightgbm...). Puede tardar hasta 1 o 2 minutos; espere, no esta colgado.
python -c "import pandas, sklearn, xgboost, lightgbm, shap, joblib" >nul 2>&1
if errorlevel 1 goto faltan_modelo
goto mapa

:mapa
echo [3/3] Comprobando el paquete del mapa...
python -c "import folium, streamlit_folium" >nul 2>&1
if errorlevel 1 goto instalar_mapa
goto iniciar

:instalar_mapa
echo Instalando el paquete del mapa (solo la primera vez; si falla, la app funciona igual sin el mapa)...
python -m pip install folium streamlit-folium
goto iniciar

:sin_modelo
echo.
echo La app todavia no tiene el modelo dentro de su carpeta.
echo Copielo con UN comando (la ruta es la carpeta proyecto-accidentes, donde ya corrio el script 06):
echo.
echo     python sincronizar_modelo.py C:\ruta\a\proyecto-accidentes
echo.
echo (o copie a mano proyecto-accidentes\models a app-accidentes\models y proyecto-accidentes\src\accidentes a app-accidentes\src\accidentes)
echo.
pause
exit /b 1

:faltan_modelo
echo.
echo Faltan librerias del modelo en este Python. Instalelas con:
echo     python -m pip install -r requirements.txt
echo y use las MISMAS versiones del entrenamiento de scikit-learn, xgboost y lightgbm
echo (la lista aparece en models\manifest_tiempo_real.json, seccion "versiones", o al ejecutar
echo  python sincronizar_modelo.py --solo-verificar).
echo.
pause
exit /b 1

:fallo_pip
echo.
echo No se pudo instalar. Revise la conexion a internet o ejecute a mano:
echo     python -m pip install streamlit plotly
echo.
pause
exit /b 1

:iniciar
echo.
echo Iniciando la aplicacion. Se abrira el navegador (normalmente en http://localhost:8501; si ese puerto esta ocupado, use la direccion "Local URL" que aparece mas abajo).
echo Deje esta ventana abierta mientras usa la app; para cerrarla, pulse Ctrl+C o cierre ESTA ventana (cerrar solo la pestana del navegador no detiene la app).
echo.
python -m streamlit run app.py
pause

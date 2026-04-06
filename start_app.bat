@echo off
REM Inicia la app Streamlit desde la carpeta del script.
REM Asegúrate de tener Python y Streamlit instalados en tu entorno.
cd /d "%~dp0"

REM Opcional: activar venv si usas uno (descomenta y ajusta la ruta)
REM call "venv\Scripts\activate"

streamlit run main.py

pause

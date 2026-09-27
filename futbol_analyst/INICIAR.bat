@echo off
title Analista de Futbol
color 0B
cd /d "%~dp0"

echo ==================================================
echo    ANALISTA DE FUTBOL - INICIANDO
echo ==================================================
echo.

REM Verificar que Python está instalado
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en el PATH.
    echo Descárgalo desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar que Flask está instalado
py -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Flask no está instalado. Instalando...
    pip install flask
    echo.
)

echo [OK] Arrancando servidor...
echo.
py app.py

pause
@echo off
setlocal

cd /d "%~dp0.."

if not exist "venv\Scripts\python.exe" (
    echo ERRO: ambiente virtual nao encontrado em "%CD%\venv".
    exit /b 1
)

"venv\Scripts\python.exe" -m flask --app app backup-db
exit /b %ERRORLEVEL%

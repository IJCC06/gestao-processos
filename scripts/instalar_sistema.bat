@echo off
setlocal
title Instalador - Gestao de Processos

cd /d "%~dp0.."
set "PROJECT_DIR=%CD%"

echo.
echo ==========================================
echo   Gestao de Processos - Instalacao
echo ==========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERRO: Python nao foi encontrado.
        echo.
        echo Instale o Python 3 e execute este instalador novamente.
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
) else (
    set "PYTHON_CMD=py -3"
)

if not exist "venv\Scripts\python.exe" (
    echo [1/5] Criando ambiente virtual...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 goto :erro
) else (
    echo [1/5] Ambiente virtual ja existe.
)

echo [2/5] Instalando dependencias...
"venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :erro

"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :erro

echo [3/5] Configurando o sistema...
"venv\Scripts\python.exe" "scripts\configurar_instalacao.py"
if errorlevel 1 goto :erro

echo [4/5] Atualizando o banco de dados...
"venv\Scripts\python.exe" -m flask --app app db upgrade
if errorlevel 1 goto :erro

echo [5/5] Criando atalho na Area de Trabalho...
cscript //nologo "scripts\criar_atalho_desktop.vbs"
if errorlevel 1 goto :erro

echo.
echo ==========================================
echo   Instalacao concluida com sucesso!
echo ==========================================
echo.
echo Use o atalho "Gestao de Processos" na Area de Trabalho.
echo.
pause
exit /b 0

:erro
echo.
echo ==========================================
echo   A instalacao nao foi concluida.
echo ==========================================
echo.
echo Verifique a mensagem de erro acima e tente novamente.
echo.
pause
exit /b 1

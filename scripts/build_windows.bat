@echo off
setlocal
title Build - Gestao de Processos

cd /d "%~dp0.."

if not exist "venv\Scripts\python.exe" (
    echo ERRO: ambiente virtual de desenvolvimento nao encontrado.
    echo Execute: python -m venv venv
    exit /b 1
)

echo [1/3] Instalando ferramentas de build...
"venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto :erro

echo [2/3] Gerando executavel...

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
"venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm GestaoProcessos.spec
if errorlevel 1 goto :erro

if not exist "dist\GestaoProcessos\GestaoProcessos.exe" (
    echo ERRO: executavel nao foi gerado.
    echo Verifique a pasta dist\GestaoProcessos.
    goto :erro
)

echo [3/3] Gerando instalador...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo ERRO: Inno Setup 6 nao foi encontrado.
    echo Instale o Inno Setup 6 para gerar o Setup.exe.
    goto :erro
)

"%ISCC%" "installer\GestaoProcessos.iss"
if errorlevel 1 goto :erro

echo.
echo Build concluido.
echo Instalador: installer_output\GestaoProcessos-Setup.exe
exit /b 0

:erro
echo.
echo BUILD FALHOU.
exit /b 1

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

rem Procura primeiro no PATH.
for /f "delims=" %%I in ('where iscc.exe 2^>nul') do goto :found_iscc_path

rem Caminhos padrao sem usar blocos IF que confundem o CMD com "(x86)".
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" goto :found_iscc_pf86
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" goto :found_iscc_pf
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" goto :found_iscc_local_programs
if exist "%LOCALAPPDATA%\Inno Setup 6\ISCC.exe" goto :found_iscc_local

goto :inno_not_found

:found_iscc_path
for /f "delims=" %%I in ('where iscc.exe 2^>nul') do set "ISCC=%%I"
goto :compile_inno

:found_iscc_pf86
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
goto :compile_inno

:found_iscc_pf
set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
goto :compile_inno

:found_iscc_local_programs
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
goto :compile_inno

:found_iscc_local
set "ISCC=%LOCALAPPDATA%\Inno Setup 6\ISCC.exe"
goto :compile_inno

:inno_not_found
echo ERRO: Inno Setup 6 nao foi encontrado.
echo.
echo Instale o Inno Setup 6 ou informe manualmente o caminho do ISCC.exe:
echo   set ISCC=C:\caminho\para\ISCC.exe
echo   scripts\build_windows.bat
goto :erro

:compile_inno
echo Inno Setup encontrado em:
echo %ISCC%
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

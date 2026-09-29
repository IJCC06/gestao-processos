@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
for %%I in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~fI"
set "BACKUP_SCRIPT=%PROJECT_DIR%\scripts\backup_db.bat"
set "TASK_NAME=GestaoProcessos - Backup diario"

if not exist "%BACKUP_SCRIPT%" (
    echo ERRO: script de backup nao encontrado.
    exit /b 1
)

schtasks /Create /TN "%TASK_NAME%" /TR "\"%BACKUP_SCRIPT%"\"" /SC DAILY /ST 02:00 /F

if errorlevel 1 (
    echo ERRO: nao foi possivel criar a tarefa agendada.
    exit /b 1
)

echo.
echo Backup automatico configurado com sucesso.
echo Tarefa: %TASK_NAME%
echo Horario: todos os dias as 02:00.
echo.
echo Para executar agora: "%BACKUP_SCRIPT%"
echo Para remover a tarefa: schtasks /Delete /TN "%TASK_NAME%" /F

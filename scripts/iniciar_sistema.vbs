Option Explicit

Dim shell, fso, projectDir, pythonw, scriptPath, command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
pythonw = projectDir & "\venv\Scripts\pythonw.exe"
scriptPath = projectDir & "\scripts\iniciar_sistema.pyw"

If Not fso.FileExists(pythonw) Then
    pythonw = projectDir & "\.venv\Scripts\pythonw.exe"
End If

If Not fso.FileExists(pythonw) Then
    MsgBox "Nao foi encontrado o ambiente virtual do sistema." & vbCrLf & _
           "Verifique se a instalacao foi concluida corretamente.", _
           vbCritical, "Gestao de Processos"
    WScript.Quit 1
End If

command = """" & pythonw & """ """ & scriptPath & """"
shell.Run command, 0, False

Set shell = Nothing
Set fso = Nothing

Option Explicit

Dim shell, fso, projectDir, launcher, desktop, shortcut

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
launcher = projectDir & "\scripts\iniciar_sistema.vbs"
desktop = shell.SpecialFolders("Desktop")

If Not fso.FileExists(launcher) Then
    MsgBox "O inicializador do sistema nao foi encontrado.", _
           vbCritical, "Gestao de Processos"
    WScript.Quit 1
End If

Set shortcut = shell.CreateShortcut(desktop & "\Gestao de Processos.lnk")
shortcut.TargetPath = launcher
shortcut.WorkingDirectory = projectDir
shortcut.Description = "Abrir o Sistema de Gestao de Processos"
shortcut.IconLocation = "%SystemRoot%\System32\shell32.dll,21"
shortcut.Save

MsgBox "Atalho criado na Area de Trabalho." & vbCrLf & vbCrLf & _
       "Agora basta clicar em 'Gestao de Processos' para abrir o sistema.", _
       vbInformation, "Gestao de Processos"

Set shortcut = Nothing
Set shell = Nothing
Set fso = Nothing

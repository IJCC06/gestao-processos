[Setup]
AppId={{B9B2C1B0-9B9B-4E6D-9E15-7F7C6B4A2D11}
AppName=Gestão de Processos
AppVersion=1.0.0
AppPublisher=Gestão de Processos
DefaultDirName={autopf}\GestaoProcessos
DefaultGroupName=Gestão de Processos
OutputDir=..\installer_output
OutputBaseFilename=GestaoProcessos-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=Gestão de Processos

[Files]
Source: "..\dist\GestaoProcessos\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autodesktop}\Gestão de Processos"; Filename: "{app}\GestaoProcessos.exe"; WorkingDir: "{app}"
Name: "{group}\Gestão de Processos"; Filename: "{app}\GestaoProcessos.exe"; WorkingDir: "{app}"

[Run]
Filename: "{app}\GestaoProcessos.exe"; Description: "Iniciar Gestão de Processos"; Flags: nowait postinstall skipifsilent

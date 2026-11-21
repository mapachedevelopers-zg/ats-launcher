; Script de Inno Setup para Launcher de Chasis
; Compatible con Inno Setup 6.x

#define MyAppName "Launcher de Chasis"
#define MyAppVersion "2.2.1"
#define MyAppPublisher "Mapache Developers"
#define MyAppURL "https://github.com/mapachedevelopers-zg/ats-launcher"
#define MyAppExeName "Launcher_Chasis.exe"
#define SourceDir "dist\Launcher_Chasis"

[Setup]
AppId={{D37E84B1-65A2-4FA3-94D1-5AC5F6D0778B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
OutputDir=dist\installer
OutputBaseFilename=Launcher_Chasis_Setup_2.2.1
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Cierre automatico si el launcher esta en ejecucion durante instalacion o actualizacion
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Ejecutable principal
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Archivo de configuracion: se preserva si el usuario ya lo tenia configurado
Source: "{#SourceDir}\config_launcher.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
; Dependencias internas (PySide6, DLLs, etc.)
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Icono para la app
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Script de Inno Setup para ATS VIP
; Compatible con Inno Setup 6.x

#define MyAppName "ATS VIP"
#define MyAppVersion "2.3.2"
#define MyAppPublisher "CheoYT"
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
UsePreviousAppDir=yes
DirExistsWarning=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist\installer
OutputBaseFilename=ATS_VIP_Setup_2.3.2
SetupIconFile=logo.ico
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes

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
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Ejecutable principal
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Archivo de configuracion: se preserva si el usuario ya lo tenia configurado
Source: "{#SourceDir}\config_launcher.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
; Dependencias internas (PySide6, DLLs, etc.)
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Icono para la app
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; Limpiar dependencias y residuos de versiones anteriores antes de instalar
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\Launcher_Xtrink.exe"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  Params: String;
  TargetDir: String;
  TestFile: String;
  NeedsAdmin: Boolean;
begin
  Result := True;
  
  // Si ya tenemos permisos de administrador, procedemos directamente
  if IsAdmin then
    Exit;

  // Evitar bucle infinito si ya se intentó elevar
  Params := GetCmdTail;
  if Pos('/ELEVATED', UpperCase(Params)) > 0 then
    Exit;

  // Determinar el directorio de destino
  TargetDir := ExpandConstant('{param:DIR}');
  if TargetDir = '' then
    TargetDir := ExpandConstant('{autopf}\{#MyAppName}');

  // Comprobar si la carpeta requiere privilegios de administrador para escribir
  NeedsAdmin := False;
  TestFile := AddBackslash(TargetDir) + '.perm_test.tmp';
  if not ForceDirectories(TargetDir) or not SaveStringToFile(TestFile, '1', False) then
    NeedsAdmin := True
  else
    DeleteFile(TestFile);

  // Si requiere administrador, solicitar elevación mediante UAC y esperar
  if NeedsAdmin then
  begin
    Params := Params + ' /ELEVATED';
    if ShellExec('runas', ExpandConstant('{srcexe}'), Params, '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode) then
    begin
      // El instalador elevado completó la instalación; salimos limpiamente
      Result := False;
      Exit;
    end
    else
    begin
      // El usuario canceló la elevación UAC
      Result := False;
      Exit;
    end;
  end;
end;

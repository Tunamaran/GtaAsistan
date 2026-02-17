[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=GTA Asistan
AppVersion=17022026.01
AppPublisher=GTA Asistan
DefaultDirName={autopf}\GTA Asistan
DefaultGroupName=GTA Asistan
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=GtaAsistan_Setup_v17022026.01
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\launcher.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardImageFile=compiler:WizClassicImage-IS.bmp
WizardSmallImageFile=compiler:WizClassicSmallImage-IS.bmp

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "installwinrt"; Description: "Windows OCR dil paketi kur (Internet gerekli)"

[Files]
Source: "dist\GtaAsistan\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "gta_tum_araclar.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\GTA Asistan"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\GTA Asistan"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -Command ""Add-WindowsCapability -Online -Name 'Language.OCR~~~en-US~0.0.1.0'"""; StatusMsg: "Windows OCR dil paketi kuruluyor..."; Flags: runhidden waituntilterminated; Tasks: installwinrt
Filename: "{app}\launcher.exe"; Description: "GTA Asistan Baslat"; Flags: nowait postinstall skipifsilent shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}\__pycache__"
Type: dirifempty; Name: "{app}"


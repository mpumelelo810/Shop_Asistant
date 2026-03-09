[Setup]
AppName=Shop Assistant Pro
AppVersion=1.0
DefaultDirName={pf}\ShopAssistantPro
DefaultGroupName=Shop Assistant Pro
OutputDir=installer
OutputBaseFilename=ShopAssistantProSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\shop_audit_system.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Shop Assistant Pro"; Filename: "{app}\shop_audit_system.exe"
Name: "{autodesktop}\Shop Assistant Pro"; Filename: "{app}\shop_audit_system.exe"

[Run]
Filename: "{app}\shop_audit_system.exe"; Description: "Launch Shop Assistant Pro"; Flags: nowait postinstall skipifsilent
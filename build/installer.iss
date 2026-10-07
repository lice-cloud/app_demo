; ─────────────────────────────────────────────────────────────
; app_demo Windows 安装程序（Inno Setup 6）
;
; 编译（需先执行 PyInstaller 生成 dist/app_demo）：
;   iscc /DMyAppVersion=0.1.0 build\installer.iss
;
; 特性：
;   - 安装向导可选择安装位置（DefaultDirName 只是默认值，用户可修改）
;   - PrivilegesRequiredOverridesAllowed=dialog 允许用户在
;     「仅为我安装(免管理员)」与「为所有用户安装(需管理员)」之间选择，
;     默认目录随权限模式自动变化（{autopf}）
;   - 免管理员模式默认安装到 %LOCALAPPDATA%\Programs\app_demo，
;     自动更新无需提权
; ─────────────────────────────────────────────────────────────

#define MyAppName "app_demo"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "lice-cloud"
#define MyAppExeName "app_demo.exe"

[Setup]
; AppId 用于标识同一应用，升级/卸载时保持不变（请勿随意更改）
AppId={{1BCF2B5F-415B-441D-B3C6-00EAB7A11952}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; 允许用户选择安装权限模式（决定默认目录与是否需要管理员）
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; 安装前检测并关闭正在运行的应用
CloseApplications=yes
RestartApplications=no
OutputDir=..\dist\installer
OutputBaseFilename=app_demo-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
; 如需中文界面，可先在 Inno Setup 中安装 ChineseSimplified.isl 后启用：
; Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\app_demo\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

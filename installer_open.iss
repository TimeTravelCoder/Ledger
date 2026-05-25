; ============================================================
; LedgerOpen 开源版安装脚本 (Inno Setup)
; ============================================================

#define MyAppName "LedgerOpen"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TimeTravelCoder"
#define MyAppURL "https://github.com/TimeTravelCoder/LedgerOpen"
#define MyAppExeName "LedgerOpen.exe"
#define MyAppDescription "LedgerOpen 桌面文档分类与智能管理工具"

[Setup]
; 基本信息
AppId={{B2C3D4E5-F6A7-8901-BCDE-F1234567890A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases

; 安装路径
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; 输出设置
OutputDir=dist
OutputBaseFilename=LedgerOpen-Setup-v1.0.0-windows
SetupIconFile=app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; 系统要求
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; 权限 (不需要管理员也可以安装到用户目录)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式(&D)"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序
Source: "dist\LedgerOpen.exe"; DestDir: "{app}"; Flags: ignoreversion

; 文档
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "RELEASE_NOTES.md"; DestDir: "{app}"; DestName: "发布说明.md"; Flags: ignoreversion
Source: "电脑文档管理规范.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 开始菜单
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; 桌面快捷方式 (可选)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppDescription}"

[Run]
; 安装完成后可选择立即运行
Filename: "{app}\{#MyAppExeName}"; Description: "立即启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时清理工作区缓存目录
Type: filesandordirs; Name: "{app}"

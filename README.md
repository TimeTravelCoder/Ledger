# Ledger Open

本分支：`master`

Ledger Open 是项目的基础开源版分支，提供本地桌面文档分类管理的最小完整体验。它适合学习项目结构、二次开发、轻量使用和作为其它增强分支的基础参照。

## 分支定位

`master` 是基础版，不追求最新旗舰 UI 或自动发布能力。

- 保留收集箱、工作空间、标签、搜索、查重和备份看板等核心能力。
- 适合快速理解代码结构和本地文件管理流程。
- 不包含 Plus 的工作区增强删除工具。
- 不包含 pro 的多轮安全事务修复合集。
- 不包含 Max 的 Windows Release workflow。
- 不包含 Max_Mac 的 macOS DMG workflow。

需要正式 Windows 发布请使用 `Max`。需要 macOS DMG 请使用 `Max_Mac`。

## 分支关系

| 分支 | 定位 | 适合场景 |
|---|---|---|
| `master` | 基础开源版 | 学习、轻量使用、最小功能集 |
| `Plus` | 增强工作区版 | 重复文件、删除、批量工具和布局验证 |
| `pro` | 安全事务版 | 安全边界、事务、备份、性能修复 |
| `Max` | Windows 旗舰发布版 | Windows zip / 安装器 / Release |
| `Max_Mac` | macOS DMG 分支 | macOS `.app` / `.dmg` 自动构建 |

## 核心功能

- 收集箱：临时存放新文件，补充名称、标签和备注后归档。
- 工作空间：初始化标准目录结构，按目录浏览文件。
- 搜索：基于 SQLite 元数据按文件名、标签和备注检索。
- 标签系统：支持自定义标签，输入时可带 `#` 或不带 `#`。
- 查重清理：基于文件信息检测重复项。
- 备份看板：记录硬盘和云盘备份路径，展示 3-2-1 备份健康度。
- 控制面板：展示文件总数、待整理文件和标签覆盖率等统计信息。
- 设置中心：管理主题、工作空间路径和文件监控开关。

## 快速开始

环境要求：

- Python 3.10+
- Windows 10 / 11 64-bit

安装依赖：

```powershell
pip install PySide6 watchdog
```

启动程序：

```powershell
python main.py
```

首次启动会自动初始化默认工作空间目录。

## 推荐工作流

```text
新文件落地桌面或下载目录
        ↓
导入收集箱
        ↓
填写名称、标签、备注
        ↓
选择分类目录
        ↓
归档到工作空间
        ↓
通过标签和搜索检索
        ↓
按需备份
```

## 打包说明

`master` 分支保留基础安装脚本：

```text
installer_open.iss
```

如需本地尝试 PyInstaller 打包，可先安装：

```powershell
pip install pyinstaller
```

再执行：

```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name LedgerOpen --icon app_icon.ico "--add-data=app_icon.png;." "--add-data=app_icon.ico;." main.py
```

正式发布流程不建议在 `master` 上完成，请使用 `Max` 分支。

## 数据与配置

- `.config.json`：运行时配置。
- `Workspace/`：默认工作空间。
- SQLite 数据库：保存文件路径、标签、备注和备份状态。

这些文件属于本地运行数据，不建议提交到 Git。

## 项目结构

```text
LedgerOpen/
├── main.py
├── config.py
├── db.py
├── file_manager.py
├── ui/
│   ├── main_window.py
│   ├── dashboard_view.py
│   ├── inbox_view.py
│   ├── workspace_view.py
│   ├── backup_view.py
│   ├── settings_view.py
│   └── styles.py
├── app_icon.png
├── app_icon.ico
├── installer_open.iss
├── RELEASE_NOTES.md
└── 电脑文档管理规范.md
```

## 开发检查

```powershell
python -m compileall -q .
```

## 贡献建议

- 基础能力和通用修复可先在 `master` 验证。
- 工作区增强类功能可迁移到 `Plus`。
- 安全事务类修复可迁移到 `pro`。
- 需要面向用户发布的功能应合入 `Max` 或 `Max_Mac`。

## License

本项目基于 MIT License 发布。

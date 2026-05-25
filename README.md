# Ledger Max

本分支：`Max`

Ledger Max 是当前项目的 Windows 旗舰发布分支，面向个人学习、科研资料、项目文档和日常文件的本地化整理。它以“收集箱 -> 智能命名 -> 分类归档 -> 标签检索 -> 3-2-1 备份”为主流程，重点提供完整桌面端体验、稳定的 Windows 打包发布流程和旗舰 UI。

## 分支定位

`Max` 是 Windows 用户的主力分支。

- 面向 Windows 10 / 11 64-bit。
- 保留 Max 旗舰界面、三套主题、多目录监听、语义标签推荐、剧场预览和安全 ZIP 归档。
- 配置了 Windows GitHub Actions 自动构建 workflow。
- 正式 Windows Release 建议从该分支打 `v*` 标签发布。

如果需要 macOS DMG，请使用 `Max_Mac` 分支。`Max` 分支不承担 macOS DMG 构建职责。

## 分支关系

| 分支 | 定位 | 适合场景 |
|---|---|---|
| `master` | 基础开源版 | 学习、轻量使用、最小功能集 |
| `Plus` | 增强工作区版 | 重点验证文件删除、重复文件和批量工具 |
| `pro` | 安全事务版 | 验证事务、安全边界、备份和性能修复 |
| `Max` | Windows 旗舰发布版 | Windows 正式打包、安装器、Release 发布 |
| `Max_Mac` | macOS DMG 分支 | macOS `.app` / `.dmg` 自动构建 |

## 核心功能

- 控制面板：统计文件数量、收集箱待处理项、标签覆盖率、最近修改和备份健康度。
- 智能收集箱：拖拽文件、一键投递、命名模板、标签与备注录入。
- 多目录监听：最多监听 3 个常用投递目录，例如 Downloads、桌面和聊天文件目录。
- 工作空间浏览器：目录树、搜索、标签筛选、状态筛选、路径复制、文件定位和详情编辑。
- 文件预览：支持文本、Markdown、代码、图片、PDF、Office Open XML 文档文本提取。
- 智能标签推荐：根据文件名和备注推荐常用标签。
- 批量操作：批量移动、批量追加标签、重复文件扫描、自动规则归类。
- 安全 ZIP 归档：多选文件打包为 ZIP，并在校验成功后清理源文件。
- 3-2-1 备份：记录硬盘和云盘备份位置，执行增量镜像备份。
- 旗舰主题：Cyber Dark、Chinese Jade、Slate Light。

## 快速运行

环境要求：

- Python 3.10+
- Windows 10 / 11 64-bit

安装依赖：

```powershell
pip install -r requirements.txt
```

启动程序：

```powershell
python main.py
```

首次启动会创建默认工作空间，并初始化标准目录模板。

## 本地 Windows 打包

安装构建依赖：

```powershell
pip install -r requirements-build.txt
```

构建单文件 EXE：

```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name Ledger --icon app_icon.ico "--add-data=app_icon.png;." "--add-data=app_icon.ico;." main.py
```

构建 Inno Setup 安装器：

```powershell
& "C:\Users\Ming\AppData\Local\Programs\Inno Setup 6\iscc.exe" installer.iss
```

构建产物：

```text
dist/Ledger.exe
dist/Ledger-v<version>-windows-x64.zip
dist/Ledger-Setup-v<version>-windows-x64.exe
```

## Windows 自动构建与发布

`Max` 分支包含 Windows 专用 workflow：

```text
.github/workflows/build-windows-release.yml
```

触发方式：

- 推送 `Max` 分支：构建 Windows EXE、zip 和安装器，并上传 Actions artifact。
- 手动运行 `Build Windows Release`：用于不发版的打包验证。
- 推送 `v*` 标签：自动创建或更新 GitHub Release，并上传 Windows zip 和安装器。

正式发布示例：

```powershell
git switch Max
git pull
git tag v1.2.3
git push origin v1.2.3
```

详细说明见：

```text
WINDOWS_RELEASE_WORKFLOW.md
```

## 默认目录规范

```text
00Inbox / 00收集箱
01Study / 01课程学习
02Research / 02课题研究
03Projects / 03项目管理
04Code / 04代码仓库
05Papers / 05学术论文
06Notes / 06知识笔记
07Resources / 07常用资源
08PPT / 08演示汇报
09Resume / 09个人简历
10Archive / 10归档区
99Temp / 99临时缓冲
```

可以在设置页启用自定义目录模板。

## 数据与配置

- `.config.json`：本地配置文件。
- `Workspace/`：默认工作空间。
- `Workspace/.docman.db`：SQLite 元数据数据库。

这些都是本地运行数据，不建议提交到 Git。

## 项目结构

```text
Ledger/
├── .github/workflows/build-windows-release.yml
├── main.py
├── config.py
├── db.py
├── file_manager.py
├── semantic_analyzer.py
├── ui/
│   ├── main_window.py
│   ├── dashboard_view.py
│   ├── inbox_view.py
│   ├── workspace_view.py
│   ├── backup_view.py
│   ├── settings_view.py
│   ├── styles.py
│   ├── icon_utils.py
│   └── toast.py
├── app_icon.png
├── app_icon.ico
├── installer.iss
├── requirements.txt
├── requirements-build.txt
├── RELEASE_NOTES.md
├── WINDOWS_RELEASE_WORKFLOW.md
└── 电脑文档管理规范.md
```

## 开发检查

```powershell
python -m py_compile main.py config.py file_manager.py db.py ui\workspace_view.py ui\main_window.py
```

如果修改移动、删除、备份或 ZIP 归档逻辑，建议先用测试工作空间验证，避免直接操作重要资料。

## License

本项目基于 MIT License 发布。

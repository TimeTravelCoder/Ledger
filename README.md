<div align="center">

# 👑 Ledger Max · Windows 旗舰版

**本地桌面文档分类、智能命名、标签检索与安全备份工具**

[![Branch](https://img.shields.io/badge/Branch-Max-6366F1)](https://github.com/TimeTravelCoder/Ledger/tree/Max)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)](https://github.com/TimeTravelCoder/Ledger)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt)](https://doc.qt.io/qtforpython/)
[![Release](https://img.shields.io/badge/Windows-Release-success)](https://github.com/TimeTravelCoder/Ledger/releases)

✨ `Max` 是 Ledger 的 Windows 旗舰发布分支，负责稳定体验、Windows 自动构建、便携版 zip 与安装器发布。

</div>

---

## 🧭 分支定位

| 分支 | 定位 | 适合场景 |
|---|---|---|
| 📁 `master` | 基础开源版 | 学习、轻量使用、最小功能集 |
| 🧩 `Plus` | 工作区增强版 | 删除、查重、批量工具验证 |
| 🛡️ `pro` | 安全事务版 | 路径安全、备份、事务与性能修复 |
| 👑 `Max` | Windows 旗舰发布版 | Windows zip、安装器、Release |
| 🍎 `Max_Mac` | macOS DMG 分支 | macOS `.app` / `.dmg` 自动构建 |

> 需要 macOS DMG 请使用 `Max_Mac`；本分支专注 Windows 旗舰版发布。

---

## ✨ 旗舰能力

| 模块 | 能力 |
|---|---|
| 📥 智能收集箱 | 拖拽投递、命名模板、标签与备注录入 |
| 📡 多目录监听 | 最多监听 3 个投递目录，新文件落地后提醒整理 |
| 🏷️ 标签推荐 | 根据文件名和备注推荐常用标签 |
| 🗂️ 工作空间 | 目录树、搜索、标签筛选、状态筛选和路径复制 |
| 👁️ 文件预览 | 文本、Markdown、代码、图片、PDF、Office Open XML |
| 🎭 剧场模式 | 文本与图片支持沉浸式大屏预览 |
| 🔒 安全归档 | 多选文件打包 ZIP，校验成功后清理源文件 |
| 💾 3-2-1 备份 | 硬盘 / 云盘备份路径、增量镜像、健康度记录 |
| 🎨 主题系统 | Cyber Dark、Chinese Jade、Slate Light |

---

## 🚀 快速运行

### 环境

- 🐍 Python 3.10+
- 🪟 Windows 10 / 11 64-bit

### 安装依赖

```powershell
pip install -r requirements.txt
```

### 启动

```powershell
python main.py
```

首次启动会创建默认工作空间，并初始化标准目录模板。

---

## 📦 本地 Windows 打包

安装构建依赖：

```powershell
pip install -r requirements-build.txt
```

构建无控制台窗口的单文件 EXE：

```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name Ledger --icon app_icon.ico "--add-data=app_icon.png;." "--add-data=app_icon.ico;." main.py
```

构建 Inno Setup 安装器：

```powershell
& "C:\Users\Ming\AppData\Local\Programs\Inno Setup 6\iscc.exe" installer.iss
```

输出产物：

```text
dist/Ledger.exe
dist/Ledger-v<version>-windows-x64.zip
dist/Ledger-Setup-v<version>-windows-x64.exe
```

---

## 🤖 GitHub Actions 发布

`Max` 分支包含 Windows 专用 workflow：

```text
.github/workflows/build-windows-release.yml
```

| 触发方式 | 结果 |
|---|---|
| 🔁 推送 `Max` | 构建 EXE / zip / installer，并上传 Actions artifact |
| 🖱️ 手动运行 workflow | 用于不发版的打包验证 |
| 🏷️ 推送 `v*` 标签 | 自动创建或更新 Release，并上传 Windows zip 与安装器 |

正式发布示例：

```powershell
git switch Max
git pull
git tag v1.2.4
git push origin v1.2.4
```

详细说明见 [`WINDOWS_RELEASE_WORKFLOW.md`](WINDOWS_RELEASE_WORKFLOW.md)。

---

## 🗃️ 默认目录规范

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

---

## 🧰 数据与配置

| 路径 | 说明 |
|---|---|
| `.config.json` | 本地配置 |
| `Workspace/` | 默认工作空间 |
| `Workspace/.docman.db` | SQLite 元数据数据库 |

这些都是本地运行数据，不建议提交到 Git。

---

## 🏗️ 项目结构

```text
Ledger/
├── .github/workflows/build-windows-release.yml
├── main.py
├── config.py
├── db.py
├── file_manager.py
├── semantic_analyzer.py
├── ui/
├── app_icon.png
├── app_icon.ico
├── installer.iss
├── requirements.txt
├── requirements-build.txt
├── RELEASE_NOTES.md
├── WINDOWS_RELEASE_WORKFLOW.md
└── 电脑文档管理规范.md
```

---

## ✅ 开发检查

```powershell
python -m py_compile main.py config.py file_manager.py db.py ui\workspace_view.py ui\main_window.py
```

---

## 📄 License

本项目基于 MIT License 发布。

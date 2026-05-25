<div align="center">

# 📁 Ledger Open · 基础开源版

**轻量、本地、可学习的桌面文档分类与管理工具**

[![Branch](https://img.shields.io/badge/Branch-master-2563EB)](https://github.com/TimeTravelCoder/Ledger/tree/master)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt)](https://doc.qt.io/qtforpython/)

告别桌面文件乱堆：用“收集箱 -> 整理 -> 工作空间”的方式，让每份文档都有标签、备注和归宿。

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

`master` 是最适合阅读代码、理解结构和二次开发的基础分支。

---

## ✨ 功能亮点

| 模块 | 功能 |
|---|---|
| 📥 收集箱 | 临时存放新文件，补充名称、标签和备注后归档 |
| 🗂️ 工作空间 | 标准目录结构、文件树浏览和搜索 |
| 🔍 检索 | 按文件名、标签和备注关键词检索 SQLite 元数据 |
| 🏷️ 标签系统 | 自定义标签，支持带 `#` 或不带 `#` 输入 |
| 🔁 查重清理 | 检测重复文件并辅助清理 |
| 💾 备份看板 | 记录硬盘 / 云盘备份路径和 3-2-1 健康度 |
| 📊 控制面板 | 文件总数、待整理文件和标签覆盖率 |
| ⚙️ 设置中心 | 主题、工作空间路径和文件监控开关 |

---

## 🚀 快速开始

环境：

- 🐍 Python 3.10+
- 🪟 Windows 10 / 11 64-bit

安装依赖：

```powershell
pip install PySide6 watchdog
```

启动：

```powershell
python main.py
```

首次启动会自动初始化默认工作空间目录。

---

## 🔄 推荐工作流

```text
📄 新文件落地桌面或下载目录
        ↓
📥 导入收集箱
        ↓
🏷️ 填写名称、标签、备注
        ↓
🗂️ 选择分类目录
        ↓
✅ 归档到工作空间
        ↓
🔍 通过标签和搜索检索
        ↓
💾 按需备份
```

---

## 📦 打包说明

`master` 保留基础安装脚本：

```text
installer_open.iss
```

本地尝试 PyInstaller：

```powershell
pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name LedgerOpen --icon app_icon.ico "--add-data=app_icon.png;." "--add-data=app_icon.ico;." main.py
```

正式发布建议使用 `Max` 分支。

---

## 🧰 数据与配置

| 路径 | 说明 |
|---|---|
| `.config.json` | 运行时配置 |
| `Workspace/` | 默认工作空间 |
| SQLite 数据库 | 文件路径、标签、备注和备份状态 |

---

## 🏗️ 项目结构

```text
LedgerOpen/
├── main.py
├── config.py
├── db.py
├── file_manager.py
├── ui/
├── app_icon.png
├── app_icon.ico
├── installer_open.iss
├── RELEASE_NOTES.md
└── 电脑文档管理规范.md
```

---

## ✅ 开发检查

```powershell
python -m compileall -q .
```

---

## 📄 License

本项目基于 MIT License 发布。

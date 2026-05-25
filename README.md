<div align="center">

# 🧩 Ledger Plus · 工作区增强版

**面向文件列表、重复文件、删除动作和批量工具体验的增强分支**

[![Branch](https://img.shields.io/badge/Branch-Plus-F59E0B)](https://github.com/TimeTravelCoder/Ledger/tree/Plus)
[![Focus](https://img.shields.io/badge/Focus-Workspace%20Tools-F97316)](https://github.com/TimeTravelCoder/Ledger)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt)](https://doc.qt.io/qtforpython/)

`Plus` 用来打磨工作区高频操作：查重、多选、删除、移动、批量工具和布局空间。

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

> `Plus` 不是正式发布分支；它更像工作区操作体验的试验台。

---

## ✨ Plus 增强点

| 模块 | 增强 |
|---|---|
| 🔍 重复文件 | 结果列表、多选处理、删除工具 |
| 🗑️ 文件删除 | 删除逻辑与查重状态解耦 |
| 🚚 文件移动 | 目标冲突处理和批量移动体验 |
| 🧰 批量工具 | 简化工作区批量操作入口 |
| 📐 布局空间 | 优化工作区下方面板和按钮间距 |
| 🧾 状态同步 | 删除后刷新文件列表和元数据 |

---

## 📦 基础功能

| 模块 | 能力 |
|---|---|
| 📥 收集箱 | 文件整理、命名和归档 |
| 🗂️ 工作空间 | 标准目录、文件列表、搜索和筛选 |
| 🏷️ 标签系统 | 自定义标签、备注和状态 |
| 💾 备份看板 | 备份路径和健康度统计 |
| 📊 控制面板 | 最近文件、标签分布和基础统计 |

---

## 🚀 快速运行

```powershell
pip install PySide6 watchdog
python main.py
```

环境：

- 🐍 Python 3.10+
- 🪟 Windows 10 / 11 64-bit

---

## 🧪 推荐验证流程

1. 🧰 准备测试工作空间和样例文件。
2. 🔍 放入同名、同大小或内容重复的文件。
3. ✅ 扫描重复文件，验证列表和多选。
4. 🗑️ 测试删除重复项和普通文件。
5. 🚚 测试批量移动与目标冲突。
6. 🔄 验证删除/移动后列表、数据库和磁盘状态一致。

---

## 🧰 数据与配置

| 路径 | 说明 |
|---|---|
| `.config.json` | 本地配置 |
| `Workspace/` | 默认工作空间 |
| SQLite 数据库 | 文件路径、标签、备注和备份状态 |

---

## 🏗️ 项目结构

```text
Ledger/
├── main.py
├── config.py
├── db.py
├── file_manager.py
├── ui/
├── app_icon.png
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

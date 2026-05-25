<div align="center">

# 🛡️ Ledger Pro · 安全事务版

**面向文件操作安全、数据库一致性和备份稳定性的增强分支**

[![Branch](https://img.shields.io/badge/Branch-pro-0F766E)](https://github.com/TimeTravelCoder/Ledger/tree/pro)
[![Focus](https://img.shields.io/badge/Focus-Safety%20%26%20Transactions-14B8A6)](https://github.com/TimeTravelCoder/Ledger)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt)](https://doc.qt.io/qtforpython/)

`pro` 是 Ledger 的可靠性验证分支，专注路径安全、文件事务、备份边界、SQLite 同步和高风险操作回归。

</div>

---

## 🧭 分支定位

| 分支 | 定位 | 适合场景 |
|---|---|---|
| 📁 `master` | 基础开源版 | 学习、轻量使用、最小功能集 |
| 🧩 `Plus` | 工作区增强版 | 删除、查重、批量工具验证 |
| 🛡️ `pro` | 安全事务版 | 路径安全、事务、备份、性能修复 |
| 👑 `Max` | Windows 旗舰发布版 | Windows zip、安装器、Release |
| 🍎 `Max_Mac` | macOS DMG 分支 | macOS `.app` / `.dmg` 自动构建 |

> `pro` 不是正式发布分支。确认稳定后，再把需要发布的修复迁移到 `Max` 或 `Max_Mac`。

---

## 🔐 Pro 重点

| 方向 | 说明 |
|---|---|
| 🧱 路径边界 | 阻断路径穿越、非法字符和目录逃逸 |
| 🧾 数据一致性 | 降低数据库记录与真实磁盘状态不一致 |
| 🗑️ 删除安全 | 校验文件状态，减少误删和残留记录 |
| 🚚 移动事务 | 处理命名冲突、移动失败和元数据同步 |
| 💾 备份安全 | 避免循环备份、离线设备和云备份异常 |
| 🧪 回归验证 | 用于高风险文件逻辑的集中测试 |
| ⚡ 性能修复 | SQLite 预过滤、查询优化、状态刷新 |

---

## ✨ 核心功能

| 模块 | 能力 |
|---|---|
| 📊 控制面板 | 文件总量、占用、收集箱、标签覆盖率、备份健康度 |
| 📥 智能收集箱 | 命名模板、分类目录、标签、备注和状态 |
| 🗂️ 工作空间 | 目录树、搜索、筛选、预览、定位和路径复制 |
| 🏷️ 元数据管理 | SQLite 保存路径、标签、备注、状态和备份记录 |
| 🔍 查重工具 | 文件名、大小、哈希等重复识别 |
| 💾 备份模块 | 硬盘 / 云盘备份配置与增量镜像 |
| ⚙️ 设置中心 | 工作空间、下载目录、主题、标签、规则和模板 |

---

## 🚀 快速运行

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

环境：

- 🐍 Python 3.10+
- 🪟 Windows 10 / 11 64-bit

---

## 🧪 推荐验证流程

1. 🧰 使用测试工作空间，不直接操作真实资料库。
2. 📥 放入少量样例文件到收集箱。
3. 🏷️ 验证命名、归档、标签、状态和备注是否同步到数据库。
4. 🔍 验证重复文件扫描、删除和列表刷新。
5. 🚚 验证移动、重命名和目标冲突。
6. 💾 验证备份目标为空、离线、只读或路径异常时的提示。
7. ✅ 验证 UI、数据库和磁盘状态是否一致。

---

## 🧰 数据与配置

| 路径 | 说明 |
|---|---|
| `.config.json` | 本地配置 |
| `Workspace/` | 默认工作空间 |
| `Workspace/.docman.db` | SQLite 元数据数据库 |

---

## 🏗️ 项目结构

```text
Ledger/
├── main.py
├── config.py
├── db.py
├── file_manager.py
├── requirements.txt
├── ui/
├── app_icon.png
├── app_icon.ico
├── RELEASE_NOTES.md
└── 电脑文档管理规范.md
```

---

## ✅ 开发检查

```powershell
python -m py_compile main.py config.py file_manager.py db.py ui\workspace_view.py ui\main_window.py
python -m compileall -q .
```

---

## 📄 License

本项目基于 MIT License 发布。

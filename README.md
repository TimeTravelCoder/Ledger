<div align="center">

# 📁 Ledger · 开源版

**本地桌面文档分类与智能管理工具**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt)](https://doc.qt.io/qtforpython/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)](https://github.com/TimeTravelCoder/LedgerOpen)

> 告别桌面文件乱堆！Ledger 帮你用「收集箱 → 整理 → 工作空间」的工作流，让每份文档都有标签、有备注、有归宿。

</div>

---

## ✨ 功能亮点

| 模块 | 功能描述 |
|---|---|
| 📥 **收集箱** | 临时存放新文件，填写名称 / 标签 / 备注后一键归档到工作空间 |
| 🗂️ **工作空间** | 标准化目录结构自动初始化，文件树浏览与搜索 |
| 🔍 **全文搜索** | 按文件名、标签、备注关键词快速检索 SQLite 元数据 |
| 🏷️ **标签系统** | 自定义标签字典，支持带 `#` 或不带 `#` 输入，自动归一化 |
| 🔄 **查重清理** | 自动检测 MD5 重复文件，支持多选批量删除 |
| 💾 **备份看板** | 记录硬盘 / 云盘备份路径，直观展示 3-2-1 备份健康度 |
| 📊 **控制面板** | 实时统计文件总数、未整理文件、标签覆盖率等关键指标 |
| ⚙️ **设置中心** | 主题切换、工作空间路径配置、文件监控开关 |

---

## 🖥️ 界面预览

```
┌─────────────────────────────────────────────────────┐
│  📁 Ledger                              [─][□][✕]   │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ 📊 控制面板 │         主内容区域                        │
│ 📥 收集箱  │   · 文件树 / 搜索结果 / 统计卡片            │
│ 🗂️ 工作区  │   · 文件详情面板                          │
│ 🏷️ 标签    │   · 操作按钮栏                            │
│ 💾 备份    │                                          │
│ ⚙️ 设置    │                                          │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- **Python** 3.10 或更高版本
- **操作系统** Windows 10 / 11（64位）

### 安装依赖

```bash
pip install PySide6 watchdog
```

### 启动软件

```bash
python main.py
```

首次启动将自动初始化工作空间目录结构，无需任何手动配置。

---

## 📂 项目结构

```
LedgerOpen/
├── main.py                 # 程序入口
├── config.py               # 全局配置与路径管理
├── db.py                   # SQLite 数据库操作层
├── file_manager.py         # 文件操作核心逻辑
├── ui/
│   ├── main_window.py      # 主窗口框架
│   ├── dashboard_view.py   # 控制面板
│   ├── inbox_view.py       # 收集箱视图
│   ├── workspace_view.py   # 工作空间视图（文件树 + 搜索 + 查重）
│   ├── backup_view.py      # 备份管理视图
│   ├── settings_view.py    # 设置视图
│   └── styles.py           # 全局样式主题
└── 电脑文档管理规范.md        # 推荐文档管理规范参考
```

---

## 🔧 工作流程

```
新文件落地桌面
      ↓
拖入 / 导入「收集箱」
      ↓
填写 文件名 · 标签 · 备注
      ↓
选择归档目标分类
      ↓
一键整理 → 进入「工作空间」
      ↓
SQLite 元数据同步 ✓
标签可搜索 ✓  备份可追踪 ✓
```

---

## ⚙️ 配置说明

| 文件 / 目录 | 说明 |
|---|---|
| `.config.json` | 运行时配置（工作空间路径、主题等），**不建议提交 Git** |
| `Workspace/` | 工作空间根目录，**不建议提交 Git** |
| `ledger.db` | SQLite 数据库，**不建议提交 Git** |

建议将以上三项加入 `.gitignore`。

---

## 🤝 参与贡献

欢迎 Fork 本仓库并提交 Pull Request！

1. Fork 本项目
2. 创建你的功能分支 `git checkout -b feat/your-feature`
3. 提交更改 `git commit -m "feat: add some feature"`
4. 推送分支 `git push origin feat/your-feature`
5. 发起 Pull Request

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源发布，你可以自由使用、修改和分发。

---

<div align="center">

Made with ❤️ by [TimeTravelCoder](https://github.com/TimeTravelCoder)

</div>

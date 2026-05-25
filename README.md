<div align="center">

# 👑 Ledger Max · 旗舰版

**极具格调的本地桌面文档分类与智能管理工具**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt)](https://doc.qt.io/qtforpython/)
[![Theme](https://img.shields.io/badge/Themes-Cyber%20%7C%20Jade%20%7C%20Slate-darkviolet)](https://github.com/TimeTravelCoder/Ledger)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)](https://github.com/TimeTravelCoder/Ledger)

> ✨ **Ledger Max** 是专为个人学习、科研工作者和高端内容创作者打造的本地文档整理与分类利器。它将美学格调融入“收集箱 → 智能重命名 → 归档 → 标签检索 → 3-2-1安全备份”的完整文档流。

</div>

---

## 🎨 Max 旗舰美学 (Premium UI/UX)

- **Glassmorphism 磨砂玻璃特效**：主看板、统计卡片、分类预览面板采用毛玻璃材质，高对比度视觉重心。
- **三套旗舰级配色主题**：
  - 🌑 **赛博极光 (Cyber Dark)**：幽深太空黑与霓虹靛紫发光阴影交相辉映，极具极客质感。
  - 🌿 **温润国风 (Chinese Jade)**：清新象牙白底融合柔美竹叶青，优雅自然。
  - ☀️ **现代极简 (Slate Light)**：高级石墨蓝加持亮白水晶背景，商务洗练。
- **物理缓动微交互动效**：侧边栏按钮、数据卡片悬停时，具有 2px 的柔性悬浮以及微发光平滑过渡，为点击注入灵魂。
- **发光数据 Tooltip**：图表节点随鼠标悬停触发实时高亮气泡，让统计数据富有灵性。

---

## ⚙️ 旗舰生产力扩展 (Flagship Features)

- 📂 **拖拽直达 · 一键投递**：直接拖拽外部文件至“收集箱”区域，零步骤直接录入并唤起归类表单。
- 🏷️ **智能语义标签推荐**：打字输入文件名或备注时，AI 语义分析毫秒级推荐 Top-3 匹配标签，点击一键确认。
- 🎭 **沉浸式剧场阅读器**：纯文本、Markdown 与大图预览支持大屏暗场全屏阅读模式，提供沉浸式检视体验。
- 🔒 **安全保险箱归档**：多选文件一键安全打包为 ZIP 归档，并在打包完成后自动安全删除原磁盘文件与脏数据。

---

## 🛡️ 稳如磐石的安全机制 (Security Core)

- **[P0] 闪退完美避坑**：完美消除由于 `desc_label` 属性未绑定导致的界面加载闪退 Bug，极致丝滑。
- **[P1] 数据库线程安全隔离**：弃用全局单 SQLite 连接，升级为 `threading.local()` 多线程安全池隔离架构，彻底绝迹跨线程访问错误。
- **[P1] 数据防丢失逻辑**：重构未入库文件的整理与归档事务，确保**物理移库与数据入库原子化同步**，杜绝标签丢失。
- **磁盘状态实时失步校验**：备份、排重、移动等物理操作前强制同步磁盘文件状态，避免数据偏差。
- **路径穿越与特权字符拦截**：新建文件与文件夹时，严格过滤 `../`、`..\` 及 Windows 特权非法字符，阻断非法目录注入。

---

## 💻 快速运行与构建

### 1. 运行环境

- **Python** 3.10+
- **系统要求** Windows 10 / 11 (64-bit)

```bash
# 安装系统运行核心依赖
pip install -r requirements.txt
# 运行主程序
python main.py
```

### 2. 编译为可独立执行的桌面程序 (EXE)

```bash
# 安装打包构建依赖
pip install -r requirements-build.txt

# 1. 编译纯 EXE
python -m PyInstaller --noconfirm --onefile --windowed --name Ledger --icon app_icon.ico "--add-data=app_icon.png;." "--add-data=app_icon.ico;." main.py

# 2. 编译专业的 Windows 安装向导 (Inno Setup 6+)
& "C:\Users\Ming\AppData\Local\Programs\Inno Setup 6\iscc.exe" installer.iss
```

---

## 📁 推荐文档归类规范 (Built-in Spec)

软件自动支持中英双语工作空间规范化模板，确保目录层级不超过4层：

```text
00收集箱 (00Inbox)      ← 缓冲暂存，待整理
01课程学习 (01Study)     ← 书本、课件与复习资料
02课题研究 (02Research)  ← 论文草稿、文献库
03项目管理 (03Projects)  ← 需求、计划与周报
04代码仓库 (04Code)      ← 源码工程
05学术论文 (05Papers)    ← PDF 文献与会议记录
06知识笔记 (06Notes)     ← 随笔与 Markdown 笔记
07常用资源 (07Resources) ← 软件包与媒体资源
08演示汇报 (08PPT)       ← 汇报幻灯片
09个人简历 (09Resume)    ← 求职与履历
10归档区 (10Archive)     ← 旧项目冷归档
99临时缓冲 (99Temp)      ← 随时可清的临时测试垃圾桶
```

---

## 📂 系统项目架构

```
Ledger/
├── main.py                 # 应用主入口
├── config.py               # 配置注册与命名规范沙箱
├── db.py                   # SQLite 元数据库 (Thread-local)
├── file_manager.py         # 磁盘I/O事务、3-2-1备份与文件查重
├── ui/
│   ├── main_window.py      # 主侧边栏架构与监听注入
│   ├── dashboard_view.py   # 磨砂玻璃数据统计看板
│   ├── inbox_view.py       # 拖拽投递式智能收集箱
│   ├── workspace_view.py   # 文件树浏览器、剧场预览、批量事务
│   ├── backup_view.py      # 备份配置与健康状态
│   ├── settings_view.py    # 主题切换与字典模板定义
│   ├── styles.py           # 三套旗舰版主题 QSS 样式表
│   ├── toast.py            # 微交互轻提示气泡
│   └── icon_utils.py       # 智能文件格式渲染工具
├── app_icon.png
├── app_icon.ico
├── installer.iss           # Windows 独立安装向导脚本
├── RELEASE_NOTES.md        # 发布日志说明
└── 电脑文档管理规范.md        # 管理规范建议
```

---

## 📄 授权协议

本项目基于 [MIT License](LICENSE) 授权发布，欢迎学习、修改与二次发行。

---

<div align="center">

👑 **Ledger Max · 以极致美学，重塑个人文档归宿**  
Made with 💜 by [TimeTravelCoder](https://github.com/TimeTravelCoder)

</div>

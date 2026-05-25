# Ledger Pro

本分支：`pro`

Ledger Pro 是项目的安全事务与稳定性增强分支。它位于基础版和 Max 旗舰版之间，重点不是发布安装包，而是验证文件操作、数据库同步、路径安全、备份流程和性能优化等核心可靠性能力。

## 分支定位

`pro` 适合用于稳定性验证、核心逻辑回归和安全修复沉淀。

- 强调文件移动、删除、备份和重命名的事务安全。
- 强调路径穿越、非法字符、目录边界等安全防护。
- 强调 SQLite 元数据与真实磁盘文件状态同步。
- 不包含 Max 分支的 Windows Release workflow。
- 不包含 Max_Mac 分支的 macOS DMG workflow。

正式 Windows 发布请使用 `Max` 分支。macOS DMG 请使用 `Max_Mac` 分支。

## 分支关系

| 分支 | 定位 | 适合场景 |
|---|---|---|
| `master` | 基础开源版 | 学习、轻量使用、最小功能集 |
| `Plus` | 增强工作区版 | 文件删除、重复文件和批量工具验证 |
| `pro` | 安全事务版 | 安全边界、事务、备份、性能修复 |
| `Max` | Windows 旗舰发布版 | Windows zip / 安装器 / Release |
| `Max_Mac` | macOS DMG 分支 | macOS `.app` / `.dmg` 自动构建 |

## 核心能力

- 控制面板：统计文件总量、占用空间、收集箱待处理项、标签覆盖率和备份健康度。
- 智能收集箱：按命名模板整理文件，维护标签、备注、状态和分类目标。
- 工作空间浏览器：目录树、搜索、标签筛选、状态筛选、预览、定位和路径复制。
- 文件元数据：使用 SQLite 保存文件路径、标签、备注、状态和备份记录。
- 批量操作：批量追加标签、批量移动、重复文件扫描和建议处理。
- 备份模块：硬盘和云盘路径配置、增量镜像备份和备份状态记录。
- 设置中心：工作空间、下载目录、主题、标签、规则和命名模板。

## Pro 重点修复方向

该分支重点沉淀了多轮 P0/P1 级修复：

- 路径安全边界：限制路径穿越、非法文件名和目录逃逸。
- 删除同步：减少数据库记录与真实磁盘状态不一致。
- 备份安全：避免循环备份、云备份变量错误和目标设备异常。
- 重命名安全：处理冲突、批量重命名和模板变量。
- Office 文件模板：避免新建空白 Office 文件损坏。
- 数据库稳定性：改善连接超时、查询过滤和状态同步。
- UI 可读性：图表、设置面板、进度提示和高对比绘制优化。

## 快速运行

环境要求：

- Python 3.10+
- Windows 10 / 11 64-bit

安装依赖：

```powershell
pip install -r requirements.txt
```

如果当前分支没有虚拟环境，建议先创建：

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

启动程序：

```powershell
python main.py
```

## 推荐验证流程

1. 使用测试目录作为工作空间，不要直接指向真实资料库。
2. 初始化标准目录。
3. 放入少量测试文件到收集箱。
4. 验证重命名、归档、标签、状态和备注是否同步到数据库。
5. 验证重复文件扫描和删除操作。
6. 验证备份目标为空、离线、只读或路径异常时的提示。
7. 验证移动、删除、备份后工作空间视图和数据库记录是否一致。

## 数据与配置

- `.config.json`：本地配置文件。
- `Workspace/`：默认工作空间。
- `Workspace/.docman.db`：SQLite 元数据数据库。

这些文件属于本地运行数据，不建议提交到 Git。

## 项目结构

```text
Ledger/
├── main.py
├── config.py
├── db.py
├── file_manager.py
├── requirements.txt
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
├── RELEASE_NOTES.md
└── 电脑文档管理规范.md
```

## 开发检查

基础语法检查：

```powershell
python -m py_compile main.py config.py file_manager.py db.py ui\workspace_view.py ui\main_window.py
```

全量编译检查：

```powershell
python -m compileall -q .
```

## 注意事项

- `pro` 分支适合做高风险文件逻辑验证，操作真实资料前请先备份。
- 删除、移动、备份和 ZIP 归档都涉及真实磁盘文件，测试时建议使用专门样例目录。
- 如果某个修复需要正式发布，请先合入或移植到 `Max` 分支。

## License

本项目基于 MIT License 发布。

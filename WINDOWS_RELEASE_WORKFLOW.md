# Windows Release Workflow 使用说明

本文档说明 `Max` 分支的 Windows 自动构建与发布流程。

工作流文件：

```text
.github/workflows/build-windows-release.yml
```

GitHub Actions 页面：

```text
https://github.com/TimeTravelCoder/Ledger/actions/workflows/build-windows-release.yml
```

## 这个工作流会做什么

`Build Windows Release` 会在 GitHub 的 `windows-latest` runner 上自动完成：

1. 拉取仓库代码。
2. 安装 Python 3.12。
3. 安装 `requirements.txt` 和 `requirements-build.txt`。
4. 运行基础语法检查。
5. 使用 PyInstaller 构建无控制台窗口的 `Ledger.exe`。
6. 打包绿色便携版 zip。
7. 安装 Inno Setup 并构建 Windows 安装器。
8. 上传 Actions artifact。
9. 如果是 `v*` 标签触发，则自动创建或更新 GitHub Release，并上传 zip 与安装器。

## 触发方式

### 方式 1：推送 Max 分支

适合验证构建是否能通过。

```powershell
git switch Max
git pull
git push origin Max
```

如果只是普通分支推送，产物只会出现在 Actions 的 artifact 中，不会上传到 Release。

产物命名示例：

```text
Ledger-windows-dev-3f3450e
Ledger-vdev-3f3450e-windows-x64.zip
Ledger-Setup-vdev-3f3450e-windows-x64.exe
```

### 方式 2：手动运行 workflow

适合不想新建标签，只想测试一次打包。

操作步骤：

1. 打开 GitHub 仓库。
2. 进入 `Actions`。
3. 选择 `Build Windows Release`。
4. 点击 `Run workflow`。
5. Branch 选择 `Max`。
6. 等待运行完成后，在该 run 页面底部下载 artifact。

手动运行也只上传 Actions artifact，不会自动创建 Release。

### 方式 3：推送版本标签正式发布

适合发布给用户下载。

推荐版本号使用纯数字版本，例如：

```text
v1.2.3
v1.3.0
v2.0.0
```

本地发布命令：

```powershell
git switch Max
git pull
git tag v1.2.3
git push origin v1.2.3
```

推送 `v*` 标签后，工作流会自动：

- 创建或更新 `v1.2.3` Release。
- 生成 GitHub 自动更新说明。
- 上传 `Ledger-v1.2.3-windows-x64.zip`。
- 上传 `Ledger-Setup-v1.2.3-windows-x64.exe`。

Release 下载页格式：

```text
https://github.com/TimeTravelCoder/Ledger/releases/tag/v1.2.3
```

## 输出文件说明

### Actions artifact

每次 workflow 成功后都会上传 artifact，里面包含：

```text
Ledger.exe
Ledger-v<version>-windows-x64.zip
Ledger-Setup-v<version>-windows-x64.exe
```

### GitHub Release 资产

只有 `v*` 标签触发时才会上传到 Release：

```text
Ledger-v<version>-windows-x64.zip
Ledger-Setup-v<version>-windows-x64.exe
```

其中：

- `Ledger-v<version>-windows-x64.zip`：绿色便携版，解压即可运行。
- `Ledger-Setup-v<version>-windows-x64.exe`：Windows 安装向导，适合普通用户。

## Release Notes 怎么写

当前 workflow 在自动创建 Release 时使用 GitHub 的 `--generate-notes`。

如果需要更正式的中文更新说明，可以在构建成功后手动编辑 Release：

1. 打开对应 Release 页面。
2. 点击 `Edit`。
3. 修改标题和说明。
4. 保存。

也可以使用命令行：

```powershell
gh release edit v1.2.3 --title "Ledger Max v1.2.3" --notes-file RELEASE_NOTES.md
```

## 重新发布或修复失败标签

如果标签已经推送，但构建失败，修复代码后可以把标签移动到新提交：

```powershell
git tag -f v1.2.3
git push --force origin v1.2.3
```

注意：这会改写远端标签指向。只有确认该版本还没有被大量用户下载时才建议这样做。

如果只是想重新跑一次同一个 Actions run，可以在 GitHub Actions 页面点击 `Re-run jobs`。

## 常见问题

### 为什么普通 Max 分支推送没有 Release

这是正常行为。普通分支推送只做构建验证和 artifact 上传；只有 `v*` 标签触发才会上传到 Release。

### 为什么 dev 构建里的安装器版本是 0.0.0

Inno Setup 的 `AppVersion` 需要数字版本。普通分支构建使用 `dev-提交号` 作为文件名版本，但安装器内部版本会回退为 `0.0.0`。

正式发布请使用 `v1.2.3` 这类数字标签。

### 为什么 Release 没有中文更新说明

workflow 默认使用 GitHub 自动生成说明。正式发布后建议手动编辑 Release，或者使用 `gh release edit ... --notes-file RELEASE_NOTES.md` 覆盖为中文说明。

### 如果提示权限不足怎么办

检查仓库设置：

```text
Settings -> Actions -> General -> Workflow permissions
```

需要允许 GitHub Actions 具备写入 Release 的权限。当前仓库已经验证过可以上传 Release 资产。

### 如果 Inno Setup 安装失败怎么办

查看 Actions 日志中的 `Install Inno Setup` 步骤。该步骤通过 Chocolatey 安装：

```powershell
choco install innosetup --no-progress -y
```

如果 Chocolatey 源临时失败，通常重新运行 job 即可。

## 推荐发布流程

1. 在 `Max` 分支完成代码修改。
2. 推送 `Max`，等待 `Build Windows Release` 成功。
3. 确认 artifact 能正常生成。
4. 决定版本号，例如 `v1.2.3`。
5. 推送版本标签。
6. 等待 Release 自动生成。
7. 编辑 Release Notes，补充正式中文更新说明。
8. 在 Release 页面确认 zip 和安装器都可以下载。

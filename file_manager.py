import os
import shutil
import datetime
import hashlib
from pathlib import Path
from config import config
from db import db

# Standard directories are now dynamically fetched from global config

PROJECT_SUBDIRS = [
    "docs",
    "src",
    "data",
    "assets",
    "models",
    "output",
    "test"
]

BANNED_KEYWORDS = ["最终版", "最终版2", "最新最终版", "新建文档", "新建文本文档", "新建文件夹", "最终修改版", "最最新版"]

class FileManager:
    @staticmethod
    def _delete_workspace_record(abs_path):
        try:
            ws_root = Path(config.workspace_dir).resolve()
            abs_path = Path(abs_path).resolve()
            rel_path = str(abs_path.relative_to(ws_root)).replace("\\", "/")
            if db.get_file_info(rel_path):
                db.delete_file_record(rel_path)
        except Exception:
            pass

    @staticmethod
    def move_replace(src_path, dest_path, replace=True):
        """Move a file and replace any existing destination file (or auto-rename if replace is False)."""
        src = Path(src_path)
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists():
            if replace:
                FileManager._delete_workspace_record(dest)
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            else:
                # Resolve duplicate names by appending incremental suffixes
                stem = dest.stem
                ext = dest.suffix
                counter = 1
                while True:
                    candidate_name = f"{stem}_{counter}{ext}"
                    candidate_dest = dest.parent / candidate_name
                    if not candidate_dest.exists():
                        dest = candidate_dest
                        break
                    counter += 1

        shutil.move(str(src), str(dest))
        return dest

    @staticmethod
    def safe_workspace_path(rel_path):
        """Sanitize and validate that resolved paths never escape the workspace root.
        Rejects absolute paths and parent traversals (..) outside the workspace."""
        ws_root = Path(config.workspace_dir).resolve()

        # Check if the path is absolute
        p = Path(rel_path)
        if p.is_absolute():
            resolved = p.resolve()
        else:
            resolved = (ws_root / rel_path).resolve()

        if resolved == ws_root or resolved.is_relative_to(ws_root):
            return resolved

        raise PermissionError(f"安全边界拦截：路径 '{rel_path}' 尝试越界访问工作空间外部！")

    @staticmethod
    def delete_file(rel_path):
        """Delete a workspace file and its database record safely."""
        try:
            if not rel_path or rel_path.strip() in ["", ".", "/"]:
                raise ValueError("安全边界拦截：严禁传入空路径或工作空间根目录进行删除！")

            abs_path = FileManager.safe_workspace_path(rel_path)
            ws_root = Path(config.workspace_dir).resolve()
            if abs_path.resolve() == ws_root:
                raise PermissionError("安全边界拦截：严禁删除工作区根目录本身！")

            is_dir = False
            if abs_path.exists():
                is_dir = abs_path.is_dir()
                if is_dir:
                    shutil.rmtree(abs_path)
                else:
                    abs_path.unlink()

            # Cascade delete database records (sub-files as well if it's a folder)
            if is_dir:
                db.delete_folder_records(rel_path)
            else:
                db.delete_file_record(rel_path)
        except Exception as e:
            raise e

    @staticmethod
    def get_desktop_path():
        """Returns the user's authentic desktop path on Windows, handling OneDrive redirection."""
        if os.name == "nt":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
                )
                path, _ = winreg.QueryValueEx(key, "Desktop")
                winreg.CloseKey(key)
                expanded = os.path.expandvars(path)
                if os.path.exists(expanded):
                    return expanded
            except Exception:
                pass
        return str(Path.home() / "Desktop")

    @staticmethod
    def init_workspace(custom_ws_dir=None, custom_lang=None):
        """Create standard workspace directory structure."""
        ws_path = custom_ws_dir if custom_ws_dir else config.workspace_dir

        # Retrieve folders based on configuration
        if config.use_custom_dirs and config.custom_standard_dirs:
            dirs = config.custom_standard_dirs
        else:
            lang = custom_lang if custom_lang else config.workspace_lang
            from config import STANDARD_DIRS_CN, STANDARD_DIRS_EN
            dirs = STANDARD_DIRS_CN if lang == "cn" else STANDARD_DIRS_EN

        ws_root = Path(ws_path)
        try:
            ws_root.mkdir(parents=True, exist_ok=True)
            ws_root_abs = ws_root.resolve()
            for d in dirs:
                # Resolve paths to enforce secure boundaries
                target_path = (ws_root / d).resolve()
                if not target_path.is_relative_to(ws_root_abs):
                    print(f"Skipping dangerous workspace path traversal: {d}")
                    continue
                target_path.mkdir(parents=True, exist_ok=True)
            return True, "工作空间目录及标准分类文件夹初始化成功！"
        except Exception as e:
            return False, f"初始化工作空间失败: {str(e)}"

    @staticmethod
    def init_project_structure(project_name):
        """Helper to initialize standard structure for a new project in 03_Projects."""
        ws_root = Path(config.workspace_dir)
        proj_folder = config.get_standard_dirs()[3]
        proj_dir = ws_root / proj_folder / project_name

        # Guard layer depth check
        depth = FileManager.get_folder_depth(ws_root, proj_dir)
        if depth > 4:
            return False, f"项目深度 ({depth}层) 超过推荐的最大4层！"

        try:
            proj_dir.mkdir(parents=True, exist_ok=True)
            for subd in PROJECT_SUBDIRS:
                (proj_dir / subd).mkdir(exist_ok=True)

            readme_path = proj_dir / "README.md"
            if not readme_path.exists():
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(f"# {project_name}\n\n项目创建于: {datetime.datetime.now().strftime('%Y-%m-%d')}\n")

            return True, f"项目 '{project_name}' 目录结构创建成功！"
        except Exception as e:
            return False, f"创建项目结构失败: {str(e)}"

    @staticmethod
    def get_folder_depth(base_dir, target_path):
        """Calculate folder layer depth relative to the base directory. Base level is 0."""
        try:
            base = Path(base_dir).resolve()
            target = Path(target_path).resolve()

            if not target.is_relative_to(base):
                return 0

            # Count parts of relative path
            rel_parts = target.relative_to(base).parts
            return len(rel_parts)
        except Exception:
            return 0

    @staticmethod
    def check_folder_depth_violation(target_rel_path):
        """Check if relative target path violates the 4-layer depth limit."""
        ws_root = Path(config.workspace_dir)
        target_abs = ws_root / target_rel_path
        depth = FileManager.get_folder_depth(ws_root, target_abs)
        return depth > 4, depth

    @staticmethod
    def is_banned_name(filename):
        """Check if filename contains banned words."""
        stem = Path(filename).stem
        for keyword in BANNED_KEYWORDS:
            if keyword in stem:
                return True
        return False

    @staticmethod
    def create_file(relative_path: str, content: str = ""):
        """Create a new file at the given workspace-relative path safely.
        Returns (success: bool, message: str)."""
        try:
            file_path = FileManager.safe_workspace_path(relative_path)

            # Prevent 0-byte Office binary creations which MS Office/WPS flags as corrupt
            ext = file_path.suffix.lower()
            if ext in [".docx", ".xlsx", ".pptx"]:
                return False, "Office 复合二进制格式 (docx/xlsx/pptx) 暂不支持直接新建。请在资源管理器中正常创建后，拖入收集箱进行智能归档！"

            file_path.parent.mkdir(parents=True, exist_ok=True)
            if file_path.exists():
                return False, f"文件已存在: {relative_path}"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True, f"文件创建成功: {relative_path}"
        except Exception as e:
            return False, f"创建文件失败: {str(e)}"

    @staticmethod
    def create_folder(relative_path: str):
        """Create a new folder at the given workspace-relative path safely.
        Returns (success: bool, message: str)."""
        try:
            folder_path = FileManager.safe_workspace_path(relative_path)

            # Depth check: folder itself should not exceed 4 levels under workspace root
            is_violation, depth = FileManager.check_folder_depth_violation(relative_path)
            if is_violation:
                return False, f"目录层级深度为 {depth} 层，超过规范上限 4 层，无法创建！"

            if folder_path.exists():
                return False, f"文件夹已存在: {relative_path}"

            folder_path.mkdir(parents=True, exist_ok=False)
            return True, f"文件夹创建成功: {relative_path}"
        except Exception as e:
            return False, f"创建文件夹失败: {str(e)}"


    @staticmethod
    def scan_desktop_files():
        """Scan non-shortcut files on desktop."""
        desktop = Path(FileManager.get_desktop_path())
        if not desktop.exists():
            return []

        file_list = []
        try:
            for entry in os.scandir(desktop):
                if entry.is_file():
                    # Exclude desktop shortcuts and hidden system files
                    ext = Path(entry.name).suffix.lower()
                    if ext not in [".lnk", ".ini", ".url"] and not entry.name.startswith("~$"):
                        file_list.append({
                            "path": entry.path,
                            "name": entry.name,
                            "size": entry.stat().st_size,
                            "modified": datetime.datetime.fromtimestamp(entry.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        })
        except Exception as e:
            print(f"Error scanning desktop: {e}")

        return file_list

    @staticmethod
    def scan_desktop_summary():
        """Return desktop summary for UX feedback."""
        desktop = Path(FileManager.get_desktop_path())
        summary = {
            "normal_files": 0,
            "folders": 0,
            "shortcuts": 0,
            "temporary_files": 0
        }
        if not desktop.exists():
            return summary

        try:
            for entry in os.scandir(desktop):
                if entry.is_dir():
                    summary["folders"] += 1
                    continue
                ext = Path(entry.name).suffix.lower()
                if entry.name.startswith("~$"):
                    summary["temporary_files"] += 1
                elif ext in [".lnk", ".ini", ".url"]:
                    summary["shortcuts"] += 1
                else:
                    summary["normal_files"] += 1
        except Exception as e:
            print(f"Error scanning desktop summary: {e}")
        return summary

    @staticmethod
    def clean_desktop_to_inbox():
        """Move non-shortcut files from Desktop to Inbox."""
        desktop_files = FileManager.scan_desktop_files()
        inbox_dir = Path(config.workspace_dir) / config.get_inbox_name()

        inbox_dir.mkdir(parents=True, exist_ok=True)
        moved_count = 0
        errors = []

        for file_info in desktop_files:
            src = Path(file_info["path"])
            dest = inbox_dir / src.name
            try:
                FileManager.move_replace(src, dest, replace=False)
                moved_count += 1
            except Exception as e:
                errors.append(f"无法移动 {src.name}: {str(e)}")

        return moved_count, errors

    @staticmethod
    def scan_workspace_files():
        """Scan workspace and sync file metadata with SQLite DB, cleaning up deleted items. Accelerated via Rust."""
        ws_root = Path(config.workspace_dir)
        if not ws_root.exists():
            return 0

        disk_files = set()
        scanned_count = 0

        try:
            # Import our rust core extension locally to avoid top-level import errors
            try:
                import ledger_core
                rust_available = True
            except ImportError:
                rust_available = False

            if rust_available:
                # Fast path using Rust parallel scanner
                results = ledger_core.scan_workspace_files(str(ws_root.resolve()))
                for rel_path, filename, size, mtime in results:
                    disk_files.add(rel_path)
                    try:
                        db.sync_file_metadata(rel_path, filename, size, mtime)
                        scanned_count += 1
                    except Exception as e:
                        print(f"Error syncing metadata for {rel_path}: {e}")
            else:
                # Fallback path using standard Python os.walk
                for root, dirs, files in os.walk(ws_root):
                    dirs[:] = [d for d in dirs if not d.startswith(".") and not d.startswith("$")]
                    for f in files:
                        if f.startswith(".") or f in [".docman.db", ".config.json"] or f.startswith("~$"):
                            continue

                        file_abs_path = Path(root) / f
                        rel_path = str(file_abs_path.relative_to(ws_root)).replace("\\", "/")
                        disk_files.add(rel_path)

                        try:
                            stat = file_abs_path.stat()
                            db.sync_file_metadata(rel_path, f, stat.st_size, stat.st_mtime)
                            scanned_count += 1
                        except Exception as e:
                            print(f"Error syncing metadata for {rel_path}: {e}")

            # Clean up db records for files that are no longer on disk
            db_files = [row["filepath"] for row in db.search_files()]
            to_delete = [db_f for db_f in db_files if db_f not in disk_files]
            if to_delete:
                db.delete_file_records(to_delete)

        except Exception as e:
            print(f"Error scanning workspace: {e}")

        return scanned_count

    @staticmethod
    def organize_file(src_path, dest_rel_path, new_filename):
        """Move and rename a file into the structured workspace safely."""
        ws_root = Path(config.workspace_dir)
        src = Path(src_path)
        dest = FileManager.safe_workspace_path(dest_rel_path)

        if src.resolve() == dest.resolve():
            return str(dest.relative_to(ws_root)).replace("\\", "/")

        # 1. Banned word check
        if FileManager.is_banned_name(new_filename):
            raise ValueError(f"文件名 '{new_filename}' 包含禁用词！(如: {', '.join(BANNED_KEYWORDS)})")

        # 2. Depth check
        is_violation, depth = FileManager.check_folder_depth_violation(dest_rel_path)
        if is_violation:
            raise ValueError(f"保存路径的层级深度 ({depth}层) 超过规范最大限制 (4层)！")

        # 3. Create parent directories
        dest.parent.mkdir(parents=True, exist_ok=True)

        # 4. Handle duplicate name collisions safely by appending incremental numeric suffixes
        if dest.exists():
            stem = dest.stem
            ext = dest.suffix
            counter = 1
            while True:
                candidate_name = f"{stem}_{counter}{ext}"
                candidate_dest = dest.parent / candidate_name
                if not candidate_dest.exists():
                    dest = candidate_dest
                    new_filename = candidate_name
                    break
                counter += 1

        # 5. Pre-read source stats inside workspace (if inside and exists) before physical move
        src_is_inside = False
        src_rel_path = None
        src_stat = None
        try:
            src_rel = src.relative_to(ws_root)
            src_is_inside = True
            src_rel_path = str(src_rel).replace("\\", "/")
            if src.exists():
                src_stat = src.stat()
        except ValueError:
            pass

        # 6. Physical Move
        shutil.move(str(src), str(dest))

        # 7. Database Update
        # Calculate new relative path dynamically based on final dest position
        new_rel_path = str(dest.relative_to(ws_root)).replace("\\", "/")

        if src_is_inside and src_rel_path:
            if not db.get_file_info(src_rel_path) and src_stat is not None:
                db.sync_file_metadata(src_rel_path, src.name, src_stat.st_size, src_stat.st_mtime)
            db.rename_file_record(src_rel_path, new_rel_path, new_filename)
        else:
            # Sync fresh file metadata
            stat = dest.stat()
            db.sync_file_metadata(new_rel_path, new_filename, stat.st_size, stat.st_mtime)

        return new_rel_path

    @staticmethod
    def perform_backup(backup_type, workspace_records=None):
        """Incremental mirroring backup to disk or cloud."""
        # Ensure database is synchronized with physical disk before backup
        FileManager.scan_workspace_files()

        ws_root = Path(config.workspace_dir)
        if not ws_root.exists():
            return False, "工作空间未创建，无法备份。"

        dest_dir = config.backup_disk_dir if backup_type == "disk" else config.backup_cloud_dir
        if not dest_dir:
            return False, f"未配置{'外部硬盘' if backup_type == 'disk' else '云盘'}备份路径！"

        dest_path = Path(dest_dir)

        # Verify drive root connectivity and enforce loop-backup prevention
        try:
            dest_abs = dest_path.resolve()
            ws_root_abs = ws_root.resolve()

            # Enforce Loop Backup Prevention: backup path cannot be equal to or inside the workspace
            if dest_abs == ws_root_abs or dest_abs.is_relative_to(ws_root_abs):
                return False, "安全拦截：备份目标目录不能设定在工作空间内部，否则会导致循环套娃备份！"

            drive_root = dest_abs.anchor
            # Check if anchor is resolved and physically online/exists
            if drive_root and not os.path.exists(drive_root):
                return False, f"备份存储介质不可用，请确认对应的驱动器或盘符 '{drive_root}' 已正确连接并挂载！"
        except Exception as e:
            return False, f"路径有效性检查失败: {str(e)}"

        try:
            dest_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"无法访问备份目录: {str(e)}"

        copied_files_count = 0
        copied_bytes_count = 0
        backed_up_rel_paths = []

        # Get all records in the db if not pre-queried
        if workspace_records is None:
            workspace_records = db.search_files()

        for record in workspace_records:
            rel_path = record["filepath"]
            src_file = ws_root / rel_path

            if not src_file.exists():
                continue

            dst_file = dest_path / rel_path

            # Check if we need to copy
            need_copy = False
            if not dst_file.exists():
                need_copy = True
            else:
                src_stat = src_file.stat()
                dst_stat = dst_file.stat()
                if src_stat.st_size != dst_stat.st_size or abs(src_stat.st_mtime - dst_stat.st_mtime) > 0.1:
                    need_copy = True

            if need_copy:
                try:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src_file), str(dst_file))

                    # Verify integrity via SHA256 checksums
                    src_hash = FileManager.calculate_file_hash(src_file)
                    dst_hash = FileManager.calculate_file_hash(dst_file)
                    if src_hash != dst_hash:
                        raise ValueError(f"文件 {rel_path} 备份完整性校验失败，校验和不一致！")

                    copied_files_count += 1
                    copied_bytes_count += src_file.stat().st_size
                except Exception as e:
                    print(f"Error copying {rel_path} to backup: {e}")
                    db.add_backup_history(backup_type, copied_files_count, copied_bytes_count, status=f"error: {str(e)}")
                    return False, f"备份中途失败: {str(e)}"

            backed_up_rel_paths.append(rel_path)

        # Update SQLite status
        db.mark_as_backed_up(backed_up_rel_paths, backup_type)
        db.add_backup_history(backup_type, copied_files_count, copied_bytes_count, status="success")

        size_mb = copied_bytes_count / (1024 * 1024)
        return True, f"备份成功！同步了 {copied_files_count} 个文件 ({size_mb:.2f} MB)。"

    @staticmethod
    def calculate_file_hash(file_path, chunk_size=1024 * 1024):
        """Calculate SHA256 for duplicate detection."""
        file_path = Path(file_path)
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def find_duplicates(mode="filename"):
        """Find duplicate files by filename, size, or hash."""
        # Ensure database is synchronized with physical disk before duplicate scanning
        FileManager.scan_workspace_files()
        ws_root = Path(config.workspace_dir)
        records = db.search_files()
        grouped = {}

        for record in records:
            abs_path = ws_root / record["filepath"]
            if not abs_path.exists():
                continue

            record_data = dict(record)

            if mode == "filename":
                key = record_data["filename"].lower()
            elif mode == "size":
                key = record_data["file_size"]
            else:
                try:
                    key = FileManager.calculate_file_hash(abs_path)
                    record_data["_duplicate_hash"] = key
                except Exception:
                    continue

            grouped.setdefault(key, []).append(record_data)

        return {k: v for k, v in grouped.items() if len(v) > 1}

    @staticmethod
    def suggest_rule_target(filename):
        """Suggest a target directory by keyword and extension."""
        lower_name = filename.lower()
        ext = Path(filename).suffix.lower()

        rules = getattr(config, "auto_rules", [])
        for rule in rules:
            if ext in rule["extensions"] or any(keyword in lower_name for keyword in rule["keywords"]):
                for directory in config.get_standard_dirs():
                    if directory.startswith(rule["target_prefix"]):
                        return rule["name"], directory
        return None, None

    @staticmethod
    def bulk_update_tags(rel_paths, tags_list, mode="replace"):
        """Bulk update tags for multiple records."""
        for rel_path in rel_paths:
            info = db.get_file_info(rel_path)
            if not info:
                continue
            current = [t.strip() for t in info.get("tags", "").split(",") if t.strip()]
            if mode == "append":
                merged = current[:]
                for tag in tags_list:
                    if tag not in merged:
                        merged.append(tag)
                db.update_file_tags(rel_path, merged)
            else:
                db.update_file_tags(rel_path, tags_list)

    @staticmethod
    def bulk_move_files(rel_paths, target_dir, subfolder=""):
        """Bulk move files into a target directory."""
        ws_root = Path(config.workspace_dir)
        moved = []
        subfolder = subfolder.strip().replace("\\", "/").strip("/")
        for rel_path in rel_paths:
            src_abs = ws_root / rel_path
            if not src_abs.exists():
                continue
            new_rel = f"{target_dir}/{subfolder}/{src_abs.name}" if subfolder else f"{target_dir}/{src_abs.name}"
            final_rel = FileManager.organize_file(str(src_abs), new_rel, src_abs.name)
            moved.append(final_rel)
        return moved

    @staticmethod
    def bulk_rename_files(rel_paths, prefix="", suffix=""):
        """Bulk rename files by adding prefix and suffix to stem."""
        ws_root = Path(config.workspace_dir)
        renamed = []
        for rel_path in rel_paths:
            src_abs = ws_root / rel_path
            if not src_abs.exists():
                continue
            new_name = f"{prefix}{src_abs.stem}{suffix}{src_abs.suffix}"
            new_rel = str(Path(rel_path).parent / new_name).replace("\\", "/")
            final_rel = FileManager.organize_file(str(src_abs), new_rel, new_name)
            renamed.append(final_rel)
        return renamed

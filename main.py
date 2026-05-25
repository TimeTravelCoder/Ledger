import os
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox


def get_crash_log_path():
    candidates = []
    appdata_dir = os.environ.get("APPDATA")
    if appdata_dir:
        candidates.append(Path(appdata_dir) / "Ledger")
    candidates.append(Path.home() / ".ledger")
    candidates.append(Path(tempfile.gettempdir()) / "Ledger")

    for base_dir in candidates:
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
            return base_dir / "ledger_crash.log"
        except Exception:
            continue

    return Path(tempfile.gettempdir()) / "ledger_crash.log"


def write_crash_log(exc):
    log_path = get_crash_log_path()
    content = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ledger 启动失败\n"
        f"Python: {sys.version}\n"
        f"Executable: {sys.executable}\n\n"
        f"{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}\n"
    )
    try:
        log_path.write_text(content, encoding="utf-8")
    except Exception:
        pass
    return log_path

def main():
    app = None
    try:
        # 1. Initialize QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Ledger")
        app.setApplicationDisplayName("Ledger")
        app.setQuitOnLastWindowClosed(False)

        from file_manager import FileManager
        from ui.main_window import MainWindow

        # 2. Check if first run (workspace directory doesn't exist yet)
        from config import config
        ws_path = Path(config.workspace_dir)
        is_first_run = not ws_path.exists()

        # 3. Automatically initialize workspace folders on startup
        print("正在初始化规范目录结构...")
        FileManager.init_workspace()

        # 4. Perform a workspace scan to sync existing files with SQLite
        print("正在同步本地磁盘文件与本地 SQLite 数据库...")
        FileManager.scan_workspace_files()

        # 5. Create and display the main window
        print("启动图形化主窗口...")
        window = MainWindow(is_first_run=is_first_run)
        window.show()

        # 6. Run event loop
        return app.exec()
    except Exception as exc:
        log_path = write_crash_log(exc)
        message = (
            "Ledger 启动失败，已记录崩溃日志。\n\n"
            f"错误信息：{exc}\n\n"
            f"日志位置：{log_path}"
        )
        try:
            if QApplication.instance() is None:
                app = QApplication(sys.argv)
            QMessageBox.critical(None, "Ledger 启动失败", message)
        except Exception:
            print(message, file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from file_manager import FileManager

def main():
    # 1. Initialize QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("ComputerDocumentManager")
    app.setApplicationDisplayName("电脑文档分类与管理软件")

    # 2. Check if first run (workspace directory doesn't exist yet)
    from config import config
    from pathlib import Path
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

    # 5. Run event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

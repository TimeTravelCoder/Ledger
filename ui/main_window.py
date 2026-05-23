import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QFrame, 
                             QMessageBox, QSystemTrayIcon, QStyle)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QIcon
from config import config
from ui.styles import get_stylesheet

# Import views
from ui.dashboard_view import DashboardView
from ui.inbox_view import InboxView
from ui.workspace_view import WorkspaceView
from ui.backup_view import BackupView
from ui.settings_view import SettingsView

# Watchdog imports for background Downloads monitoring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DownloadWatcher(FileSystemEventHandler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.last_triggered = {}

    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        # Avoid temporary browser download files like .tmp, .crdownload, .part
        if file_path.suffix.lower() in [".tmp", ".crdownload", ".part", ".download"]:
            return
            
        # Anti-debounce check (sometimes OS triggers multiple created events)
        import time
        now = time.time()
        if str(file_path) in self.last_triggered:
            if now - self.last_triggered[str(file_path)] < 1.0:
                return
        self.last_triggered[str(file_path)] = now
        
        # Emit signal to main GUI thread
        self.signal.emit(str(file_path))

class WatcherThread(QThread):
    file_created_signal = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.observer = None

    def run(self):
        event_handler = DownloadWatcher(self.file_created_signal)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=self.path, recursive=False)
        self.observer.start()
        
        # QThread event loop keeps thread alive
        self.exec()
        
        # When thread exits
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def stop(self):
        if self.observer:
            self.observer.stop()
        self.quit()
        self.wait()

class MainWindow(QMainWindow):
    file_downloaded_notifier = Signal(str)

    def __init__(self, is_first_run=False):
        super().__init__()
        self.is_first_run = is_first_run
        self.watcher_thread = None
        self.init_ui()
        self.setup_downloads_watcher()
        
        # If first run, trigger the welcome popup after rendering
        if self.is_first_run:
            QTimer.singleShot(600, self.show_first_run_welcome)

    def init_ui(self):
        self.setWindowTitle("电脑文档分类与管理软件")
        self.resize(1150, 750)
        self.setMinimumSize(600, 400)  # Allow resizing with reasonable minimum
        
        # Set beautiful app icon
        icon_path = Path(__file__).parent.parent / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Enforce dark or light style sheet based on config
        self.setStyleSheet(get_stylesheet(config.theme))

        # Main Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 15, 0, 15)
        sidebar_layout.setSpacing(5)

        # Sidebar Title
        title_container = QHBoxLayout()
        title_container.setContentsMargins(15, 10, 15, 20)
        
        logo_lbl = QLabel("📂")
        logo_lbl.setStyleSheet("font-size: 24px;")
        title_container.addWidget(logo_lbl)
        
        title_lbl = QLabel("文档分类与管理")
        title_lbl.setObjectName("SidebarTitle")
        title_container.addWidget(title_lbl, 1)
        sidebar_layout.addLayout(title_container)

        # Navigation Buttons
        self.nav_buttons = []
        self.btn_dash = self.create_nav_button("📊 控制面板", 0)
        self.btn_inbox = self.create_nav_button("📥 智能收集箱", 1)
        self.btn_ws = self.create_nav_button("📂 工作空间浏览器", 2)
        self.btn_backup = self.create_nav_button("🛡️ 3-2-1 备份卫士", 3)
        self.btn_settings = self.create_nav_button("⚙️ 软件参数设置", 4)

        for btn in [self.btn_dash, self.btn_inbox, self.btn_ws, self.btn_backup, self.btn_settings]:
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Set default active nav button
        self.btn_dash.setChecked(True)

        sidebar_layout.addStretch()

        # Theme Switching Toggle at bottom of sidebar
        theme_container = QHBoxLayout()
        theme_container.setContentsMargins(15, 10, 15, 10)
        
        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setObjectName("ThemeToggleBtn")
        self.update_theme_btn_text()
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        theme_container.addWidget(self.btn_theme_toggle, 1)
        
        sidebar_layout.addLayout(theme_container)

        main_layout.addWidget(self.sidebar)

        # 2. Right Content Area (QStackedWidget)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("MainContainer")
        
        # Instantiate subviews
        self.view_dashboard = DashboardView()
        self.view_inbox = InboxView()
        self.view_workspace = WorkspaceView()
        self.view_backup = BackupView()
        self.view_settings = SettingsView()

        # Add to stack
        self.content_stack.addWidget(self.view_dashboard)
        self.content_stack.addWidget(self.view_inbox)
        self.content_stack.addWidget(self.view_workspace)
        self.content_stack.addWidget(self.view_backup)
        self.content_stack.addWidget(self.view_settings)

        main_layout.addWidget(self.content_stack, 1)

        # 3. Inter-view Signal & Slots connections
        # Let Dashboard trigger switch to Inbox tab
        self.view_dashboard.switch_to_inbox_signal.connect(lambda: self.switch_tab(1))
        
        # Connect refresh triggers to keep views updated in real-time
        self.view_dashboard.refresh_other_views_signal.connect(self.refresh_all_views)
        self.view_inbox.refresh_other_views_signal.connect(self.refresh_all_views)
        self.view_workspace.refresh_other_views_signal.connect(self.refresh_all_views)
        self.view_backup.refresh_other_views_signal.connect(self.refresh_all_views)
        self.view_settings.refresh_other_views_signal.connect(self.refresh_all_views)
        
        # Background download signals
        self.file_downloaded_notifier.connect(self.on_file_downloaded_notification)

        # Setup System Tray Icon for desktop convenience
        self.setup_tray_icon()

    def create_nav_button(self, text, index):
        btn = QPushButton(text)
        btn.setObjectName("SidebarBtn")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.clicked.connect(lambda: self.switch_tab(index))
        return btn

    def switch_tab(self, index):
        self.content_stack.setCurrentIndex(index)
        # Sync checked states of sidebar buttons (needed if switched programmatically)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            
        # Special refreshes on tab activation
        if index == 0:
            self.view_dashboard.refresh_data()
        elif index == 1:
            self.view_inbox.scan_inbox()
        elif index == 2:
            self.view_workspace.run_search()
        elif index == 3:
            self.view_backup.refresh_history()

    def toggle_theme(self):
        new_theme = "light" if config.theme == "dark" else "dark"
        config.theme = new_theme
        config.save()
        
        # Apply style sheet globally
        self.setStyleSheet(get_stylesheet(config.theme))
        
        # Update sub-components if necessary (e.g. refresh UI states)
        self.update_theme_btn_text()
        self.refresh_all_views()

    def update_theme_btn_text(self):
        if config.theme == "dark":
            self.btn_theme_toggle.setText("☀️ 切换浅色模式")
        else:
            self.btn_theme_toggle.setText("🌙 切换深色模式")

    @Slot()
    def refresh_all_views(self):
        # Prevent database locks or recursive refreshes by executing quietly
        self.view_dashboard.refresh_data()
        self.view_inbox.scan_inbox()
        self.view_inbox.build_tags_checklist()
        self.view_inbox.refresh_directory_combo()
        self.view_workspace.setup_models() # Relink model if path changed
        self.view_workspace.refresh_tags_cloud()
        self.view_workspace.refresh_status_combo()
        self.view_workspace.run_search()
        self.view_backup.refresh_history()

    def setup_downloads_watcher(self):
        """Sets up watchdog file watcher thread on the downloads folder."""
        # Stop previous if any
        if self.watcher_thread:
            self.watcher_thread.stop()
            self.watcher_thread = None

        if not config.monitored_downloads:
            return

        dl_path = config.downloads_dir
        if not os.path.exists(dl_path):
            print(f"Downloads folder '{dl_path}' does not exist, skipping watcher.")
            return

        # Start background watchdog thread
        self.watcher_thread = WatcherThread(dl_path)
        self.watcher_thread.file_created_signal.connect(self.on_file_downloaded_detected)
        self.watcher_thread.start()

    @Slot(str)
    def on_file_downloaded_detected(self, file_path):
        # Debounce/Pass to main GUI thread via custom signal
        self.file_downloaded_notifier.emit(file_path)

    @Slot(str)
    def on_file_downloaded_notification(self, file_path):
        # Show message box or notification
        filename = Path(file_path).name
        
        # Don't show if active workspace directory is inside downloads or something
        reply = QMessageBox.question(self, "检测到新文件下载 📥", 
                                     f"系统检测到新下载的文件:\n'{filename}'\n\n"
                                     f"是否立即将其导入 00_Inbox 收集箱并运行文件规范重命名和标签分类？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                                     
        if reply == QMessageBox.Yes:
            # Move file to 00_Inbox
            inbox_dir = Path(config.workspace_dir) / "00_Inbox"
            inbox_dir.mkdir(parents=True, exist_ok=True)
            
            dest = inbox_dir / filename
            counter = 1
            while dest.exists():
                stem = Path(file_path).stem
                ext = Path(file_path).suffix
                dest = inbox_dir / f"{stem}_{counter}{ext}"
                counter += 1
                
            try:
                import shutil
                shutil.move(file_path, str(dest))
                
                # Toast notification
                self.tray_icon.showMessage(
                    "文件导入成功",
                    f"已成功将 '{filename}' 导入收集箱！",
                    QSystemTrayIcon.Information,
                    3000
                )
                
                # Switch tab to Inbox
                self.switch_tab(1)
                
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"无法导入文件:\n{str(e)}")

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use custom or fallback standard folder icon for tray
        icon_path = Path(__file__).parent.parent / "app_icon.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("电脑文档规范分类与管理系统")
        self.tray_icon.show()

    def show_first_run_welcome(self):
        ws_dir = config.workspace_dir
        msg = (
            "👋 <b>欢迎使用电脑文档分类与管理系统！</b><br><br>"
            "检测到您是第一次启动本软件，系统已为您自动初始化并创建了符合规范的专属工作空间（Workspace）以及 12 个日常分类标准的文件夹：<br>"
            f"<font color='#6366F1'><b>👉 {ws_dir}</b></font><br><br>"
            "<b>💡 快速上手整理建议：</b><br>"
            "1. 可将您浏览器下载目录中的文件、或桌面堆积的杂乱文件，移动进 <b>00_Inbox（收集箱）</b> 中。<br>"
            "2. 在左侧切换至 <b>📥 智能收集箱</b> 面板，体验自动根据规范模板改名、勾选中文分类标签、一键物理归档分流！<br>"
            "3. 建议在 <b>⚙️ 软件参数设置</b> 中配置您所习惯的常用路径与自定义标签字典。<br><br>"
            "现在，开启您的高效知识管理与备份之旅吧！"
        )
        # Create RichText QMessageBox
        box = QMessageBox(self)
        box.setWindowTitle("🎉 首次运行欢迎与规范初始化成功！")
        box.setText(msg)
        box.setTextFormat(Qt.RichText)
        box.setIcon(QMessageBox.Information)
        box.setStyleSheet(self.styleSheet()) # Inherit styles
        box.exec()

    def closeEvent(self, event):
        # Clean up background watcher threads on exit
        if self.watcher_thread:
            self.watcher_thread.stop()
        event.accept()

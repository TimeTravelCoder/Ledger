import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QFrame, 
                             QMessageBox, QSystemTrayIcon, QStyle)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QSize
from PySide6.QtGui import QIcon
from config import config
from ui.icon_utils import line_icon
from ui.styles import get_stylesheet
from ui.toast import ToastManager

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
        self.sidebar_collapsed = False
        self.init_ui()
        self.setup_downloads_watcher()
        
        # If first run, trigger the welcome popup after rendering
        if self.is_first_run:
            QTimer.singleShot(600, self.show_first_run_welcome)

    def init_ui(self):
        self.setWindowTitle("Ledger")
        self.resize(1150, 750)
        self.setMinimumSize(600, 400)  # Allow resizing with reasonable minimum
        
        self.app_icon = self.load_app_icon()
        if not self.app_icon.isNull():
            self.setWindowIcon(self.app_icon)
        
        # Enforce dark or light style sheet based on config
        self.setStyleSheet(get_stylesheet(config.theme))

        # Main Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.toast_manager = ToastManager(self)

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
        
        self.sidebar_logo_lbl = QLabel()
        self.sidebar_logo_lbl.setFixedSize(26, 26)
        # Pixmap will be set dynamically in refresh_nav_icons() based on active theme
        title_container.addWidget(self.sidebar_logo_lbl)
        
        self.sidebar_title_lbl = QLabel("Ledger")
        self.sidebar_title_lbl.setObjectName("SidebarTitle")
        title_container.addWidget(self.sidebar_title_lbl, 1)
        sidebar_layout.addLayout(title_container)

        # Navigation Buttons
        self.nav_buttons = []
        self.btn_dash = self.create_nav_button("控制面板", 0, "dashboard")
        self.btn_inbox = self.create_nav_button("智能收集箱", 1, "inbox")
        self.btn_ws = self.create_nav_button("工作空间浏览器", 2, "workspace")
        self.btn_backup = self.create_nav_button("3-2-1 备份卫士", 3, "backup")
        self.btn_settings = self.create_nav_button("软件参数设置", 4, "settings")

        for btn in [self.btn_dash, self.btn_inbox, self.btn_ws, self.btn_backup, self.btn_settings]:
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Set default active nav button
        self.btn_dash.setChecked(True)
        self.refresh_nav_icons()

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

    def load_app_icon(self):
        root = Path(__file__).parent.parent
        for filename in ("app_icon.ico", "app_icon.png"):
            icon_path = root / filename
            if icon_path.exists():
                return QIcon(str(icon_path))
        return self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)

    def create_nav_button(self, text, index, icon_name):
        btn = QPushButton(text)
        btn.setObjectName("SidebarBtn")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setProperty("nav_label", text)
        btn.setProperty("icon_name", icon_name)  # Store icon name for dynamic theme coloring
        btn.setToolTip(text)
        btn.setIconSize(QSize(18, 18))
        btn.clicked.connect(lambda: self.switch_tab(index))
        return btn

    def refresh_nav_icons(self):
        # Determine unselected icon color and logo color based on current theme
        if config.theme == "dark":
            unselected_color = "#AAD9F2"
            logo_color = "#0A84B1"
        elif config.theme == "zhongguose":
            unselected_color = "#4A6E56"
            logo_color = "#127A60"
        else:
            unselected_color = "#475569"
            logo_color = "#4F46E5"
            
        selected_color = "#FFFFFF"  # Pure white on selected solid backgrounds
        
        # Update logo icon dynamically to match the current theme's accent color
        self.sidebar_logo_lbl.setPixmap(line_icon("logo", color=logo_color, size=26).pixmap(26, 26))
        
        for btn in self.nav_buttons:
            icon_name = btn.property("icon_name")
            if not icon_name:
                continue
            is_active = btn.isChecked()
            color = selected_color if is_active else unselected_color
            btn.setIcon(line_icon(icon_name, color=color, size=18))

    def switch_tab(self, index):
        self.content_stack.setCurrentIndex(index)
        # Sync checked states of sidebar buttons (needed if switched programmatically)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            
        # Dynamically refresh nav icons to swap selected/unselected styles instantly
        self.refresh_nav_icons()
            
        # Special refreshes on tab activation
        if index == 0:
            self.view_dashboard.refresh_data()
        elif index == 1:
            self.view_inbox.scan_inbox()
        elif index == 2:
            self.view_workspace.apply_content_responsive()
            self.view_workspace.run_search()
        elif index == 3:
            self.view_backup.refresh_history()

    def toggle_theme(self):
        if config.theme == "dark":
            new_theme = "light"
        elif config.theme == "light":
            new_theme = "zhongguose"
        else:
            new_theme = "dark"
        config.theme = new_theme
        config.save()
        
        # Apply style sheet globally
        self.setStyleSheet(get_stylesheet(config.theme))
        
        # Update sub-components if necessary (e.g. refresh UI states)
        self.update_theme_btn_text()
        self.refresh_nav_icons()
        self.refresh_all_views()

    def show_toast(self, message, title="", level="info", duration=3200):
        if hasattr(self, "toast_manager"):
            self.toast_manager.show_toast(message=message, title=title, level=level, duration=duration)

    def update_theme_btn_text(self):
        if config.theme == "dark":
            self.btn_theme_toggle.setText("切换浅色模式")
            theme_icon_color = "#AAD9F2"
        elif config.theme == "light":
            self.btn_theme_toggle.setText("切换幽竹清溪")
            theme_icon_color = "#475569"
        else:
            self.btn_theme_toggle.setText("切换深色模式")
            theme_icon_color = "#4A6E56"
            
        self.btn_theme_toggle.setIcon(line_icon("theme", color=theme_icon_color, size=16))
        self.btn_theme_toggle.setIconSize(QSize(16, 16))
        theme_text = self.btn_theme_toggle.text()
        self.btn_theme_toggle.setProperty("expanded_text", theme_text)
        self.btn_theme_toggle.setToolTip(theme_text)
        if self.sidebar_collapsed:
            self.btn_theme_toggle.setText("")

    @Slot()
    def refresh_all_views(self):
        # Prevent database locks or recursive refreshes by executing quietly
        self.view_dashboard.refresh_data()
        self.view_inbox.scan_inbox()
        self.view_inbox.refresh_preset_combo()
        self.view_inbox.build_tags_checklist()
        self.view_inbox.refresh_directory_combo()
        self.view_workspace.setup_models() # Relink model if path changed
        self.view_workspace.refresh_tags_cloud()
        self.view_workspace.refresh_status_combo()
        self.view_workspace.refresh_rule_hint_for_current_selection()
        self.view_workspace.run_search()
        self.view_backup.refresh_history()
        self.refresh_nav_icons()

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
        inbox_name = config.get_inbox_name()
        reply = QMessageBox.question(self, "检测到新文件下载",
                                     f"系统检测到新下载的文件:\n'{filename}'\n\n"
                                     f"是否立即将其导入 {inbox_name} 收集箱并运行文件规范重命名和标签分类？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                                     
        if reply == QMessageBox.Yes:
            # Move file to active inbox
            inbox_dir = Path(config.workspace_dir) / inbox_name
            inbox_dir.mkdir(parents=True, exist_ok=True)
            
            dest = inbox_dir / filename
            try:
                import shutil
                from file_manager import FileManager
                FileManager.move_replace(file_path, dest)
                
                self.show_toast(
                    message=f"'{filename}' 已导入收集箱。",
                    title="导入成功",
                    level="success",
                    duration=3200,
                )
                
                # Switch tab to Inbox
                self.switch_tab(1)
                
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"无法导入文件:\n{str(e)}")

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        self.tray_icon.setIcon(line_icon("workspace", "#D1FFFF", 16))
        self.tray_icon.setToolTip("Ledger - 电脑文档规范分类与管理系统")
        self.tray_icon.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_responsive_layout()
        if hasattr(self, "view_workspace"):
            self.view_workspace.apply_content_responsive()

    def apply_responsive_layout(self):
        width = self.width()
        should_collapse = width < 1100
        if should_collapse == self.sidebar_collapsed:
            return
        self.sidebar_collapsed = should_collapse
        self.apply_sidebar_mode(should_collapse)

    def apply_sidebar_mode(self, collapsed):
        self.sidebar.setVisible(True)
        self.sidebar.setFixedWidth(74 if collapsed else 220)
        self.sidebar_title_lbl.setVisible(not collapsed)

        for btn in self.nav_buttons:
            label = btn.property("nav_label") or btn.toolTip() or btn.text()
            btn.setText("" if collapsed else label)
            btn.setToolTip(label)
            btn.setProperty("compact", collapsed)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        theme_text = self.btn_theme_toggle.property("expanded_text") or self.btn_theme_toggle.toolTip()
        self.btn_theme_toggle.setText("" if collapsed else theme_text)
        self.btn_theme_toggle.setToolTip(theme_text)
        self.btn_theme_toggle.setProperty("compact", collapsed)
        self.btn_theme_toggle.style().unpolish(self.btn_theme_toggle)
        self.btn_theme_toggle.style().polish(self.btn_theme_toggle)

    def show_first_run_welcome(self):
        ws_dir = config.workspace_dir
        msg = (
            "<b>欢迎使用 Ledger 电脑文档规范分类与管理系统！</b><br><br>"
            "检测到您是第一次启动本软件，系统已为您自动初始化并创建了符合规范的专属工作空间（Workspace）以及 12 个日常分类标准的文件夹：<br>"
            f"<font color='#6366F1'><b>{ws_dir}</b></font><br><br>"
            "<b>快速上手整理建议：</b><br>"
            f"1. 可将您浏览器下载目录中的文件、或桌面堆积的杂乱文件，移动进 <b>{config.get_inbox_name()}（收集箱）</b> 中。<br>"
            "2. 在左侧切换至 <b>智能收集箱</b> 面板，体验自动根据规范模板改名、勾选中文分类标签、一键物理归档分流！<br>"
            "3. 建议在 <b>软件参数设置</b> 中配置您所习惯的常用路径与自定义标签字典。<br><br>"
            "现在，开启您的高效知识管理与备份之旅吧！"
        )
        # Create RichText QMessageBox
        box = QMessageBox(self)
        box.setWindowTitle("首次运行欢迎与规范初始化成功")
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

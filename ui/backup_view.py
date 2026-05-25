import os
import datetime
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QFrame,
                             QProgressBar, QTextEdit, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFileDialog, QMessageBox, QScrollArea)
from PySide6.QtCore import Qt, Signal, QSize, QThread
from config import config
from db import db
from file_manager import FileManager
from ui.icon_utils import decorate_table, line_icon
from ui.toast import show_toast

class BackupWorker(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, backup_type, workspace_records=None):
        super().__init__()
        self.backup_type = backup_type
        self.workspace_records = workspace_records

    def run(self):
        try:
            success, msg = FileManager.perform_backup(self.backup_type, self.workspace_records)
            self.finished_signal.emit(success, msg)
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class BackupView(QWidget):
    refresh_other_views_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.backup_worker = None
        self.init_ui()

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Modern scroll area to handle different window heights beautifully
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")
        scroll_content.setStyleSheet("#ScrollContent { background: transparent; }")

        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(15)

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)

        # 1. Header
        header = QLabel("3-2-1 备份卫士")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(header)

        # 2. 3-2-1 Guideline Explanation Card
        guide_card = QFrame()
        guide_card.setObjectName("CardPanel")
        guide_layout = QVBoxLayout(guide_card)
        guide_layout.setContentsMargins(15, 12, 15, 12)
        guide_layout.setSpacing(6)

        g_title = QLabel("什么是 3-2-1 备份原则？")
        g_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #6366F1;")
        guide_layout.addWidget(g_title)

        g_desc = QLabel(
            "数据安全重于泰山！规范要求对于核心资料遵循以下准则：\n"
            "• <b>3 份数据</b>: 本地工作主数据 + 2个独立备份副本。\n"
            "• <b>2 种介质</b>: 存储在不同的介质上（例如本地SSD硬盘 + 外部移动硬盘/U盘）。\n"
            "• <b>1 份异地</b>: 至少1份备份托管在异地或云端（例如利用 OneDrive/Google Drive 目录同步）。"
        )
        g_desc.setTextFormat(Qt.RichText)
        g_desc.setStyleSheet("color: #94A3B8; font-size: 12px; line-height: 1.6;")
        g_desc.setWordWrap(True)
        guide_layout.addWidget(g_desc)
        main_layout.addWidget(guide_card)

        # 3. Path Configurations
        config_card = QFrame()
        config_card.setObjectName("CardPanel")
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(15, 15, 15, 15)
        config_layout.setSpacing(12)

        config_title = QLabel("备份路径配置")
        config_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        config_layout.addWidget(config_title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Disk backup field
        grid.addWidget(QLabel("外部介质备份路径:"), 0, 0)
        self.input_disk_path = QLineEdit(config.backup_disk_dir)
        self.input_disk_path.setPlaceholderText("选择您的移动硬盘、U盘备份文件夹路径...")
        grid.addWidget(self.input_disk_path, 0, 1)
        self.btn_browse_disk = QPushButton("浏览...")
        self.btn_browse_disk.setIcon(line_icon("folder", size=16))
        self.btn_browse_disk.setIconSize(QSize(16, 16))
        self.btn_browse_disk.clicked.connect(self.browse_disk_path)
        grid.addWidget(self.btn_browse_disk, 0, 2)

        # Cloud backup field
        grid.addWidget(QLabel("云端同步目录路径:"), 1, 0)
        self.input_cloud_path = QLineEdit(config.backup_cloud_dir)
        self.input_cloud_path.setPlaceholderText("选择您的 OneDrive 或 iCloud/Google Drive 映射文件夹...")
        grid.addWidget(self.input_cloud_path, 1, 1)
        self.btn_browse_cloud = QPushButton("浏览...")
        self.btn_browse_cloud.setIcon(line_icon("folder", size=16))
        self.btn_browse_cloud.setIconSize(QSize(16, 16))
        self.btn_browse_cloud.clicked.connect(self.browse_cloud_path)
        grid.addWidget(self.btn_browse_cloud, 1, 2)

        config_layout.addLayout(grid)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_run_disk = QPushButton("运行硬盘增量备份")
        self.btn_run_disk.setObjectName("PrimaryBtn")
        self.btn_run_disk.setIcon(line_icon("backup", "#FFFFFF", 16))
        self.btn_run_disk.setIconSize(QSize(16, 16))
        self.btn_run_disk.clicked.connect(lambda: self.run_backup("disk"))
        btn_layout.addWidget(self.btn_run_disk)

        self.btn_run_cloud = QPushButton("运行云端增量备份")
        self.btn_run_cloud.setObjectName("SuccessBtn")
        self.btn_run_cloud.setIcon(line_icon("backup", "#FFFFFF", 16))
        self.btn_run_cloud.setIconSize(QSize(16, 16))
        self.btn_run_cloud.clicked.connect(lambda: self.run_backup("cloud"))
        btn_layout.addWidget(self.btn_run_cloud)

        config_layout.addLayout(btn_layout)
        main_layout.addWidget(config_card)

        # 4. Progress and logs
        log_card = QFrame()
        log_card.setObjectName("CardPanel")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(15, 15, 15, 15)
        log_layout.setSpacing(8)

        log_title = QLabel("备份控制台输出 & 进度")
        log_title.setObjectName("CardTitle")
        log_layout.addWidget(log_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        log_layout.addWidget(self.progress_bar)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFixedHeight(120)
        self.console_output.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px;")
        log_layout.addWidget(self.console_output)

        main_layout.addWidget(log_card)

        # 5. History Table
        hist_card = QFrame()
        hist_card.setObjectName("CardPanel")
        hist_layout = QVBoxLayout(hist_card)
        hist_layout.setContentsMargins(15, 15, 15, 15)
        hist_layout.setSpacing(8)

        hist_title = QLabel("最近备份历史记录")
        hist_title.setObjectName("CardTitle")
        hist_layout.addWidget(hist_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["备份时间", "类型", "文件数", "容量", "状态"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setFixedHeight(150)
        decorate_table(self.history_table, row_height=34, icon_size=20)
        hist_layout.addWidget(self.history_table)

        main_layout.addWidget(hist_card)

        self.refresh_history()

    def browse_disk_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择移动硬盘备份目录", config.backup_disk_dir)
        if dir_path:
            # Enforce Loop Backup Prevention
            try:
                ws_root = Path(config.workspace_dir).resolve()
                selected = Path(dir_path).resolve()
                if selected == ws_root or selected.is_relative_to(ws_root):
                    QMessageBox.warning(self, "路径无效", "安全拦截：备份目录不能选择在工作空间目录内部，否则会导致循环备份！")
                    return
            except Exception:
                pass

            self.input_disk_path.setText(dir_path)
            config.backup_disk_dir = dir_path
            config.save()
            self.refresh_other_views_signal.emit()

    def browse_cloud_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择云盘映射备份目录", config.backup_cloud_dir)
        if dir_path:
            # Enforce Loop Backup Prevention
            try:
                ws_root = Path(config.workspace_dir).resolve()
                selected = Path(dir_path).resolve()
                if selected == ws_root or selected.is_relative_to(ws_root):
                    QMessageBox.warning(self, "路径无效", "安全拦截：备份目录不能选择在工作空间目录内部，否则会导致循环备份！")
                    return
            except Exception:
                pass

            self.input_cloud_path.setText(dir_path)
            config.backup_cloud_dir = dir_path
            config.save()
            self.refresh_other_views_signal.emit()

    def run_backup(self, backup_type):
        # 1. Update config directories first
        if backup_type == "disk":
            config.backup_disk_dir = self.input_disk_path.text().strip()
        else:
            config.backup_cloud_dir = self.input_cloud_path.text().strip()

        # Enforce Loop Backup Prevention on manual edits
        try:
            ws_root = Path(config.workspace_dir).resolve()
            if backup_type == "disk" and config.backup_disk_dir:
                selected = Path(config.backup_disk_dir).resolve()
                if selected == ws_root or selected.is_relative_to(ws_root):
                    QMessageBox.warning(self, "备份失败", "安全拦截：外部介质备份路径不能设定在工作空间内部，防止循环备份！")
                    return
            if backup_type == "cloud" and config.backup_cloud_dir:
                selected = Path(config.backup_cloud_dir).resolve()
                if selected == ws_root or selected.is_relative_to(ws_root):
                    QMessageBox.warning(self, "备份失败", "安全拦截：云端同步备份路径不能设定在工作空间内部，防止循环备份！")
                    return
        except Exception:
            pass

        config.save()

        # Disable buttons to prevent double click race conditions
        self.btn_run_disk.setEnabled(False)
        self.btn_run_cloud.setEnabled(False)

        # 2. Start backup Worker thread
        label = "移动硬盘" if backup_type == "disk" else "云端同步盘"
        self.progress_bar.setValue(10) # 10% on startup
        self.console_output.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 启动增量镜像备份至 '{label}' (后台异步处理中)...")

        # Pass None to force BackupWorker thread to query dynamically after scan_workspace_files completes
        self.backup_worker = BackupWorker(backup_type, None)
        self.backup_worker.finished_signal.connect(lambda success, msg: self.on_backup_finished(backup_type, success, msg))
        self.backup_worker.start()

    def on_backup_finished(self, backup_type, success, msg):
        label = "移动硬盘" if backup_type == "disk" else "云端同步盘"
        self.progress_bar.setValue(100)

        if success:
            self.console_output.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 备份完成！{msg}")
            show_toast(self, f"{label}增量备份已完成。", title="备份成功", level="success", duration=3600)
        else:
            self.console_output.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 备份失败！原因: {msg}")
            QMessageBox.critical(self, "备份失败", f"备份未成功运行！\n原因: {msg}")

        # Re-enable buttons and reset worker reference
        self.btn_run_disk.setEnabled(True)
        self.btn_run_cloud.setEnabled(True)
        self.backup_worker = None

        # Refresh
        self.refresh_history()
        self.refresh_other_views_signal.emit()

    def refresh_history(self):
        history = db.get_backup_history(limit=10)
        self.history_table.setRowCount(0)

        for i, h in enumerate(history):
            self.history_table.insertRow(i)

            is_disk_backup = h["backup_type"] == "disk"
            b_type = "外部介质" if is_disk_backup else "云盘同步"

            sz = h["bytes_copied"]
            sz_str = f"{sz / 1024:.1f} KB" if sz < 1024*1024 else f"{sz / (1024*1024):.1f} MB"

            item_time = QTableWidgetItem(h["timestamp"])
            item_type = QTableWidgetItem(b_type)
            item_type.setIcon(line_icon("backup", size=16))
            item_files = QTableWidgetItem(str(h["files_copied"]))
            item_size = QTableWidgetItem(sz_str)
            is_success = h["status"] == "success"
            item_status = QTableWidgetItem("成功" if is_success else f"失败 ({h['status']})")
            item_status.setIcon(line_icon("success" if is_success else "warning", size=16))

            item_time.setFlags(item_time.flags() & ~Qt.ItemIsEditable)
            item_type.setFlags(item_type.flags() & ~Qt.ItemIsEditable)
            item_files.setFlags(item_files.flags() & ~Qt.ItemIsEditable)
            item_size.setFlags(item_size.flags() & ~Qt.ItemIsEditable)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)

            self.history_table.setItem(i, 0, item_time)
            self.history_table.setItem(i, 1, item_type)
            self.history_table.setItem(i, 2, item_files)
            self.history_table.setItem(i, 3, item_size)
            self.history_table.setItem(i, 4, item_status)

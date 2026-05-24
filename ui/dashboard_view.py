import os
import datetime
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QMessageBox, QScrollArea, QProgressBar)
from PySide6.QtCore import Qt, Signal, QSize
from config import config
from db import db
from file_manager import FileManager
from ui.icon_utils import decorate_table, file_type_icon, line_icon

def display_name(tag):
    return tag[1:] if str(tag).startswith("#") else str(tag)

class DashboardView(QWidget):
    # Signal emitted when user wants to switch to the Inbox tab (for quick cleanup)
    switch_to_inbox_signal = Signal()
    refresh_other_views_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
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
        main_layout.setSpacing(20)
        
        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)

        # 1. Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel("控制面板 / Dashboard")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        self.refresh_btn = QPushButton("刷新数据")
        self.refresh_btn.setObjectName("PrimaryBtn")
        self.refresh_btn.setIcon(line_icon("refresh", "#FFFFFF", 16))
        self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        header_layout.addWidget(self.refresh_btn, 0, Qt.AlignRight)
        
        main_layout.addLayout(header_layout)

        # 2. Stats Grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)

        self.card_total_files = self.create_stat_card("文件总数", "0", "统计当前工作空间内的所有文件", "file")
        self.card_total_size = self.create_stat_card("存储容量", "0.00 MB", "工作空间占用的磁盘空间大小", "workspace")
        self.card_unorganized = self.create_stat_card("收集箱未整理", "0", "00_Inbox 目录中等待整理的文件", "inbox")
        self.card_tags_count = self.create_stat_card("使用标签数", "0", "当前已在文件上打上的标签总数", "tag")
        self.card_recent_count = self.create_stat_card("近7天整理量", "0", "最近 7 天内更新或整理过的文件数", "dashboard")

        stats_grid.addWidget(self.card_total_files, 0, 0)
        stats_grid.addWidget(self.card_total_size, 0, 1)
        stats_grid.addWidget(self.card_unorganized, 0, 2)
        stats_grid.addWidget(self.card_tags_count, 0, 3)
        stats_grid.addWidget(self.card_recent_count, 1, 0)

        main_layout.addLayout(stats_grid)

        insight_strip = QFrame()
        insight_strip.setObjectName("InsightStrip")
        insight_layout = QHBoxLayout(insight_strip)
        insight_layout.setContentsMargins(12, 8, 12, 8)
        insight_layout.setSpacing(10)
        self.pending_chip = QLabel("待处理: --")
        self.coverage_chip = QLabel("标签覆盖: --")
        self.recent_chip = QLabel("近7天整理: --")
        for chip in [self.pending_chip, self.coverage_chip, self.recent_chip]:
            chip.setObjectName("InsightChip")
            insight_layout.addWidget(chip)
        insight_layout.addStretch()
        main_layout.addWidget(insight_strip)

        # 3. Middle Section: Desktop Cleanliness & Backup health
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(20)

        # Desktop Cleanliness Card
        self.desktop_card = QFrame()
        self.desktop_card.setObjectName("CardPanel")
        desktop_layout = QVBoxLayout(self.desktop_card)
        desktop_layout.setSpacing(10)
        desktop_layout.setContentsMargins(15, 15, 15, 15)

        desktop_title = QLabel("桌面整理状态 (桌面规范建议 ≤ 10个文件)")
        desktop_title.setObjectName("CardTitle")
        desktop_layout.addWidget(desktop_title)

        self.desktop_status_lbl = QLabel("正在扫描桌面...")
        self.desktop_status_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        desktop_layout.addWidget(self.desktop_status_lbl)

        self.desktop_desc_lbl = QLabel("仅保留快捷方式、待处理文件和临时文件。")
        self.desktop_desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        desktop_layout.addWidget(self.desktop_desc_lbl)

        desktop_btn_layout = QHBoxLayout()
        self.clean_desktop_btn = QPushButton("一键导入收集箱")
        self.clean_desktop_btn.setObjectName("SuccessBtn")
        self.clean_desktop_btn.setIcon(line_icon("inbox", "#FFFFFF", 16))
        self.clean_desktop_btn.setIconSize(QSize(16, 16))
        self.clean_desktop_btn.clicked.connect(self.clean_desktop)
        desktop_btn_layout.addWidget(self.clean_desktop_btn)
        
        self.go_to_inbox_btn = QPushButton("前往收集箱")
        self.go_to_inbox_btn.setIcon(line_icon("move", size=16))
        self.go_to_inbox_btn.setIconSize(QSize(16, 16))
        self.go_to_inbox_btn.clicked.connect(lambda: self.switch_to_inbox_signal.emit())
        desktop_btn_layout.addWidget(self.go_to_inbox_btn)
        desktop_layout.addLayout(desktop_btn_layout)

        middle_layout.addWidget(self.desktop_card, 1)

        # 3-2-1 Backup Card
        self.backup_card = QFrame()
        self.backup_card.setObjectName("CardPanel")
        backup_layout = QVBoxLayout(self.backup_card)
        backup_layout.setSpacing(10)
        backup_layout.setContentsMargins(15, 15, 15, 15)

        backup_title = QLabel("3-2-1 备份健康度")
        backup_title.setObjectName("CardTitle")
        backup_layout.addWidget(backup_title)

        self.backup_score_lbl = QLabel("备份分值: 0/100")
        self.backup_score_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        backup_layout.addWidget(self.backup_score_lbl)

        self.backup_ssd_status = QLabel("1. 主数据 (本地 SSD): 已就绪")
        self.backup_ssd_status.setStyleSheet("font-size: 12px;")
        backup_layout.addWidget(self.backup_ssd_status)

        self.backup_disk_status = QLabel("2. 外部介质 (移动硬盘): 未配置")
        self.backup_disk_status.setStyleSheet("font-size: 12px;")
        backup_layout.addWidget(self.backup_disk_status)

        self.backup_cloud_status = QLabel("3. 异地备份 (云盘同步): 未配置")
        self.backup_cloud_status.setStyleSheet("font-size: 12px;")
        backup_layout.addWidget(self.backup_cloud_status)

        middle_layout.addWidget(self.backup_card, 1)

        main_layout.addLayout(middle_layout)

        # 4. Recent Files List
        recent_card = QFrame()
        recent_card.setObjectName("CardPanel")
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(15, 15, 15, 15)
        recent_layout.setSpacing(10)

        recent_title = QLabel("最近修改的文档 (5个)")
        recent_title.setObjectName("CardTitle")
        recent_layout.addWidget(recent_title)

        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(4)
        self.recent_table.setHorizontalHeaderLabels(["名称", "位置", "大小", "修改时间"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent_table.setFixedHeight(180)
        decorate_table(self.recent_table, row_height=34, icon_size=22)
        recent_layout.addWidget(self.recent_table)

        self.tags_summary = QLabel("标签分布: --")
        self.tags_summary.setWordWrap(True)
        self.tags_summary.setStyleSheet("color: #94A3B8; font-size: 11px;")
        recent_layout.addWidget(self.tags_summary)

        self.tag_progress = QProgressBar()
        self.tag_progress.setRange(0, 100)
        self.tag_progress.setValue(0)
        self.tag_progress.setFormat("标签覆盖度")
        recent_layout.addWidget(self.tag_progress)

        self.recent_progress = QProgressBar()
        self.recent_progress.setRange(0, 100)
        self.recent_progress.setValue(0)
        self.recent_progress.setFormat("近7天整理进度")
        recent_layout.addWidget(self.recent_progress)

        self.bar_title = QLabel("标签概览")
        self.bar_title.setObjectName("CardTitle")
        recent_layout.addWidget(self.bar_title)
        self.bar_container = QFrame()
        self.bar_container_layout = QVBoxLayout(self.bar_container)
        self.bar_container_layout.setContentsMargins(0, 0, 0, 0)
        self.bar_container_layout.setSpacing(6)
        recent_layout.addWidget(self.bar_container)

        main_layout.addWidget(recent_card)

        self.refresh_data()

    def create_stat_card(self, title, default_val, description, icon_name):
        card = QFrame()
        card.setObjectName("CardPanel")
        card.setMinimumHeight(100)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(15, 12, 15, 12)
        
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setObjectName("MetricIcon")
        icon_lbl.setPixmap(line_icon(icon_name, size=18).pixmap(18, 18))

        title_lbl = QLabel(title)
        title_lbl.setObjectName("CardTitle")
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl, 1)
        
        val_lbl = QLabel(default_val)
        val_lbl.setObjectName("CardValue")
        
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        desc_lbl.setWordWrap(True)
        
        layout.addLayout(title_row)
        layout.addWidget(val_lbl)
        layout.addWidget(desc_lbl)
        
        # Save reference to modify values later
        card.value_label = val_lbl
        return card

    def refresh_data(self):
        # 1. Trigger File Manager disk sync first
        FileManager.scan_workspace_files()

        # 2. Query stats from DB
        all_files = db.search_files()
        total_count = len(all_files)
        total_bytes = sum(f["file_size"] for f in all_files)
        
        # Convert bytes to MB/GB
        if total_bytes > 1024*1024*1024:
            size_str = f"{total_bytes / (1024*1024*1024):.2f} GB"
        else:
            size_str = f"{total_bytes / (1024*1024):.2f} MB"

        inbox_name = config.get_inbox_name()
        inbox_files = db.search_files(query=inbox_name + "/")
        inbox_count = len(inbox_files)
        
        # If both inboxes exist, combine their counts
        other_inbox = "00Inbox" if inbox_name == "00收集箱" else "00收集箱"
        other_path = Path(config.workspace_dir) / other_inbox
        if other_path.exists() and other_path.is_dir():
            other_files = db.search_files(query=other_inbox + "/")
            inbox_count += len(other_files)

        # Count tags
        unique_tags = set()
        for f in all_files:
            if f["tags"]:
                for t in f["tags"].split(","):
                    if t.strip():
                        unique_tags.add(t.strip())
        tags_count = len(unique_tags)
        recent_files = db.get_recent_files(days=7)
        recent_count = len(recent_files)
        tag_distribution = db.get_tag_distribution()
        top_tags = sorted(tag_distribution.items(), key=lambda item: item[1], reverse=True)[:5]
        tag_summary_text = "、".join(f"{tag}({count})" for tag, count in top_tags) if top_tags else "--"
        tag_coverage = min(100, int((tags_count / max(1, total_count)) * 100))
        recent_progress = min(100, int((recent_count / max(1, total_count)) * 100))

        # Update card values
        self.card_total_files.value_label.setText(str(total_count))
        self.card_total_size.value_label.setText(size_str)
        self.card_unorganized.value_label.setText(str(inbox_count))
        self.card_tags_count.value_label.setText(str(tags_count))
        self.card_recent_count.value_label.setText(str(recent_count))
        self.tags_summary.setText(f"标签分布: {tag_summary_text}")
        self.tag_progress.setValue(tag_coverage)
        self.recent_progress.setValue(recent_progress)
        self.pending_chip.setText(f"待处理: {inbox_count} 个")
        self.coverage_chip.setText(f"标签覆盖: {tag_coverage}%")
        self.recent_chip.setText(f"近7天整理: {recent_count} 个")
        self.render_tag_bars(top_tags)

        # 3. Check Desktop Cleanliness
        desktop_files = FileManager.scan_desktop_files()
        desktop_summary = FileManager.scan_desktop_summary()
        desktop_count = len(desktop_files)
        if desktop_count <= 10:
            self.desktop_status_lbl.setText(f"优秀 (桌面有 {desktop_count} 个文件)")
            self.desktop_status_lbl.setStyleSheet("color: #10B981; font-size: 16px; font-weight: bold;")
            self.desktop_desc_lbl.setText(
                f"普通文件 {desktop_summary['normal_files']} 个，文件夹 {desktop_summary['folders']} 个，快捷方式 {desktop_summary['shortcuts']} 个。"
            )
            self.clean_desktop_btn.setEnabled(True)
        else:
            self.desktop_status_lbl.setText(f"警告: 建议整理 (有 {desktop_count} 个文件)")
            self.desktop_status_lbl.setStyleSheet("color: #EF4444; font-size: 16px; font-weight: bold;")
            self.desktop_desc_lbl.setText("桌面文件数已超过规范建议的 10 个！建议立即清理。")
            self.clean_desktop_btn.setEnabled(True)

        # 4. Check 3-2-1 Backup health
        has_disk = bool(config.backup_disk_dir)
        has_cloud = bool(config.backup_cloud_dir)
        
        score = 33
        if has_disk: score += 33
        if has_cloud: score += 34
        
        self.backup_score_lbl.setText(f"备份健康度: {score}/100")
        
        if score == 100:
            self.backup_score_lbl.setStyleSheet("color: #10B981; font-size: 16px; font-weight: bold;")
        elif score >= 66:
            self.backup_score_lbl.setStyleSheet("color: #F59E0B; font-size: 16px; font-weight: bold;")
        else:
            self.backup_score_lbl.setStyleSheet("color: #EF4444; font-size: 16px; font-weight: bold;")

        # Update disk label
        if has_disk:
            # Check if recently backed up
            recent_backups = db.get_backup_history(limit=5)
            disk_ok = any(b["backup_type"] == "disk" and b["status"] == "success" for b in recent_backups)
            if disk_ok:
                self.backup_disk_status.setText("2. 外部介质 (移动硬盘): 已配置并备份")
                self.backup_disk_status.setStyleSheet("color: #10B981; font-size: 12px;")
            else:
                self.backup_disk_status.setText("2. 外部介质 (移动硬盘): 已配置但尚未运行备份")
                self.backup_disk_status.setStyleSheet("color: #F59E0B; font-size: 12px;")
        else:
            self.backup_disk_status.setText("2. 外部介质 (移动硬盘): 未配置")
            self.backup_disk_status.setStyleSheet("color: #EF4444; font-size: 12px;")

        # Update cloud label
        if has_cloud:
            cloud_ok = any(b["backup_type"] == "cloud" and b["status"] == "success" for b in recent_backups)
            if cloud_ok:
                self.backup_cloud_status.setText("3. 异地备份 (云盘同步): 已配置并备份")
                self.backup_cloud_status.setStyleSheet("color: #10B981; font-size: 12px;")
            else:
                self.backup_cloud_status.setText("3. 异地备份 (云盘同步): 已配置但尚未运行备份")
                self.backup_cloud_status.setStyleSheet("color: #F59E0B; font-size: 12px;")
        else:
            self.backup_cloud_status.setText("3. 异地备份 (云盘同步): 未配置")
            self.backup_cloud_status.setStyleSheet("color: #EF4444; font-size: 12px;")

        # 5. Populate Recent Files
        self.populate_recent_table(all_files)

    def populate_recent_table(self, all_files):
        # Sort files by modified time descending
        sorted_files = sorted(all_files, key=lambda x: x["modified_time"], reverse=True)[:5]
        
        self.recent_table.setRowCount(0)
        for i, f in enumerate(sorted_files):
            self.recent_table.insertRow(i)
            
            # File size readable
            sz = f["file_size"]
            sz_str = f"{sz / 1024:.1f} KB" if sz < 1024*1024 else f"{sz / (1024*1024):.1f} MB"
            
            # Date readable
            mtime = datetime.datetime.fromtimestamp(f["modified_time"]).strftime("%Y-%m-%d %H:%M:%S")
            
            item_name = QTableWidgetItem(f["filename"])
            item_name.setIcon(file_type_icon(f["filename"]))
            item_path = QTableWidgetItem(f["filepath"])
            item_size = QTableWidgetItem(sz_str)
            item_mtime = QTableWidgetItem(mtime)
            
            # Read-only
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            item_path.setFlags(item_path.flags() & ~Qt.ItemIsEditable)
            item_size.setFlags(item_size.flags() & ~Qt.ItemIsEditable)
            item_mtime.setFlags(item_mtime.flags() & ~Qt.ItemIsEditable)

            self.recent_table.setItem(i, 0, item_name)
            self.recent_table.setItem(i, 1, item_path)
            self.recent_table.setItem(i, 2, item_size)
            self.recent_table.setItem(i, 3, item_mtime)

    def clean_desktop(self):
        summary = FileManager.scan_desktop_summary()
        if summary["normal_files"] == 0:
            QMessageBox.information(
                self, "暂无可导入文件",
                f"桌面当前没有可导入收集箱的普通文件。\n\n"
                f"文件夹: {summary['folders']} 个\n"
                f"快捷方式: {summary['shortcuts']} 个\n"
                f"临时文件: {summary['temporary_files']} 个"
            )
            return

        reply = QMessageBox.question(self, "确认清理", 
                                     "是否确认将桌面上所有的普通文件移动到 00_Inbox 收集箱进行统一整理？\n(桌面快捷方式 .lnk 文件将被忽略)",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            moved, errors = FileManager.clean_desktop_to_inbox()
            if errors:
                error_msg = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n及其他 {len(errors) - 5} 个文件..."
                QMessageBox.warning(self, "清理完成 (部分失败)", f"已成功移动 {moved} 个文件，但部分文件移动失败:\n{error_msg}")
            else:
                QMessageBox.information(self, "清理完成", f"桌面清理成功！已成功移动 {moved} 个文件到收集空间。")
            
            self.refresh_data()
            self.refresh_other_views_signal.emit()

    def on_refresh_clicked(self):
        self.refresh_data()
        self.refresh_other_views_signal.emit()
        
        # Get count and size for message feedback
        all_files = db.search_files()
        total_count = len(all_files)
        total_bytes = sum(f["file_size"] for f in all_files)
        if total_bytes > 1024*1024*1024:
            size_str = f"{total_bytes / (1024*1024*1024):.2f} GB"
        else:
            size_str = f"{total_bytes / (1024*1024):.2f} MB"
            
        QMessageBox.information(
            self, "全量同步成功",
            f"主控制面板与本地磁盘已全量同步自检完成！\n\n"
            f"文件总数: {total_count} 个\n"
            f"空间占用: {size_str}\n\n"
            f"所有其他功能视图已同步刷新！"
        )

    def render_tag_bars(self, tag_items):
        while self.bar_container_layout.count():
            item = self.bar_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not tag_items:
            self.bar_container_layout.addWidget(QLabel("暂无标签数据"))
            return
        total = sum(count for _, count in tag_items) or 1
        for tag, count in tag_items:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            name = QLabel(display_name(tag))
            name.setFixedWidth(90)
            bar = QProgressBar()
            bar.setRange(0, total)
            bar.setValue(count)
            bar.setFormat(str(count))
            row_layout.addWidget(name)
            row_layout.addWidget(bar, 1)
            self.bar_container_layout.addWidget(row)

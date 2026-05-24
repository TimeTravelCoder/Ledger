import os
import datetime
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QMessageBox, QScrollArea, QProgressBar)
from PySide6.QtCore import Qt, Signal, QSize, QRectF, QPointF, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QLinearGradient, QPainterPath
from config import config
from db import db
from file_manager import FileManager
from ui.icon_utils import decorate_table, file_type_icon, line_icon
from ui.toast import show_toast

def display_name(tag):
    return tag[1:] if str(tag).startswith("#") else str(tag)


TAG_COLOR_PALETTE = [
    "#4A6FA6",
    "#1BA784",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#0EA5E9",
    "#14B8A6",
    "#EC4899",
    "#22C55E",
    "#F97316",
]


def tag_color(tag):
    value = str(tag or "").strip().lstrip("#")
    if not value:
        return QColor("#85B3CB")
    index = sum(ord(ch) for ch in value.lower()) % len(TAG_COLOR_PALETTE)
    return QColor(TAG_COLOR_PALETTE[index])


class TagDistributionChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.setMinimumHeight(170)
        self.setMouseTracking(True)
        self.hovered_index = -1
        self.tooltip_pos = QPoint()

    def set_data(self, items):
        self.items = [(tag, display_name(tag), count) for tag, count in items[:6]]
        self.update()

    def mouseMoveEvent(self, event):
        if not self.items:
            super().mouseMoveEvent(event)
            return
        rect = self.rect().adjusted(12, 12, -12, -12)
        row_h = max(20, rect.height() // max(1, len(self.items)))
        
        pos = event.position()
        y = pos.y() - rect.top()
        index = int(y // row_h)
        
        if 0 <= index < len(self.items):
            self.hovered_index = index
            self.tooltip_pos = pos.toPoint()
        else:
            self.hovered_index = -1
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_index = -1
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(12, 12, -12, -12)
        
        theme = config.theme
        is_light = theme in ["light", "zhongguose"]
        text_muted = QColor("#475569") if is_light else QColor("#85B3CB")

        if not self.items:
            painter.setPen(text_muted)
            painter.drawText(rect, Qt.AlignCenter, "暂无标签数据")
            return

        max_count = max(count for _, _, count in self.items) or 1
        row_h = max(20, rect.height() // max(1, len(self.items)))
        for index, (tag, name, count) in enumerate(self.items):
            y = rect.top() + index * row_h + 3
            label_rect = QRectF(rect.left(), y, 86, row_h - 6)
            bar_rect = QRectF(rect.left() + 94, y + 5, rect.width() - 142, row_h - 16)
            color = tag_color(tag)
            
            # Calculate theme-adaptive background track color
            track_color = QColor(0, 0, 0, 13) if is_light else QColor(255, 255, 255, 13)
            
            # Theme-aware text lightness adjustments for charts
            if is_light:
                label_color = color.darker(115)
                count_color = color.darker(130)
            else:
                label_color = color.lighter(140)
                count_color = color.lighter(165)
                
            # Draw label
            painter.setPen(label_color)
            painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignLeft, name[:10])
            
            # Draw background track
            painter.setPen(Qt.NoPen)
            painter.setBrush(track_color)
            painter.drawRoundedRect(bar_rect, 4, 4)
            
            # Draw active bar
            active = QRectF(bar_rect)
            active_w = max(6, bar_rect.width() * count / max_count)
            active.setWidth(active_w)
            
            # If hovered, draw glowing shadow under active bar
            if index == self.hovered_index:
                glow = QPainterPath()
                glow.addRoundedRect(active.adjusted(-2, -2, 2, 2), 5, 5)
                glow_color = QColor(color)
                glow_color.setAlpha(60)
                painter.fillPath(glow, glow_color)
            
            # Gradient fill for active bar
            grad = QLinearGradient(active.left(), active.top(), active.right(), active.top())
            color_start = color
            color_end = QColor(color)
            if is_light:
                color_end = color_end.lighter(110)
            else:
                color_end = color_end.darker(110)
            grad.setColorAt(0.0, color_start)
            grad.setColorAt(1.0, color_end)
            
            painter.setBrush(grad)
            painter.drawRoundedRect(active, 4, 4)
            
            # Draw count value
            painter.setPen(count_color)
            painter.drawText(QRectF(bar_rect.right() + 8, y, 42, row_h - 6), Qt.AlignVCenter | Qt.AlignRight, str(count))

        # Render premium hovering glassmorphic tooltip气泡
        if self.hovered_index != -1 and self.hovered_index < len(self.items):
            tag, name, count = self.items[self.hovered_index]
            tooltip_txt = f"标签: {tag}\n文档数量: {count} 个"
            
            # Measure text size
            fm = painter.fontMetrics()
            lines = tooltip_txt.split('\n')
            txt_w = max(fm.horizontalAdvance(line) for line in lines) + 20
            txt_h = len(lines) * fm.height() + 14
            
            # Position tooltip box slightly offset from cursor
            tip_x = self.tooltip_pos.x() + 15
            tip_y = self.tooltip_pos.y() - txt_h - 10
            
            # Prevent going off bounds
            if tip_x + txt_w > self.width():
                tip_x = self.tooltip_pos.x() - txt_w - 15
            if tip_y < 0:
                tip_y = self.tooltip_pos.y() + 15
                
            tip_rect = QRectF(tip_x, tip_y, txt_w, txt_h)
            
            # Draw background (translucent dark acrylic / light frost)
            painter.setPen(QPen(QColor(255, 255, 255, 50) if not is_light else QColor(0, 0, 0, 30), 1))
            bg_color = QColor(30, 41, 59, 230) if not is_light else QColor(255, 255, 255, 240)
            painter.setBrush(bg_color)
            painter.drawRoundedRect(tip_rect, 8, 8)
            
            # Draw glowing line tag accent color on the left of tooltip
            accent_bar = QRectF(tip_x + 2, tip_y + 6, 3, txt_h - 12)
            painter.setPen(Qt.NoPen)
            painter.setBrush(tag_color(tag))
            painter.drawRoundedRect(accent_bar, 1.5, 1.5)
            
            # Draw text
            painter.setPen(QColor("#F1F5F9") if not is_light else QColor("#0F172A"))
            text_rect = QRectF(tip_x + 10, tip_y + 7, txt_w - 12, txt_h - 14)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, tooltip_txt)


class WeeklyTrendChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.setMinimumHeight(170)
        self.setMouseTracking(True)
        self.hovered_index = -1
        self.tooltip_pos = QPoint()

    def set_data(self, items):
        self.items = items
        self.update()

    def mouseMoveEvent(self, event):
        if not self.items:
            super().mouseMoveEvent(event)
            return
        rect = self.rect().adjusted(24, 12, -24, -24)
        n = len(self.items)
        segment_w = rect.width() / float(max(1, n - 1))
        
        pos = event.position()
        closest_index = -1
        min_dist = 9999.0
        for i in range(n):
            x = rect.left() + i * segment_w
            dist = abs(pos.x() - x)
            if dist < min_dist:
                min_dist = dist
                closest_index = i
                
        if closest_index != -1 and min_dist < segment_w * 0.6:
            self.hovered_index = closest_index
            self.tooltip_pos = pos.toPoint()
        else:
            self.hovered_index = -1
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_index = -1
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Margins: bottom needs some space for text labels (24px)
        rect = self.rect().adjusted(24, 12, -24, -24)
        
        theme = config.theme
        is_light = theme in ["light", "zhongguose"]
        
        # Define high-contrast adaptive color tokens
        if is_light:
            axis_color = QColor("#94A3B8")       # Slate light axis
            text_muted = QColor("#475569")       # Dark Slate labels
            text_value = QColor("#0F172A")       # Deep Slate bold numbers
            line_color = QColor("#6366F1") if theme == "light" else QColor("#1BA784")  # Soft line color
        else:
            axis_color = QColor("#4A6FA6")       # Cyan blue axis
            text_muted = QColor("#85B3CB")       # Muted Ice Blue labels
            text_value = QColor("#D1FFFF")       # Cyan value labels
            line_color = QColor("#AAD9F2")       # Light blue lines

        if not self.items:
            painter.setPen(text_muted)
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无近 7 天数据")
            return

        max_count = max(count for _, count in self.items) or 1
        
        # Draw bottom axis line
        painter.setPen(QPen(axis_color, 1))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        
        # Top safe margin of 25px
        usable_h = rect.height() - 25
        
        # Calculate spacing
        n = len(self.items)
        segment_w = rect.width() / float(max(1, n - 1))
        
        # Compute points
        points = []
        for i, (label, count) in enumerate(self.items):
            x = rect.left() + i * segment_w
            y = rect.bottom() - (usable_h * count / max_count)
            points.append(QPointF(x, y))
            
        # Draw horizontal gridlines for premium look
        grid_pen = QPen()
        grid_pen.setColor(QColor(0, 0, 0, 12) if is_light else QColor(255, 255, 255, 12))
        grid_pen.setStyle(Qt.DashLine)
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        
        for g in range(1, 4):
            gy = rect.bottom() - (usable_h * (g / 4.0))
            painter.drawLine(rect.left(), gy, rect.right(), gy)
            
        # Draw the spline area gradient (only if we have more than 1 point)
        if len(points) > 1:
            # Reconstruct spline tangents for smooth Catmull-Rom-like Bezier path
            tangents = []
            for i in range(n):
                prev_pt = points[i-1] if i > 0 else points[0]
                next_pt = points[i+1] if i < n-1 else points[n-1]
                tangents.append(QPointF((next_pt.x() - prev_pt.x()) / 6.0, (next_pt.y() - prev_pt.y()) / 6.0))
                
            # Area path for vertical gradient fill
            area_path = QPainterPath()
            area_path.moveTo(points[0].x(), rect.bottom())
            area_path.lineTo(points[0])
            
            for i in range(n - 1):
                p1 = points[i]
                p2 = points[i+1]
                c1 = p1 + tangents[i]
                c2 = p2 - tangents[i+1]
                area_path.cubicTo(c1, c2, p2)
                
            area_path.lineTo(points[-1].x(), rect.bottom())
            area_path.closeSubpath()
            
            # Fill gradient
            grad = QLinearGradient(0, rect.top() + 25, 0, rect.bottom())
            color_start = QColor(line_color)
            color_start.setAlpha(60)
            color_end = QColor(line_color)
            color_end.setAlpha(0)
            grad.setColorAt(0.0, color_start)
            grad.setColorAt(1.0, color_end)
            
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawPath(area_path)
            
            # Spline line path
            line_path = QPainterPath()
            line_path.moveTo(points[0])
            for i in range(n - 1):
                p1 = points[i]
                p2 = points[i+1]
                c1 = p1 + tangents[i]
                c2 = p2 - tangents[i+1]
                line_path.cubicTo(c1, c2, p2)
                
            painter.setPen(QPen(line_color, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(line_path)
        else:
            # Fallback if only 1 point
            pt = points[0]
            painter.setPen(QPen(line_color, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(rect.left(), pt.y(), rect.right(), pt.y())
            
        # Draw high-tech vertical alignment line on hovered index
        if self.hovered_index != -1 and self.hovered_index < len(points):
            cursor_x = points[self.hovered_index].x()
            cursor_pen = QPen(QColor(line_color), 1, Qt.DashLine)
            painter.setPen(cursor_pen)
            painter.drawLine(cursor_x, rect.top() + 10, cursor_x, rect.bottom())

        # Draw labels and nodes
        for i, (label, count) in enumerate(self.items):
            pt = points[i]
            
            # Bottom date label
            painter.setPen(text_muted)
            painter.setFont(painter.font()) # Reset/maintain font
            painter.drawText(QRectF(pt.x() - 30, rect.bottom() + 4, 60, 18), Qt.AlignCenter, label)
            
            # Value label cleanly above the point
            painter.setPen(text_value)
            # Make the value text bold for contrast
            f = painter.font()
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(QRectF(pt.x() - 20, pt.y() - 20, 40, 16), Qt.AlignCenter, str(count))
            f.setBold(False)
            painter.setFont(f)
            
            # Glowing node (bigger on hover)
            glow_color = QColor(line_color)
            glow_color.setAlpha(80 if i == self.hovered_index else 40)
            painter.setBrush(glow_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(pt, 10 if i == self.hovered_index else 7, 10 if i == self.hovered_index else 7)
            
            # Inner dot
            painter.setBrush(QColor("#FFFFFF") if is_light else QColor("#1E293B"))
            painter.setPen(QPen(line_color, 1.5))
            painter.drawEllipse(pt, 3.5, 3.5)

        # Render floating glassmorphic tooltip for Weekly Trend
        if self.hovered_index != -1 and self.hovered_index < len(self.items):
            label, count = self.items[self.hovered_index]
            tooltip_txt = f"日期: {label}\n整理量: {count} 个"
            
            # Measure text size
            fm = painter.fontMetrics()
            lines = tooltip_txt.split('\n')
            txt_w = max(fm.horizontalAdvance(line) for line in lines) + 20
            txt_h = len(lines) * fm.height() + 14
            
            tip_x = self.tooltip_pos.x() + 15
            tip_y = self.tooltip_pos.y() - txt_h - 10
            
            if tip_x + txt_w > self.width():
                tip_x = self.tooltip_pos.x() - txt_w - 15
            if tip_y < 0:
                tip_y = self.tooltip_pos.y() + 15
                
            tip_rect = QRectF(tip_x, tip_y, txt_w, txt_h)
            
            painter.setPen(QPen(QColor(255, 255, 255, 50) if not is_light else QColor(0, 0, 0, 30), 1))
            bg_color = QColor(30, 41, 59, 230) if not is_light else QColor(255, 255, 255, 240)
            painter.setBrush(bg_color)
            painter.drawRoundedRect(tip_rect, 8, 8)
            
            # Accent bar
            accent_bar = QRectF(tip_x + 2, tip_y + 6, 3, txt_h - 12)
            painter.setPen(Qt.NoPen)
            painter.setBrush(line_color)
            painter.drawRoundedRect(accent_bar, 1.5, 1.5)
            
            # Text
            painter.setPen(QColor("#F1F5F9") if not is_light else QColor("#0F172A"))
            text_rect = QRectF(tip_x + 10, tip_y + 7, txt_w - 12, txt_h - 14)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, tooltip_txt)


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
        self.card_unorganized = self.create_stat_card("收集箱未整理", "0", f"{config.get_inbox_name()} 目录中等待整理的文件", "inbox")
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

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)
        self.tag_chart = TagDistributionChart()
        self.weekly_chart = WeeklyTrendChart()
        self.chart_card_tags = self.create_chart_card("标签分布图", self.tag_chart)
        self.chart_card_weekly = self.create_chart_card("近 7 天整理趋势", self.weekly_chart)
        charts_layout.addWidget(self.chart_card_tags, 1)
        charts_layout.addWidget(self.chart_card_weekly, 1)
        main_layout.addLayout(charts_layout)

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

        # Keep dummy/hidden member variables for 100% backend compatibility
        self.tags_summary = QLabel()
        self.bar_title = QLabel()
        self.bar_container = QFrame()
        self.bar_container_layout = QVBoxLayout(self.bar_container)

        # Create a container frame for premium indicators
        theme = config.theme
        is_light = theme in ["light", "zhongguose"]
        indicators_frame = QFrame()
        indicators_layout = QHBoxLayout(indicators_frame)
        indicators_layout.setContentsMargins(0, 5, 0, 5)
        indicators_layout.setSpacing(30) # Generous horizontal spacing

        # --- Indicator 1: 标签覆盖度 ---
        tag_indicator_widget = QWidget()
        tag_indicator_layout = QVBoxLayout(tag_indicator_widget)
        tag_indicator_layout.setContentsMargins(0, 0, 0, 0)
        tag_indicator_layout.setSpacing(6)

        tag_header_layout = QHBoxLayout()
        self.tag_lbl = QLabel("标签覆盖度")
        self.tag_value_lbl = QLabel("0%")
        tag_header_layout.addWidget(self.tag_lbl)
        tag_header_layout.addStretch()
        tag_header_layout.addWidget(self.tag_value_lbl)

        self.tag_progress = QProgressBar()
        self.tag_progress.setRange(0, 100)
        self.tag_progress.setValue(0)
        self.tag_progress.setTextVisible(False) # Hide overlapping text
        self.tag_progress.setFixedHeight(6)
        
        tag_indicator_layout.addLayout(tag_header_layout)
        tag_indicator_layout.addWidget(self.tag_progress)

        # --- Indicator 2: 近7天整理进度 ---
        recent_indicator_widget = QWidget()
        recent_indicator_layout = QVBoxLayout(recent_indicator_widget)
        recent_indicator_layout.setContentsMargins(0, 0, 0, 0)
        recent_indicator_layout.setSpacing(6)

        recent_header_layout = QHBoxLayout()
        self.recent_lbl = QLabel("近7天整理进度")
        self.recent_value_lbl = QLabel("0%")
        recent_header_layout.addWidget(self.recent_lbl)
        recent_header_layout.addStretch()
        recent_header_layout.addWidget(self.recent_value_lbl)

        self.recent_progress = QProgressBar()
        self.recent_progress.setRange(0, 100)
        self.recent_progress.setValue(0)
        self.recent_progress.setTextVisible(False) # Hide overlapping text
        self.recent_progress.setFixedHeight(6)
        
        recent_indicator_layout.addLayout(recent_header_layout)
        recent_indicator_layout.addWidget(self.recent_progress)

        # Add to horizontal indicators layout
        indicators_layout.addWidget(tag_indicator_widget, 1)
        indicators_layout.addWidget(recent_indicator_widget, 1)

        recent_layout.addWidget(indicators_frame)

        main_layout.addWidget(recent_card)

        # Apply physical hover animations to all main dashboard cards
        from ui.animations import apply_hover_physics
        apply_hover_physics([
            self.card_total_files, self.card_total_size, self.card_unorganized,
            self.card_tags_count, self.card_recent_count,
            self.desktop_card, self.backup_card, recent_card,
            self.chart_card_tags, self.chart_card_weekly
        ], lift_distance=3, shadow_blur=14)

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

    def create_chart_card(self, title, chart_widget):
        card = QFrame()
        card.setObjectName("CardPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("CardTitle")
        layout.addWidget(title_lbl)
        layout.addWidget(chart_widget)
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
        tagged_files_count = 0
        for f in all_files:
            if f["tags"]:
                tagged_files_count += 1
                for t in f["tags"].split(","):
                    if t.strip():
                        unique_tags.add(t.strip())
        tags_count = len(unique_tags)
        recent_files = db.get_recent_files(days=7)
        recent_count = len(recent_files)
        tag_distribution = db.get_tag_distribution()
        top_tags = sorted(tag_distribution.items(), key=lambda item: item[1], reverse=True)[:5]
        tag_summary_text = "、".join(f"{tag}({count})" for tag, count in top_tags) if top_tags else "--"
        tag_coverage = min(100, int((tagged_files_count / max(1, total_count)) * 100))
        recent_progress = min(100, int((recent_count / max(1, total_count)) * 100))

        # Update card values
        self.card_total_files.value_label.setText(str(total_count))
        self.card_total_size.value_label.setText(size_str)
        self.card_unorganized.value_label.setText(str(inbox_count))
        self.card_unorganized.desc_label.setText(f"{config.get_inbox_name()} 目录中等待整理的文件")
        self.card_tags_count.value_label.setText(str(tags_count))
        self.card_recent_count.value_label.setText(str(recent_count))
        self.tags_summary.setText(f"标签分布: {tag_summary_text}")
        self.pending_chip.setText(f"待处理: {inbox_count} 个")
        self.coverage_chip.setText(f"标签覆盖: {tag_coverage}%")
        self.recent_chip.setText(f"近7天整理: {recent_count} 个")
        self.tag_chart.set_data(top_tags)
        self.weekly_chart.set_data(self.build_weekly_activity(all_files))
        self.render_tag_bars(top_tags)

        # Dynamic Theme-Adaptive CSS & Label values update for Premium Progress Indicators
        theme = config.theme
        is_light = theme in ["light", "zhongguose"]
        bg_track = "rgba(0, 0, 0, 0.06)" if is_light else "rgba(255, 255, 255, 0.06)"
        lbl_style = "color: #475569; font-size: 12px; font-weight: 500;" if is_light else "color: #85B3CB; font-size: 12px; font-weight: 500;"
        tag_color_hex = "#6366F1" if theme == "light" else ("#1BA784" if theme == "zhongguose" else "#AAD9F2")
        recent_color_hex = "#4F46E5" if theme == "light" else ("#127A60" if theme == "zhongguose" else "#4A6FA6")

        self.tag_lbl.setStyleSheet(lbl_style)
        self.recent_lbl.setStyleSheet(lbl_style)
        self.tag_value_lbl.setStyleSheet(f"color: {tag_color_hex}; font-size: 12px; font-weight: bold;")
        self.recent_value_lbl.setStyleSheet(f"color: {recent_color_hex}; font-size: 12px; font-weight: bold;")

        self.tag_progress.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background-color: {bg_track};
                height: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {tag_color_hex};
                border-radius: 3px;
            }}
            """
        )
        self.recent_progress.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background-color: {bg_track};
                height: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {recent_color_hex};
                border-radius: 3px;
            }}
            """
        )

        self.tag_progress.setValue(tag_coverage)
        self.recent_progress.setValue(recent_progress)
        self.tag_value_lbl.setText(f"{tag_coverage}%")
        self.recent_value_lbl.setText(f"{recent_progress}%")

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

        # Retrieve recent backups history globally first to prevent NameError inside cloud logic
        recent_backups = db.get_backup_history(limit=5)

        # Update disk label
        if has_disk:
            # Check if recently backed up
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

    def build_weekly_activity(self, all_files):
        today = datetime.date.today()
        days = [today - datetime.timedelta(days=offset) for offset in range(6, -1, -1)]
        counts = {day: 0 for day in days}
        for record in all_files:
            try:
                day = datetime.datetime.fromtimestamp(record["modified_time"]).date()
            except Exception:
                continue
            if day in counts:
                counts[day] += 1
        return [(day.strftime("%m/%d"), counts[day]) for day in days]

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
                                     f"是否确认将桌面上所有的普通文件移动到 {config.get_inbox_name()} 收集箱进行统一整理？\n(桌面快捷方式 .lnk 文件将被忽略)",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            moved, errors = FileManager.clean_desktop_to_inbox()
            if errors:
                error_msg = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n及其他 {len(errors) - 5} 个文件..."
                QMessageBox.warning(self, "清理完成 (部分失败)", f"已成功移动 {moved} 个文件，但部分文件移动失败:\n{error_msg}")
            else:
                show_toast(self, f"桌面清理完成，已移动 {moved} 个文件。", title="清理完成", level="success", duration=3600)
            
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
            color = tag_color(tag)
            soft = QColor(color)
            soft.setAlpha(52)
            name = QLabel(display_name(tag))
            name.setFixedWidth(90)
            name.setStyleSheet(f"color: {color.name()}; font-weight: 700;")
            bar = QProgressBar()
            bar.setRange(0, total)
            bar.setValue(count)
            bar.setFormat(str(count))
            text_color_name = color.darker(130).name() if config.theme in ["light", "zhongguose"] else color.lighter(165).name()
            bar.setStyleSheet(
                f"""
                QProgressBar {{
                    border: 1px solid {color.name()};
                    border-radius: 6px;
                    text-align: center;
                    background: {soft.name(QColor.HexArgb)};
                    color: {text_color_name};
                    height: 16px;
                }}
                QProgressBar::chunk {{
                    background-color: {color.name()};
                    border-radius: 5px;
                }}
                """
            )
            row_layout.addWidget(name)
            row_layout.addWidget(bar, 1)
            self.bar_container_layout.addWidget(row)

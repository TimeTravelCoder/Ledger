import os
import datetime
import shutil
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QFrame,
                             QCheckBox, QMessageBox, QFileDialog, QTextEdit,
                             QComboBox, QScrollArea, QListWidget, QListWidgetItem,
                             QTabWidget, QLayout, QProgressBar)
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QRect
from PySide6.QtGui import QIcon, QCursor
from config import config, DEFAULT_TAGS, normalize_tags, display_tag, NAME_PRESET_BASES
from file_manager import FileManager
from ui.icon_utils import line_icon, format_bytes
from ui.toast import show_toast

class FlowLayout(QLayout):
    """
    Custom dynamic flow layout that wraps widgets horizontally as window width resizes.
    Perfect for modern capsule tag pools.
    """
    def __init__(self, parent=None, margin=0, hspacing=6, vspacing=6):
        super().__init__(parent)
        self._items = []
        self._hspacing = hspacing
        self._vspacing = vspacing
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        del self._items

    def addItem(self, item):
        self._items.append(item)

    def horizontalSpacing(self):
        return self._hspacing

    def verticalSpacing(self):
        return self._vspacing

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        x = rect.x() + margins.left()
        y = rect.y() + margins.top()
        line_height = 0
        h_space = self.horizontalSpacing()
        v_space = self.verticalSpacing()

        for item in self._items:
            space_x = h_space
            space_y = v_space
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x() + margins.left()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + margins.bottom()


class VisualTagPool(QWidget):
    """
    Interactive flow-wrap Tag pool that renders tags as high-end capsules
    with dynamic deletion buttons and a real-time inline quick-add input.
    """
    def __init__(self, category_type, parent=None):
        super().__init__(parent)
        self.category_type = category_type # "primary", "secondary", "status"
        self.tags = []

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        # Scroll area for capsules to prevent vertical UI bloat
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setMinimumHeight(70)
        self.scroll.setMaximumHeight(160)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; }")

        self.capsule_widget = QWidget()
        self.capsule_widget.setObjectName("CapsuleWidgetContainer")
        self.capsule_widget.setStyleSheet("#CapsuleWidgetContainer { background: transparent; }")
        self.capsule_layout = FlowLayout(self.capsule_widget, margin=0, hspacing=6, vspacing=6)
        self.scroll.setWidget(self.capsule_widget)
        self.main_layout.addWidget(self.scroll)

        # Inline input for quick-adding new tags
        self.input_layout = QHBoxLayout()
        self.input_layout.setSpacing(8)

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("+ 输入标签名称，按回车快速添加...")
        self.add_input.setObjectName("TagQuickAddInput")
        self.add_input.returnPressed.connect(self.add_tag_from_input)
        self.input_layout.addWidget(self.add_input)

        self.btn_add = QPushButton("添加")
        self.btn_add.setObjectName("PrimaryBtn")
        self.btn_add.setFixedWidth(60)
        self.btn_add.clicked.connect(self.add_tag_from_input)
        self.input_layout.addWidget(self.btn_add)

        self.main_layout.addLayout(self.input_layout)

    def set_tags(self, tags):
        self.tags = list(tags)
        self.refresh_capsules()

    def refresh_capsules(self):
        # Clear existing capsules safely
        while self.capsule_layout.count() > 0:
            item = self.capsule_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Generate new capsule pills
        for tag in self.tags:
            capsule = self.create_capsule(tag)
            self.capsule_layout.addWidget(capsule)

    def create_capsule(self, tag):
        capsule = QFrame()
        capsule.setObjectName(f"TagCapsule_{self.category_type}")
        capsule.setProperty("category", self.category_type)

        layout = QHBoxLayout(capsule)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        lbl = QLabel(display_tag(tag))
        lbl.setStyleSheet("background: transparent; border: none; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl)

        btn_close = QPushButton("×")
        btn_close.setObjectName("CapsuleCloseBtn")
        btn_close.setFixedSize(14, 14)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(lambda checked=False, t=tag: self.remove_tag(t))
        layout.addWidget(btn_close)

        return capsule

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)
            self.refresh_capsules()

    def add_tag_from_input(self):
        text = self.add_input.text().strip()
        if not text:
            return

        tags = normalize_tags([text])
        if tags:
            t = tags[0]
            if t not in self.tags:
                self.tags.append(t)
                self.refresh_capsules()

        self.add_input.clear()

    def get_tags(self):
        return self.tags


class SettingsView(QWidget):
    refresh_other_views_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

        # Load initial configuration data and stats
        self.populate_rule_list()
        self.populate_name_presets()
        self.load_tags_to_pools()
        self.update_workspace_stats()

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # 1. Page Header (Modern Title Panel)
        header_panel = QFrame()
        header_panel.setObjectName("ToolbarPanel")
        header_panel.setFixedHeight(50)
        header_layout = QHBoxLayout(header_panel)
        header_layout.setContentsMargins(18, 0, 18, 0)
        header_layout.setSpacing(8)

        header_icon = QLabel()
        header_icon.setPixmap(line_icon("settings", size=18).pixmap(18, 18))
        header_layout.addWidget(header_icon)

        header = QLabel("系统参数设置")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        outer_layout.addWidget(header_panel)

        # 2. Central Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setObjectName("SettingsTabs")
        self.tabs.setContentsMargins(12, 12, 12, 12)

        # ── Tab 1: 常规路径 (Path Settings) ──────────────────────────────────
        tab_paths = QWidget()
        layout_paths = QVBoxLayout(tab_paths)
        layout_paths.setContentsMargins(15, 15, 15, 15)
        layout_paths.setSpacing(15)

        dir_card = QFrame()
        dir_card.setObjectName("CardPanel")
        dir_layout = QVBoxLayout(dir_card)
        dir_layout.setContentsMargins(20, 20, 20, 20)
        dir_layout.setSpacing(15)

        # High-fidelity Title and Subtitle
        title_vbox = QVBoxLayout()
        dir_title = QLabel("路径参数配置")
        dir_title.setObjectName("SettingsCardTitle")
        title_vbox.addWidget(dir_title)

        dir_subtitle = QLabel("配置您的文档整理主目录并激活智能 Downloads 下载监控。")
        dir_subtitle.setStyleSheet("color: #94A3B8; font-size: 11px;")
        title_vbox.addWidget(dir_subtitle)
        dir_layout.addLayout(title_vbox)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 5, 0, 5)

        # Row 0: Workspace Path
        grid.addWidget(QLabel("主工作空间目录 (Workspace):"), 0, 0)
        self.input_ws_path = QLineEdit(config.workspace_dir)
        self.input_ws_path.setPlaceholderText("选择或输入标准文档工作空间存放根路径...")
        grid.addWidget(self.input_ws_path, 0, 1)
        self.btn_browse_ws = QPushButton("浏览...")
        self.btn_browse_ws.setIcon(line_icon("folder", size=16))
        self.btn_browse_ws.setIconSize(QSize(16, 16))
        self.btn_browse_ws.clicked.connect(self.browse_workspace)
        grid.addWidget(self.btn_browse_ws, 0, 2)

        # Row 1: Workspace Status
        self.lbl_ws_status = QLabel()
        grid.addWidget(self.lbl_ws_status, 1, 1)

        # Row 2: Downloads Path
        grid.addWidget(QLabel("浏览器下载目录 (Downloads):"), 2, 0)
        self.input_dl_path = QLineEdit(config.downloads_dir)
        self.input_dl_path.setPlaceholderText("选择浏览器默认下载路径，用于自动监听导入功能...")
        grid.addWidget(self.input_dl_path, 2, 1)
        self.btn_browse_dl = QPushButton("浏览...")
        self.btn_browse_dl.setIcon(line_icon("folder", size=16))
        self.btn_browse_dl.setIconSize(QSize(16, 16))
        self.btn_browse_dl.clicked.connect(self.browse_downloads)
        grid.addWidget(self.btn_browse_dl, 2, 2)

        # Row 3: Downloads Status
        self.lbl_dl_status = QLabel()
        grid.addWidget(self.lbl_dl_status, 3, 1)

        dir_layout.addLayout(grid)

        self.cb_monitor_dl = QCheckBox("自动监控 Downloads 文件夹的变化 (弹出智能整理提醒)")
        self.cb_monitor_dl.setChecked(config.monitored_downloads)
        self.cb_monitor_dl.stateChanged.connect(self.save_monitored)
        dir_layout.addWidget(self.cb_monitor_dl)

        # Connect text changes to dynamic path validation
        self.input_ws_path.textChanged.connect(self.validate_paths_realtime)
        self.input_dl_path.textChanged.connect(self.validate_paths_realtime)

        # Bottom buttons with correct visual weight swap
        init_layout = QHBoxLayout()
        init_layout.setSpacing(12)

        # 1. Maintenance Action: Weakened to secondary outlined style to prevent accidental catalog overwrite
        self.btn_init_ws = QPushButton("一键初始化/修复标准目录结构")
        self.btn_init_ws.setObjectName("SecondaryBtn")
        self.btn_init_ws.setIcon(line_icon("success", size=16))
        self.btn_init_ws.setIconSize(QSize(16, 16))
        self.btn_init_ws.clicked.connect(self.run_init_workspace)
        init_layout.addWidget(self.btn_init_ws)

        init_layout.addStretch()

        # 2. Main Action: Swapped to Primary Indigo background to emphasize save priority
        self.btn_save_paths = QPushButton("应用路径并重新加载")
        self.btn_save_paths.setObjectName("PrimaryBtn")
        self.btn_save_paths.setStyleSheet("background-color: #6366F1; color: #FFFFFF;")
        self.btn_save_paths.setIcon(line_icon("refresh", "#FFFFFF", size=16))
        self.btn_save_paths.setIconSize(QSize(16, 16))
        self.btn_save_paths.clicked.connect(self.save_paths)
        init_layout.addWidget(self.btn_save_paths)
        dir_layout.addLayout(init_layout)

        # Render theme badge
        self.update_theme_badge()
        # Initialize validation status
        self.validate_paths_realtime()

        layout_paths.addWidget(dir_card)

        # Workspace Health & Disk Usage Meter Card
        stats_card = QFrame()
        stats_card.setObjectName("CardPanel")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(18, 18, 18, 18)
        stats_layout.setSpacing(12)

        stats_title = QLabel("空间健康与磁盘状况")
        stats_title.setObjectName("SettingsCardTitle")
        stats_layout.addWidget(stats_title)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)

        self.lbl_file_count = QLabel("文件总量: 计算中...")
        self.lbl_file_count.setStyleSheet("font-weight: 600;")
        stats_grid.addWidget(self.lbl_file_count, 0, 0)

        self.lbl_ws_size = QLabel("总占用空间: 计算中...")
        self.lbl_ws_size.setStyleSheet("font-weight: 600;")
        stats_grid.addWidget(self.lbl_ws_size, 0, 1)

        self.lbl_disk_free = QLabel("磁盘剩余容量: 计算中...")
        self.lbl_disk_free.setStyleSheet("font-weight: 600;")
        stats_grid.addWidget(self.lbl_disk_free, 1, 0, 1, 2)
        stats_layout.addLayout(stats_grid)

        # Drive Usage Progress Bar (Styled as sleek line meter)
        self.disk_bar = QProgressBar()
        self.disk_bar.setObjectName("DiskUsageBar")
        self.disk_bar.setRange(0, 100)
        self.disk_bar.setValue(0)
        self.disk_bar.setFixedHeight(8)
        self.disk_bar.setTextVisible(False)
        stats_layout.addWidget(self.disk_bar)

        layout_paths.addWidget(stats_card)
        layout_paths.addStretch()

        # ── Tab 2: 空间向导 (Workspace Wizard) ──────────────────────────────
        tab_wiz = QWidget()
        layout_wiz = QVBoxLayout(tab_wiz)
        layout_wiz.setContentsMargins(15, 15, 15, 15)
        layout_wiz.setSpacing(15)

        wiz_scroll = QScrollArea()
        wiz_scroll.setWidgetResizable(True)
        wiz_scroll.setFrameShape(QFrame.NoFrame)
        wiz_scroll.setStyleSheet("QScrollArea { background: transparent; }")

        wiz_scroll_content = QWidget()
        wiz_scroll_content.setObjectName("WizScrollContent")
        wiz_scroll_content.setStyleSheet("#WizScrollContent { background: transparent; }")
        wiz_inner = QVBoxLayout(wiz_scroll_content)
        wiz_inner.setContentsMargins(0, 0, 0, 0)
        wiz_inner.setSpacing(15)

        wizard_card = QFrame()
        wizard_card.setObjectName("CardPanel")
        wizard_layout = QVBoxLayout(wizard_card)
        wizard_layout.setContentsMargins(18, 18, 18, 18)
        wizard_layout.setSpacing(15)

        wizard_title = QLabel("新建工作空间向导")
        wizard_title.setObjectName("SettingsCardTitle")
        wizard_layout.addWidget(wizard_title)

        wizard_desc = QLabel("选择任意盘符或目录，系统将在此目录下创建 'Workspace' 文件夹，并自动初始化 12 个标准的分类目录。")
        wizard_desc.setObjectName("MutedText")
        wizard_layout.addWidget(wizard_desc)

        wiz_grid = QGridLayout()
        wiz_grid.setSpacing(10)
        wiz_grid.addWidget(QLabel("选择目标路径:"), 0, 0)
        self.input_wiz_path = QLineEdit()
        self.input_wiz_path.setPlaceholderText("选择磁盘目录，例如 D:/ 或 E:/LedgerHub")
        wiz_grid.addWidget(self.input_wiz_path, 0, 1)
        self.btn_wiz_browse = QPushButton("选择目录...")
        self.btn_wiz_browse.setIcon(line_icon("folder", size=16))
        self.btn_wiz_browse.setIconSize(QSize(16, 16))
        self.btn_wiz_browse.clicked.connect(self.browse_wizard_path)
        wiz_grid.addWidget(self.btn_wiz_browse, 0, 2)

        wiz_grid.addWidget(QLabel("标准分类模板:"), 1, 0)
        self.wiz_lang_combo = QComboBox()
        self.wiz_lang_combo.addItems([
            "中文标准模版 (00收集箱, 01课程学习, 02课题研究...)",
            "英文标准模版 (00Inbox, 01Study, 02Research...)",
            "自建自定义分类模版 (使用下方设置的自建分类模板)"
        ])
        wiz_grid.addWidget(self.wiz_lang_combo, 1, 1, 1, 2)
        wizard_layout.addLayout(wiz_grid)

        self.btn_run_wiz = QPushButton("一键生成工作空间文件夹")
        self.btn_run_wiz.setObjectName("SuccessBtn")
        self.btn_run_wiz.setIcon(line_icon("workspace", "#FFFFFF", 16))
        self.btn_run_wiz.setIconSize(QSize(16, 16))
        self.btn_run_wiz.clicked.connect(self.run_workspace_wizard)
        wizard_layout.addWidget(self.btn_run_wiz)
        wiz_inner.addWidget(wizard_card)

        custom_card = QFrame()
        custom_card.setObjectName("CardPanel")
        custom_layout = QVBoxLayout(custom_card)
        custom_layout.setContentsMargins(18, 18, 18, 18)
        custom_layout.setSpacing(15)

        custom_title = QLabel("自建分类目录模板与规范")
        custom_title.setObjectName("SettingsCardTitle")
        custom_layout.addWidget(custom_title)

        custom_desc = QLabel("启用自建模板后，系统在生成空间或整理目录时，会使用您自定义的分类文件夹结构。")
        custom_desc.setObjectName("MutedText")
        custom_layout.addWidget(custom_desc)

        self.cb_use_custom_dirs = QCheckBox("启用自建分类目录结构")
        self.cb_use_custom_dirs.setChecked(config.use_custom_dirs)
        self.cb_use_custom_dirs.stateChanged.connect(self.save_use_custom_dirs)
        custom_layout.addWidget(self.cb_use_custom_dirs)

        grid_custom = QHBoxLayout()
        grid_custom.addWidget(QLabel("自建目录结构 (用英文逗号分隔):"))
        self.input_custom_dirs = QLineEdit(", ".join(config.custom_standard_dirs))
        if not config.custom_standard_dirs:
            self.input_custom_dirs.setPlaceholderText("例如: 00收集箱, 01学习, 02工作, 03生活, 04娱乐, 99临时缓冲")
        grid_custom.addWidget(self.input_custom_dirs, 1)
        custom_layout.addLayout(grid_custom)

        self.btn_save_custom_dirs = QPushButton("保存并应用自建分类模板")
        self.btn_save_custom_dirs.setObjectName("PrimaryBtn")
        self.btn_save_custom_dirs.setIcon(line_icon("success", "#FFFFFF", 16))
        self.btn_save_custom_dirs.setIconSize(QSize(16, 16))
        self.btn_save_custom_dirs.clicked.connect(self.save_custom_dirs)
        custom_layout.addWidget(self.btn_save_custom_dirs)
        wiz_inner.addWidget(custom_card)

        wiz_scroll.setWidget(wiz_scroll_content)
        layout_wiz.addWidget(wiz_scroll)

        # ── Tab 3: 标签管理 (Tags Dictionary) ──────────────────────────────
        tab_tags = QWidget()
        layout_tags = QVBoxLayout(tab_tags)
        layout_tags.setContentsMargins(15, 15, 15, 15)
        layout_tags.setSpacing(15)

        tag_card = QFrame()
        tag_card.setObjectName("CardPanel")
        tag_layout = QVBoxLayout(tag_card)
        tag_layout.setContentsMargins(18, 18, 18, 18)
        tag_layout.setSpacing(15)

        tag_title = QLabel("自定义标签字典体系")
        tag_title.setObjectName("SettingsCardTitle")
        tag_layout.addWidget(tag_title)

        tag_desc = QLabel("配置系统的全局标签下拉池与智能归类体系。系统会自动规范并添加 '#' 前缀。")
        tag_desc.setObjectName("MutedText")
        tag_layout.addWidget(tag_desc)

        tag_grid = QGridLayout()
        tag_grid.setSpacing(15)
        tag_grid.addWidget(QLabel("一级分类标签 (Primary):"), 0, 0)
        self.tag_pool_primary = VisualTagPool("primary")
        tag_grid.addWidget(self.tag_pool_primary, 0, 1)

        tag_grid.addWidget(QLabel("二级细分标签 (Secondary):"), 1, 0)
        self.tag_pool_secondary = VisualTagPool("secondary")
        tag_grid.addWidget(self.tag_pool_secondary, 1, 1)

        tag_grid.addWidget(QLabel("状态属性标签 (Status):"), 2, 0)
        self.tag_pool_status = VisualTagPool("status")
        tag_grid.addWidget(self.tag_pool_status, 2, 1)
        tag_layout.addLayout(tag_grid)

        tag_btn_layout = QHBoxLayout()
        self.btn_save_tags = QPushButton("保存标签字典")
        self.btn_save_tags.setObjectName("PrimaryBtn")
        self.btn_save_tags.setIcon(line_icon("success", "#FFFFFF", 16))
        self.btn_save_tags.setIconSize(QSize(16, 16))
        self.btn_save_tags.clicked.connect(self.save_tags)
        tag_btn_layout.addWidget(self.btn_save_tags)

        self.btn_reset_tags = QPushButton("恢复系统出厂标签默认值")
        self.btn_reset_tags.setIcon(line_icon("refresh", size=16))
        self.btn_reset_tags.setIconSize(QSize(16, 16))
        self.btn_reset_tags.clicked.connect(self.reset_tags_to_default)
        tag_btn_layout.addWidget(self.btn_reset_tags)
        tag_layout.addLayout(tag_btn_layout)

        layout_tags.addWidget(tag_card)
        layout_tags.addStretch()

        # ── Tab 4: 自动规则 (Automation Rules) ──────────────────────────────
        tab_rules = QWidget()
        layout_rules = QVBoxLayout(tab_rules)
        layout_rules.setContentsMargins(15, 15, 15, 15)
        layout_rules.setSpacing(15)

        rules_scroll = QScrollArea()
        rules_scroll.setWidgetResizable(True)
        rules_scroll.setFrameShape(QFrame.NoFrame)
        rules_scroll.setStyleSheet("QScrollArea { background: transparent; }")

        rules_scroll_content = QWidget()
        rules_scroll_content.setObjectName("RulesScrollContent")
        rules_scroll_content.setStyleSheet("#RulesScrollContent { background: transparent; }")
        rules_scroll_inner = QVBoxLayout(rules_scroll_content)
        rules_scroll_inner.setContentsMargins(0, 0, 0, 0)
        rules_scroll_inner.setSpacing(15)

        rule_card = QFrame()
        rule_card.setObjectName("CardPanel")
        rule_layout = QVBoxLayout(rule_card)
        rule_layout.setContentsMargins(18, 18, 18, 18)
        rule_layout.setSpacing(12)

        rule_title = QLabel("规则归类自动化")
        rule_title.setObjectName("SettingsCardTitle")
        rule_layout.addWidget(rule_title)

        self.cb_auto_rule = QCheckBox("启用关键词 / 后缀名称自动归类 (导入收集箱时智能识别分流)")
        self.cb_auto_rule.setChecked(config.auto_rule_enabled)
        self.cb_auto_rule.stateChanged.connect(self.save_auto_rule_enabled)
        rule_layout.addWidget(self.cb_auto_rule)

        self.rule_scroll = QScrollArea()
        self.rule_scroll.setWidgetResizable(True)
        self.rule_scroll.setFrameShape(QFrame.NoFrame)
        self.rule_scroll.setMinimumHeight(200)
        self.rule_scroll_content = QWidget()
        self.rule_scroll_layout = QVBoxLayout(self.rule_scroll_content)
        self.rule_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.rule_scroll_layout.setSpacing(8)
        self.rule_scroll.setWidget(self.rule_scroll_content)
        rule_layout.addWidget(self.rule_scroll)

        self.btn_save_rules = QPushButton("保存归类规则")
        self.btn_save_rules.setObjectName("PrimaryBtn")
        self.btn_save_rules.setIcon(line_icon("success", "#FFFFFF", 16))
        self.btn_save_rules.setIconSize(QSize(16, 16))
        self.btn_save_rules.clicked.connect(self.save_auto_rules)
        rule_layout.addWidget(self.btn_save_rules)
        rules_scroll_inner.addWidget(rule_card)

        preset_card = QFrame()
        preset_card.setObjectName("CardPanel")
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(18, 18, 18, 18)
        preset_layout.setSpacing(12)

        preset_title = QLabel("规范命名模板")
        preset_title.setObjectName("SettingsCardTitle")
        preset_layout.addWidget(preset_title)

        preset_desc = QLabel("自定义导入时自动推荐改名的结构。支持的格式变量：{date}，{topic}，{version}，{status}，{stem}。")
        preset_desc.setObjectName("MutedText")
        preset_layout.addWidget(preset_desc)

        self.preset_list = QListWidget()
        self.preset_list.setObjectName("SettingsList")
        self.preset_list.setIconSize(QSize(18, 18))
        self.preset_list.setMinimumHeight(180)
        preset_layout.addWidget(self.preset_list)

        preset_edit = QGridLayout()
        preset_edit.setSpacing(8)
        self.input_preset_label = QLineEdit()
        self.input_preset_label.setPlaceholderText("例如: 学术论文")
        self.input_preset_prefix = QLineEdit()
        self.input_preset_prefix.setPlaceholderText("例如: 05")
        self.input_preset_format = QLineEdit()
        self.input_preset_format.setPlaceholderText("例如: {date}_{topic}_{version}")

        preset_edit.addWidget(QLabel("分类模板名称:"), 0, 0)
        preset_edit.addWidget(self.input_preset_label, 0, 1)
        preset_edit.addWidget(QLabel("默认分流目录前缀:"), 0, 2)
        preset_edit.addWidget(self.input_preset_prefix, 0, 3)
        preset_edit.addWidget(QLabel("命名格式规范:"), 1, 0)
        preset_edit.addWidget(self.input_preset_format, 1, 1, 1, 3)
        preset_layout.addLayout(preset_edit)

        preset_btn_layout = QHBoxLayout()
        self.btn_preset_add = QPushButton("新增命名模板")
        self.btn_preset_add.setIcon(line_icon("file", size=16))
        self.btn_preset_add.setIconSize(QSize(16, 16))
        self.btn_preset_add.clicked.connect(self.add_name_preset)
        preset_btn_layout.addWidget(self.btn_preset_add)

        self.btn_preset_delete = QPushButton("删除选中模板")
        self.btn_preset_delete.setIcon(line_icon("delete", size=16))
        self.btn_preset_delete.setIconSize(QSize(16, 16))
        self.btn_preset_delete.clicked.connect(self.delete_name_preset)
        preset_btn_layout.addWidget(self.btn_preset_delete)

        self.btn_preset_save = QPushButton("保存模板")
        self.btn_preset_save.setObjectName("PrimaryBtn")
        self.btn_preset_save.setIcon(line_icon("success", "#FFFFFF", 16))
        self.btn_preset_save.setIconSize(QSize(16, 16))
        self.btn_preset_save.clicked.connect(self.save_name_presets)
        preset_btn_layout.addWidget(self.btn_preset_save)
        preset_layout.addLayout(preset_btn_layout)

        # Real-time Sandbox Rename Preview
        self.sandbox_preview_box = QFrame()
        self.sandbox_preview_box.setObjectName("RenamePreviewCard")
        sandbox_layout = QVBoxLayout(self.sandbox_preview_box)
        sandbox_layout.setContentsMargins(12, 12, 12, 12)
        sandbox_layout.setSpacing(6)

        sandbox_title = QLabel("命名模板沙盒实时预览:")
        sandbox_title.setStyleSheet("font-size: 11px; font-weight: bold; text-transform: uppercase; color: #85B3CB;")
        sandbox_layout.addWidget(sandbox_title)

        self.sandbox_preview_lbl = QLabel("预览结果: --")
        self.sandbox_preview_lbl.setObjectName("PreviewFileName")
        self.sandbox_preview_lbl.setWordWrap(True)
        sandbox_layout.addWidget(self.sandbox_preview_lbl)

        preset_layout.addWidget(self.sandbox_preview_box)

        rules_scroll_inner.addWidget(preset_card)
        rules_scroll_inner.addStretch()

        rules_scroll.setWidget(rules_scroll_content)
        layout_rules.addWidget(rules_scroll)

        # Connect Naming Editor selections and live sandbox updates
        self.preset_list.currentRowChanged.connect(self.on_preset_selected)
        self.input_preset_label.textChanged.connect(self.on_preset_edited)
        self.input_preset_prefix.textChanged.connect(self.on_preset_edited)
        self.input_preset_format.textChanged.connect(self.on_preset_edited)

        # 3. Mount all tabs with linear icons into central QTabWidget
        self.tabs.addTab(tab_paths, line_icon("folder", size=16), "常规路径")
        self.tabs.addTab(tab_wiz, line_icon("workspace", size=16), "空间向导")
        self.tabs.addTab(tab_tags, line_icon("tag", size=16), "标签字典")
        self.tabs.addTab(tab_rules, line_icon("settings", size=16), "自动规则")

        # 4. Add QTabWidget to settings panel layout
        outer_layout.addWidget(self.tabs)

    def browse_workspace(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择主工作空间根目录", config.workspace_dir)
        if dir_path:
            self.input_ws_path.setText(dir_path)

    def browse_downloads(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择浏览器下载目录", config.downloads_dir)
        if dir_path:
            self.input_dl_path.setText(dir_path)

    def save_monitored(self, state):
        config.monitored_downloads = bool(state)
        config.save()

    def save_paths(self):
        ws = self.input_ws_path.text().strip()
        dl = self.input_dl_path.text().strip()
        from config import is_writable

        if not ws or not dl:
            QMessageBox.warning(self, "错误", "路径不能为空！")
            return

        # 1. Validate Workspace Path
        ws_path = Path(ws)
        if ws_path.exists():
            if not ws_path.is_dir():
                QMessageBox.warning(self, "错误", "主工作空间路径指向一个文件，请输入或选择有效目录！")
                return
            if not is_writable(ws_path):
                QMessageBox.warning(self, "错误", "主工作空间路径无写入权限，请重新选择！")
                return
        else:
            parent_dir = ws_path.parent
            if not is_writable(parent_dir):
                QMessageBox.warning(self, "错误", "主工作空间目录不存在且无法创建（父目录无写权限），请重新选择！")
                return

        # 2. Validate Downloads Path
        dl_path = Path(dl)
        if not dl_path.exists():
            QMessageBox.warning(self, "错误", "浏览器下载目录在磁盘中不存在，请重新选择！")
            return
        if not dl_path.is_dir():
            QMessageBox.warning(self, "错误", "浏览器下载目录指向了一个文件，请输入或选择有效目录！")
            return

        config.workspace_dir = ws
        config.downloads_dir = dl
        config.save()

        # Reload database connection dynamically in db.py
        from db import db
        db.close() # Connection will reopen automatically at the new path

        show_toast(self, "新路径参数已生效。", title="应用成功", level="success")
        self.update_workspace_stats()
        self.refresh_other_views_signal.emit()

    def run_init_workspace(self):
        # 1. Apply paths first
        ws = self.input_ws_path.text().strip()
        if ws:
            config.workspace_dir = ws
            config.save()

        # 2. Run initialization
        success, msg = FileManager.init_workspace()
        if success:
            show_toast(self, "标准目录结构已初始化。", title="初始化成功", level="success", duration=3600)
        else:
            QMessageBox.critical(self, "错误", msg)

        self.update_workspace_stats()
        self.refresh_other_views_signal.emit()

    def load_tags_to_pools(self):
        self.tag_pool_primary.set_tags(config.tags["primary"])
        self.tag_pool_secondary.set_tags(config.tags["secondary"])
        self.tag_pool_status.set_tags(config.tags["status"])

    def save_tags(self):
        config.tags["primary"] = self.tag_pool_primary.get_tags()
        config.tags["secondary"] = self.tag_pool_secondary.get_tags()
        config.tags["status"] = self.tag_pool_status.get_tags()

        config.save()
        show_toast(self, "自定义标签字典已保存。", title="保存成功", level="success")
        self.refresh_other_views_signal.emit()

    def reset_tags_to_default(self):
        reply = QMessageBox.question(self, "确认重置", "是否确定将您的标签字典重置为系统出厂规范定义？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            config.tags = DEFAULT_TAGS.copy()
            config.save()

            # Refresh visual pools
            self.load_tags_to_pools()

            show_toast(self, "标签字典已重置为默认设置。", title="重置成功", level="success")
            self.refresh_other_views_signal.emit()

    def browse_wizard_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择生成工作空间的盘符或目录", "")
        if dir_path:
            self.input_wiz_path.setText(dir_path)

    def run_workspace_wizard(self):
        target_root = self.input_wiz_path.text().strip()
        if not target_root:
            QMessageBox.warning(self, "警告", "请先选择目标盘符或目录！")
            return

        target_path = Path(target_root)
        if target_path.name.lower() != "workspace":
            target_path = target_path / "Workspace"

        idx = self.wiz_lang_combo.currentIndex()
        chosen_lang = "cn"
        use_custom_dirs_flag = False
        if idx == 0:
            chosen_lang = "cn"
            use_custom_dirs_flag = False
        elif idx == 1:
            chosen_lang = "en"
            use_custom_dirs_flag = False
        else:
            use_custom_dirs_flag = True
            if not config.custom_standard_dirs:
                QMessageBox.warning(self, "警告", "请先在下方配置并保存您的“自建分类目录模板”！")
                return

        reply = QMessageBox.question(
            self, "确认生成工作空间",
            f"系统即将在以下位置生成全新的规范工作空间：\n{target_path}\n\n文件夹规范：{self.wiz_lang_combo.currentText()}\n是否确认生成并自动切换至此工作空间？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # First, set global config parameter temporarily to init the workspace correctly
            old_use_custom = config.use_custom_dirs
            config.use_custom_dirs = use_custom_dirs_flag

            # 1. Physically create workspace and directories
            success, msg = FileManager.init_workspace(custom_ws_dir=str(target_path), custom_lang=chosen_lang)
            if not success:
                # Revert if failed
                config.use_custom_dirs = old_use_custom
                QMessageBox.critical(self, "生成失败", msg)
                return

            # 2. Update config
            config.workspace_dir = str(target_path)
            if idx in [0, 1]:
                config.workspace_lang = chosen_lang
            config.save()

            # 3. Update paths fields
            self.input_ws_path.setText(str(target_path))

            # 4. Reload DB dynamically
            from db import db
            db.close()

            # 5. Sync scan
            FileManager.scan_workspace_files()

            show_toast(self, f"新工作空间已切换到 {target_path}。", title="生成成功", level="success", duration=4200)

            self.input_wiz_path.clear()
            self.update_workspace_stats()
            self.refresh_other_views_signal.emit()

    def save_use_custom_dirs(self, state):
        config.use_custom_dirs = bool(state)
        config.save()
        self.refresh_other_views_signal.emit()

    def update_workspace_stats(self):
        """
        Calculates file count, workspace physical size, and disk partition stats.
        Updates path-dashboard elements in real time.
        """
        ws_dir = config.workspace_dir
        if not os.path.exists(ws_dir):
            self.lbl_file_count.setText("文件总量: --")
            self.lbl_ws_size.setText("总占用空间: --")
            self.lbl_disk_free.setText("磁盘剩余容量: 未初始化/路径不存在")
            self.disk_bar.setValue(0)
            return

        # 1. Accumulate files and sizes inside workspace recursively
        file_count = 0
        total_size = 0
        try:
            for root, dirs, files in os.walk(ws_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        # Follow_symlinks=False to prevent circular issues
                        total_size += os.path.getsize(fp)
                        file_count += 1
                    except OSError:
                        pass
        except Exception:
            pass

        # 2. Get partition info
        try:
            total, used, free = shutil.disk_usage(ws_dir)
            percent = int((used / total) * 100)
            self.lbl_disk_free.setText(f"磁盘剩余容量: {format_bytes(free)} (磁盘总大小 {format_bytes(total)})")
            self.disk_bar.setValue(percent)
        except Exception:
            self.lbl_disk_free.setText("磁盘剩余容量: 无法获取")
            self.disk_bar.setValue(0)

        self.lbl_file_count.setText(f"文件总量: {file_count} 个规范文件")
        self.lbl_ws_size.setText(f"总占用空间: {format_bytes(total_size)}")
        # Dynamically refresh path verification status in real time
        self.validate_paths_realtime()

    def validate_paths_realtime(self):
        ws = self.input_ws_path.text().strip()
        dl = self.input_dl_path.text().strip()
        from config import is_writable

        # Validate Workspace
        if not ws:
            self.lbl_ws_status.setText("✕ 路径不能为空")
            self.lbl_ws_status.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 500;")
        elif os.path.exists(ws):
            if not os.path.isdir(ws):
                self.lbl_ws_status.setText("✕ 路径指向文件，并非有效目录")
                self.lbl_ws_status.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 500;")
            elif not is_writable(Path(ws)):
                self.lbl_ws_status.setText("✕ 路径存在但无写入权限")
                self.lbl_ws_status.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 500;")
            else:
                self.lbl_ws_status.setText("✓ 路径存在且可读写")
                self.lbl_ws_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 500;")
        else:
            parent_dir = Path(ws).parent
            if is_writable(parent_dir):
                self.lbl_ws_status.setText("⚠ 路径目前在磁盘中不存在 (应用后将自动创建)")
                self.lbl_ws_status.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: 500;")
            else:
                self.lbl_ws_status.setText("✕ 路径不存在且无法创建 (父目录无写权限)")
                self.lbl_ws_status.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 500;")

        # Validate Downloads
        if not dl:
            self.lbl_dl_status.setText("✕ 路径不能为空")
            self.lbl_dl_status.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 500;")
        elif os.path.exists(dl):
            if not os.path.isdir(dl):
                self.lbl_dl_status.setText("✕ 路径指向文件，并非有效目录")
                self.lbl_dl_status.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 500;")
            else:
                self.lbl_dl_status.setText("✓ 路径存在且可监听")
                self.lbl_dl_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 500;")
        else:
            self.lbl_dl_status.setText("✕ 路径在磁盘中不存在")
            self.lbl_dl_status.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 500;")

    def update_theme_badge(self):
        pass

    def populate_rule_list(self):
        while self.rule_scroll_layout.count():
            item = self.rule_scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.rule_widgets = []
        if not config.auto_rules:
            empty = QLabel("暂无规则归类配置。\n可以先保存默认规则，或在这里添加关键词/后缀到目标目录的映射。")
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            self.rule_scroll_layout.addWidget(empty)
        for rule in config.auto_rules:
            row = QFrame()
            row.setObjectName("CardPanel")
            row_layout = QGridLayout(row)
            row_layout.setContentsMargins(10, 10, 10, 10)
            row_layout.setHorizontalSpacing(8)
            row_layout.setVerticalSpacing(8)

            name = QLineEdit(rule.get("name", ""))
            keywords = QLineEdit(", ".join(rule.get("keywords", [])))
            exts = QLineEdit(", ".join(rule.get("extensions", [])))
            prefix = QLineEdit(rule.get("target_prefix", ""))

            row_layout.addWidget(QLabel("名称"), 0, 0)
            row_layout.addWidget(name, 0, 1)
            row_layout.addWidget(QLabel("关键词"), 0, 2)
            row_layout.addWidget(keywords, 0, 3)
            row_layout.addWidget(QLabel("后缀"), 1, 0)
            row_layout.addWidget(exts, 1, 1)
            row_layout.addWidget(QLabel("前缀"), 1, 2)
            row_layout.addWidget(prefix, 1, 3)

            row.setProperty("rule_widgets", (name, keywords, exts, prefix))
            self.rule_scroll_layout.addWidget(row)
            self.rule_widgets.append(row)

        self.rule_scroll_layout.addStretch()

    def save_auto_rule_enabled(self, state):
        config.auto_rule_enabled = bool(state)
        config.save()
        self.refresh_other_views_signal.emit()

    def save_auto_rules(self):
        rules = []
        for row in self.rule_widgets:
            widgets = row.property("rule_widgets")
            if not widgets:
                continue
            name_w, keywords_w, exts_w, prefix_w = widgets
            rules.append({
                "name": name_w.text().strip() or "未命名规则",
                "keywords": [p.strip() for p in keywords_w.text().split(",") if p.strip()],
                "extensions": [p.strip().lower() if p.strip().startswith(".") else f".{p.strip().lower()}" for p in exts_w.text().split(",") if p.strip()],
                "target_prefix": prefix_w.text().strip() or "01",
            })
        config.auto_rules = rules
        config.save()
        show_toast(self, "规则归类配置已保存。", title="保存成功", level="success")
        self.refresh_other_views_signal.emit()

    def populate_name_presets(self):
        self.preset_list.clear()
        self.name_presets = []

        # Load bases
        for base in NAME_PRESET_BASES:
            self.name_presets.append({
                "label": base["label"],
                "prefix": base["prefix"],
                "format": base["default_format"],
                "base": True
            })
        # Load customs
        for item in getattr(config, "custom_name_templates", []):
            self.name_presets.append({
                "label": item.get("label", "自定义"),
                "prefix": item.get("prefix", "01"),
                "format": item.get("format", "{date}_{topic}"),
                "base": False
            })

        # Add to list widget
        for preset in self.name_presets:
            li = QListWidgetItem(f"{preset['label']} | 前缀: {preset['prefix']} | 格式: {preset['format']}")
            li.setIcon(line_icon("file" if preset["base"] else "tag", size=18))
            li.setData(Qt.UserRole, preset)
            self.preset_list.addItem(li)

        # Select first preset automatically if items exist
        if self.preset_list.count() > 0:
            self.preset_list.setCurrentRow(0)

    def on_preset_selected(self, row):
        if row < 0 or row >= len(self.name_presets):
            return
        preset = self.name_presets[row]

        # Block signals temporarily to prevent cyclic update cascades while rendering
        self.input_preset_label.blockSignals(True)
        self.input_preset_prefix.blockSignals(True)
        self.input_preset_format.blockSignals(True)

        self.input_preset_label.setText(preset["label"])
        self.input_preset_prefix.setText(preset["prefix"])
        self.input_preset_format.setText(preset["format"])

        # Enable editing only for custom templates
        is_custom = not preset.get("base", False)
        self.input_preset_label.setEnabled(is_custom)
        self.input_preset_prefix.setEnabled(is_custom)
        self.input_preset_format.setEnabled(is_custom)

        self.input_preset_label.blockSignals(False)
        self.input_preset_prefix.blockSignals(False)
        self.input_preset_format.blockSignals(False)

        self.update_sandbox_preview()

    def on_preset_edited(self):
        row = self.preset_list.currentRow()
        if row < 0 or row >= len(self.name_presets):
            return
        preset = self.name_presets[row]
        if preset.get("base"):
            return  # Locked base template

        preset["label"] = self.input_preset_label.text().strip()
        preset["prefix"] = self.input_preset_prefix.text().strip()
        preset["format"] = self.input_preset_format.text().strip()

        # Synchronize list text dynamically
        item = self.preset_list.item(row)
        if item:
            item.setText(f"{preset['label']} | 前缀: {preset['prefix']} | 格式: {preset['format']}")

        self.update_sandbox_preview()

    def update_sandbox_preview(self):
        """
        Dynamically computes naming format variables in real time using mock data.
        """
        prefix = self.input_preset_prefix.text().strip() or "01"
        fmt = self.input_preset_format.text().strip() or "{date}_{topic}"

        # Today's date mock
        mock_date = datetime.date.today().strftime("%Y%m%d")

        mock_map = {
            "{date}": mock_date,
            "{topic}": "项目研究报告",
            "{version}": "V1.0",
            "{status}": "进行中",
            "{stem}": "原始文档名"
        }

        result_name = fmt
        for placeholder, replacement in mock_map.items():
            result_name = result_name.replace(placeholder, replacement)

        ext = ".docx" # Standard file ext mock

        full_path_result = f"规范输出结果: {prefix}_{result_name}{ext}"
        self.sandbox_preview_lbl.setText(full_path_result)

    def add_name_preset(self):
        self.name_presets.append({"label": "新自定义模板", "prefix": "05", "format": "{date}_{topic}", "base": False})
        self.sync_name_preset_inputs()

        # Auto-select the newly added preset
        self.preset_list.setCurrentRow(self.preset_list.count() - 1)

    def delete_name_preset(self):
        row = self.preset_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中一个自定义模板。")
            return
        preset = self.preset_list.item(row).data(Qt.UserRole)
        if preset and preset.get("base"):
            QMessageBox.information(self, "提示", "基础系统模板为只读，不能删除。")
            return

        # Remove selected from custom set
        self.name_presets.pop(row)
        self.sync_name_preset_inputs()

    def sync_name_preset_inputs(self):
        custom = [p for p in self.name_presets if not p.get("base")]
        config.custom_name_templates = custom
        self.populate_name_presets()

    def save_name_presets(self):
        config.custom_name_templates = [p for p in self.name_presets if not p.get("base")]
        config.save()
        show_toast(self, "命名模板已保存。", title="保存成功", level="success")
        self.refresh_other_views_signal.emit()

    def save_custom_dirs(self):
        raw_dirs = self.input_custom_dirs.text().strip()
        if not raw_dirs:
            QMessageBox.warning(self, "警告", "自建目录结构不能为空！")
            return

        raw_parts = [p.strip() for p in raw_dirs.replace("；", ",").replace(";", ",").split(",") if p.strip()]
        if not raw_parts:
            QMessageBox.warning(self, "警告", "自建目录结构格式不正确！")
            return

        parts = []
        for p_str in raw_parts:
            # Check for absolute paths
            if Path(p_str).is_absolute() or p_str.startswith("/") or p_str.startswith("\\"):
                QMessageBox.warning(self, "警告", f"自建目录中不能包含绝对路径: '{p_str}'！")
                return

            # Check for path traversals
            if ".." in p_str or p_str.startswith("."):
                QMessageBox.warning(self, "警告", f"自建目录中不能包含特殊字符或路径穿越: '{p_str}'！")
                return

            # Check for Windows illegal characters in directory names
            illegal_chars = ['*', '?', '"', '<', '>', '|', ':']
            if any(char in p_str for char in illegal_chars):
                QMessageBox.warning(self, "警告", f"目录名称包含非法字符: '{p_str}'！")
                return

            parts.append(p_str)

        config.custom_standard_dirs = parts
        config.save()
        show_toast(self, "自建分类模板已保存。", title="保存成功", level="success", duration=3600)
        self.refresh_other_views_signal.emit()

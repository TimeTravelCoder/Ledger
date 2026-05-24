import datetime
import os
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QFrame, QCheckBox, QTextEdit, 
                             QMessageBox, QStackedWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal, QSize
from config import config, normalize_tag, display_tag, NAME_PRESET_BASES
from db import db
from file_manager import FileManager
from ui.icon_utils import file_type_icon, line_icon, make_empty_item
from ui.toast import show_toast

STYLE_PREVIEW_NORMAL = """
    QLineEdit {
        font-size: 14px;
        font-weight: bold;
        color: #6366F1;
        background-color: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 6px;
        padding: 6px 10px;
    }
    QLineEdit:focus {
        border: 1px solid #4F46E5;
        background-color: rgba(99, 102, 241, 0.10);
    }
"""

STYLE_PREVIEW_WARNING = """
    QLineEdit {
        font-size: 14px;
        font-weight: bold;
        color: #EF4444;
        background-color: rgba(239, 68, 68, 0.05);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 6px;
        padding: 6px 10px;
    }
    QLineEdit:focus {
        background-color: rgba(239, 68, 68, 0.05);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 6px;
        padding: 6px 10px;
    }
    QLineEdit:focus {
        border: 1px solid #EF4444;
        background-color: rgba(239, 68, 68, 0.10);
    }
"""


class InboxView(QWidget):
    refresh_other_views_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file_path = None
        self.setAcceptDrops(True) # Accept drag-and-drop desktop imports
        self.init_ui()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            super().dropEvent(event)
            return
            
        import shutil
        active_inbox_name = config.get_inbox_name()
        inbox_path = Path(config.workspace_dir) / active_inbox_name
        inbox_path.mkdir(parents=True, exist_ok=True)
        
        imported_files = []
        for url in urls:
            local_file = Path(url.toLocalFile())
            if local_file.exists() and local_file.is_file():
                dest_file = inbox_path / local_file.name
                try:
                    if local_file.resolve() != dest_file.resolve():
                        shutil.copy2(local_file, dest_file)
                        imported_files.append(local_file.name)
                except Exception as e:
                    print(f"Error importing drag-dropped file: {e}")
                    
        if imported_files:
            show_toast(self, f"成功导入 {len(imported_files)} 个外部文件至收集箱！", title="导入成功", level="success", duration=3200)
            self.scan_inbox()
            # Select the newly imported file
            for idx in range(self.file_list_widget.count()):
                item = self.file_list_widget.item(idx)
                if item.text().endswith(imported_files[-1]):
                    self.file_list_widget.setCurrentRow(idx)
                    break
            self.refresh_other_views_signal.emit()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # Left Column: List of files in 00_Inbox
        left_panel = QFrame()
        left_panel.setObjectName("CardPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(15, 15, 15, 15)

        left_title = QLabel(f"待整理文件 ({config.get_inbox_name()} 目录)")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(left_title)

        self.file_list_widget = QListWidget()
        self.file_list_widget.setObjectName("FileList")
        self.file_list_widget.setIconSize(QSize(24, 24))
        self.file_list_widget.itemSelectionChanged.connect(self.on_file_selected)
        left_layout.addWidget(self.file_list_widget)

        self.scan_inbox_btn = QPushButton("扫描收集箱")
        self.scan_inbox_btn.setIcon(line_icon("refresh", size=16))
        self.scan_inbox_btn.setIconSize(QSize(16, 16))
        self.scan_inbox_btn.clicked.connect(self.scan_inbox)
        left_layout.addWidget(self.scan_inbox_btn)

        self.btn_merge_inboxes = QPushButton("一键合并双收集箱")
        self.btn_merge_inboxes.setObjectName("SuccessBtn")
        self.btn_merge_inboxes.setIcon(line_icon("inbox", "#FFFFFF", 16))
        self.btn_merge_inboxes.setIconSize(QSize(16, 16))
        self.btn_merge_inboxes.clicked.connect(self.merge_inboxes)
        left_layout.addWidget(self.btn_merge_inboxes)

        main_layout.addWidget(left_panel, 1)

        # Right Column: Organize Panel
        self.right_stack = QStackedWidget()
        
        # 1. Placeholder View
        self.placeholder_view = QFrame()
        self.placeholder_view.setObjectName("CardPanel")
        ph_layout = QVBoxLayout(self.placeholder_view)
        ph_label = QLabel("请将外部文件拖拽投放到此处进行一键导入\n或者从左侧列表选择文件分类整理")
        ph_label.setAlignment(Qt.AlignCenter)
        ph_label.setStyleSheet("color: #94A3B8; font-size: 14px; line-height: 1.6;")
        ph_layout.addWidget(ph_label)
        self.right_stack.addWidget(self.placeholder_view)

        # 2. Main Organize Form View
        self.form_panel = QFrame()
        self.form_panel.setObjectName("CardPanel")
        form_outer_layout = QVBoxLayout(self.form_panel)
        form_outer_layout.setContentsMargins(0, 0, 0, 0)
        form_outer_layout.setSpacing(0)
        
        # Add a scroll area inside the form card to prevent layout squeezing
        form_scroll = QScrollArea(self.form_panel)
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.NoFrame)
        form_scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        form_scroll_content = QWidget()
        form_scroll_content.setObjectName("FormScrollContent")
        form_scroll_content.setStyleSheet("#FormScrollContent { background: transparent; }")
        
        form_layout = QVBoxLayout(form_scroll_content)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(15, 15, 15, 15)
        
        form_scroll.setWidget(form_scroll_content)
        form_outer_layout.addWidget(form_scroll)

        form_title = QLabel("智能整理与文件改名助手")
        form_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        form_layout.addWidget(form_title)

        # Current name display
        self.lbl_curr_name = QLabel("原文件名: ")
        self.lbl_curr_name.setStyleSheet("color: #94A3B8; font-size: 12px;")
        form_layout.addWidget(self.lbl_curr_name)

        # Naming Presets Dropdown
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("命名规范模版:"))
        self.preset_combo = QComboBox()
        self.refresh_preset_combo()
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo, 1)
        form_layout.addLayout(preset_layout)

        # Dynamic name input fields container
        self.fields_container = QFrame()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setSpacing(8)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        
        # Row 1: Date
        self.row_date = QFrame()
        layout_date = QHBoxLayout(self.row_date)
        layout_date.setContentsMargins(0, 0, 0, 0)
        self.lbl_date = QLabel("日期 / 年份:")
        self.lbl_date.setFixedWidth(80)
        self.input_date = QLineEdit()
        layout_date.addWidget(self.lbl_date)
        layout_date.addWidget(self.input_date, 1)
        self.fields_layout.addWidget(self.row_date)
        
        # Row 2: Topic
        self.row_topic = QFrame()
        layout_topic = QHBoxLayout(self.row_topic)
        layout_topic.setContentsMargins(0, 0, 0, 0)
        self.lbl_topic = QLabel("主题 / 标题:")
        self.lbl_topic.setFixedWidth(80)
        self.input_topic = QLineEdit()
        layout_topic.addWidget(self.lbl_topic)
        layout_topic.addWidget(self.input_topic, 1)
        self.fields_layout.addWidget(self.row_topic)
        
        # Row 3: Version
        self.row_version = QFrame()
        layout_version = QHBoxLayout(self.row_version)
        layout_version.setContentsMargins(0, 0, 0, 0)
        self.lbl_version = QLabel("版本:")
        self.lbl_version.setFixedWidth(80)
        self.input_version = QLineEdit()
        layout_version.addWidget(self.lbl_version)
        layout_version.addWidget(self.input_version, 1)
        self.fields_layout.addWidget(self.row_version)
        
        # Row 4: Status
        self.row_status = QFrame()
        layout_status = QHBoxLayout(self.row_status)
        layout_status.setContentsMargins(0, 0, 0, 0)
        self.lbl_status = QLabel("状态:")
        self.lbl_status.setFixedWidth(80)
        self.input_status = QComboBox()
        self.input_status.addItems(["", "Draft", "Review", "Done", "Final", "Release"])
        layout_status.addWidget(self.lbl_status)
        layout_status.addWidget(self.input_status, 1)
        self.fields_layout.addWidget(self.row_status)
        
        # Row 5: Keep Info Row
        self.row_keep_info = QLabel("保持原有文件名称，只进行物理分类与标签元数据录入。")
        self.row_keep_info.setStyleSheet("color: #94A3B8; font-style: italic; font-size: 11px;")
        self.fields_layout.addWidget(self.row_keep_info)
        
        # Connect stable signals once
        self.input_date.textChanged.connect(self.update_name_preview)
        self.input_topic.textChanged.connect(self.update_name_preview)
        self.input_version.textChanged.connect(self.update_name_preview)
        self.input_status.currentIndexChanged.connect(self.update_name_preview)
        
        self.input_topic.textChanged.connect(self.update_semantic_recommendations)

        form_layout.addWidget(self.fields_container)

        # Name Preview & Live Rule Check
        preview_container = QFrame()
        preview_container.setObjectName("RenamePreviewCard")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        preview_layout.addWidget(QLabel("重命名预览 (可直接修改):"))
        self.lbl_name_preview = QLineEdit("name_preview.ext")
        self.lbl_name_preview.setStyleSheet(STYLE_PREVIEW_NORMAL)
        self.lbl_name_preview.textChanged.connect(self.run_live_checks)
        preview_layout.addWidget(self.lbl_name_preview)
        
        # Real-time warnings label
        self.lbl_naming_warning = QLabel("")
        self.lbl_naming_warning.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: bold;")
        self.lbl_naming_warning.setWordWrap(True)
        preview_layout.addWidget(self.lbl_naming_warning)

        form_layout.addWidget(preview_container)

        # Target Directory Choice
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("分类目标目录:"))
        self.dir_combo = QComboBox()
        self.refresh_directory_combo()
        self.dir_combo.currentIndexChanged.connect(self.update_name_preview)
        dir_layout.addWidget(self.dir_combo, 1)
        form_layout.addLayout(dir_layout)

        subfolder_layout = QHBoxLayout()
        subfolder_layout.addWidget(QLabel("子文件夹 (可选):"))
        self.input_subfolder = QLineEdit()
        self.input_subfolder.setPlaceholderText("例如: Math/LinearAlgebra (最多支持4层层级)")
        self.input_subfolder.textChanged.connect(self.update_name_preview)
        subfolder_layout.addWidget(self.input_subfolder)
        form_layout.addLayout(subfolder_layout)

        self.lbl_naming_warning.setWordWrap(True)
        preview_layout.addWidget(self.lbl_naming_warning)

        form_layout.addWidget(preview_container)

        # Target Directory Choice
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("分类目标目录:"))
        self.dir_combo = QComboBox()
        self.refresh_directory_combo()
        self.dir_combo.currentIndexChanged.connect(self.update_name_preview)
        dir_layout.addWidget(self.dir_combo, 1)
        form_layout.addLayout(dir_layout)

        subfolder_layout = QHBoxLayout()
        subfolder_layout.addWidget(QLabel("子文件夹 (可选):"))
        self.input_subfolder = QLineEdit()
        self.input_subfolder.setPlaceholderText("例如: Math/LinearAlgebra (最多支持4层层级)")
        self.input_subfolder.textChanged.connect(self.update_name_preview)
        subfolder_layout.addWidget(self.input_subfolder)
        form_layout.addLayout(subfolder_layout)

        # Tags Checklist (Dynamic Hot Refresh)
        tags_title = QLabel("选择分类标签 (多选)")
        tags_title.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 5px;")
        form_layout.addWidget(tags_title)

        self.tags_container = QFrame()
        self.tags_container_layout = QHBoxLayout(self.tags_container)
        self.tags_container_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addWidget(self.tags_container)
        
        self.build_tags_checklist()

        # Smart Semantic Recommendations Section
        self.recomm_container = QFrame()
        self.recomm_layout = QHBoxLayout(self.recomm_container)
        self.recomm_layout.setContentsMargins(0, 4, 0, 4)
        self.recomm_layout.setSpacing(8)
        
        recomm_title = QLabel("智能标签推荐:")
        recomm_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #94A3B8;")
        self.recomm_layout.addWidget(recomm_title)
        
        self.recomm_chips_layout = QHBoxLayout()
        self.recomm_chips_layout.setSpacing(6)
        self.recomm_layout.addLayout(self.recomm_chips_layout)
        self.recomm_layout.addStretch()
        
        form_layout.addWidget(self.recomm_container)

        # Description / Notes
        form_layout.addWidget(QLabel("备注 / 摘要 / 文献信息:"))
        self.input_desc = QTextEdit()
        self.input_desc.setFixedHeight(60)
        self.input_desc.setPlaceholderText("可在数据库中进行全文搜索，支持Obsidian笔记大纲...")
        self.input_desc.textChanged.connect(self.update_semantic_recommendations)
        form_layout.addWidget(self.input_desc)

        # Organize Button
        self.organize_btn = QPushButton("重命名并分类移动")
        self.organize_btn.setObjectName("PrimaryBtn")
        self.organize_btn.setIcon(line_icon("move", "#FFFFFF", 16))
        self.organize_btn.setIconSize(QSize(16, 16))
        self.organize_btn.clicked.connect(self.run_organize)
        form_layout.addWidget(self.organize_btn)

        self.right_stack.addWidget(self.form_panel)
        main_layout.addWidget(self.right_stack, 2)

        self.scan_inbox()

    def refresh_preset_combo(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_defs = []
        for base in NAME_PRESET_BASES:
            self.preset_defs.append({
                "label": base["label"],
                "format": base["default_format"],
                "prefix": base["prefix"],
                "key": base["key"],
                "custom": False
            })
        for item in getattr(config, "custom_name_templates", []):
            self.preset_defs.append({
                "label": item.get("label", "自定义模板"),
                "format": item.get("format", "{date}_{topic}"),
                "prefix": item.get("prefix", "01"),
                "key": "custom",
                "custom": True
            })
        for preset in self.preset_defs:
            self.preset_combo.addItem(preset["label"])
        self.preset_combo.blockSignals(False)

    def _preset_default_value(self, preset_key, field_key):
        today = datetime.datetime.now()
        defaults = {
            "date": today.strftime("%Y-%m-%d"),
            "topic": "",
            "version": "v1",
            "status": ""
        }
        if preset_key == "paper" and field_key == "date":
            defaults["date"] = today.strftime("%Y")
        elif preset_key == "exp" and field_key == "date":
            defaults["date"] = "Exp01"
        elif preset_key == "image" and field_key == "date":
            defaults["date"] = today.strftime("%Y%m%d")
        elif preset_key == "image" and field_key == "version":
            defaults["version"] = "01"
        return defaults[field_key]

    def render_template_name(self, fmt):
        date = self.input_date.text().strip() if self.row_date.isVisible() else ""
        topic = self.input_topic.text().strip() if self.row_topic.isVisible() else ""
        ver = self.input_version.text().strip() if self.row_version.isVisible() else ""
        status = self.input_status.currentText().strip() if self.row_status.isVisible() else ""
        stem = Path(self.selected_file_path).stem if self.selected_file_path else ""

        mapping = {
            "{date}": date,
            "{topic}": topic,
            "{version}": ver,
            "{status}": status,
            "{stem}": stem
        }
        result = fmt
        for key, value in mapping.items():
            result = result.replace(key, value)
        return "_".join([p for p in result.split("_") if p])

    def scan_inbox(self):
        self.file_list_widget.clear()
        
        inbox_dirs = []
        
        if config.use_custom_dirs and config.custom_standard_dirs:
            custom_inbox_name = config.get_inbox_name()
            custom_inbox_path = Path(config.workspace_dir) / custom_inbox_name
            self.btn_merge_inboxes.setVisible(False)
            if custom_inbox_path.exists() and custom_inbox_path.is_dir():
                inbox_dirs.append((custom_inbox_path, "自建"))
        else:
            inbox_cn = Path(config.workspace_dir) / "00收集箱"
            inbox_en = Path(config.workspace_dir) / "00Inbox"
            
            # Check if both exist to show merge button
            both_exist = inbox_cn.exists() and inbox_en.exists()
            self.btn_merge_inboxes.setVisible(both_exist)
            
            if inbox_cn.exists() and inbox_cn.is_dir():
                inbox_dirs.append((inbox_cn, "中文"))
            if inbox_en.exists() and inbox_en.is_dir():
                inbox_dirs.append((inbox_en, "英文"))
            
        # Fallback if none exist
        if not inbox_dirs:
            active_inbox = Path(config.workspace_dir) / config.get_inbox_name()
            active_inbox.mkdir(parents=True, exist_ok=True)
            inbox_dirs.append((active_inbox, "自建" if config.use_custom_dirs else ("中文" if config.workspace_lang == "cn" else "英文")))
            
        has_files = False
        try:
            for inbox_path, label in inbox_dirs:
                if not inbox_path.exists():
                    continue
                files = [f for f in os.listdir(inbox_path) if os.path.isfile(inbox_path / f)]
                for f in files:
                    if f.startswith(".") or f.startswith("~$"):
                        continue
                    display_name = f"[{label}] {f}" if len(inbox_dirs) > 1 else f
                    item = QListWidgetItem(display_name)
                    item.setIcon(file_type_icon(f))
                    item.setData(Qt.UserRole, str(inbox_path / f))
                    self.file_list_widget.addItem(item)
                    has_files = True
            
            # Select first item if any
            if has_files and self.file_list_widget.count() > 0:
                self.file_list_widget.setCurrentRow(0)
            else:
                self.file_list_widget.addItem(make_empty_item(
                    "收集箱暂无文件",
                    "可以从桌面一键导入，或把下载文件放进收集箱后点击扫描。",
                    "inbox",
                ))
                self.right_stack.setCurrentIndex(0)
        except Exception as e:
            print(f"Error scanning inbox: {e}")

    def on_file_selected(self):
        items = self.file_list_widget.selectedItems()
        if not items:
            self.selected_file_path = None
            self.right_stack.setCurrentIndex(0)
            return

        selected_item = items[0]
        self.selected_file_path = selected_item.data(Qt.UserRole)
        if not self.selected_file_path:
            self.right_stack.setCurrentIndex(0)
            return
        filename = Path(self.selected_file_path).name
        
        self.lbl_curr_name.setText(f"原文件名: {filename}")
        self.right_stack.setCurrentIndex(1)
        
        # Reset fields based on current preset
        self.reset_inputs_for_file(filename)
        self.update_name_preview()

    def reset_inputs_for_file(self, filename):
        # Default presets
        stem = Path(filename).stem
        
        # 1. Clean spaces/dashes for sanitization helper
        clean_stem = stem.replace(" ", "_").replace("-", "_")
        
        self.input_date.setText(datetime.datetime.now().strftime("%Y-%m-%d"))
        self.input_topic.setText(clean_stem)
        self.input_version.setText("v1")
        
        # Clear tags checkbox
        for cb in self.primary_checkboxes + self.secondary_checkboxes + self.status_checkboxes:
            cb.setChecked(False)
            
        self.input_desc.clear()
        
        # Guess template based on filename
        if "paper" in filename.lower() or "arxiv" in filename.lower():
            self.preset_combo.setCurrentIndex(1)  # Academic paper
        elif "exp" in filename.lower() or "experiment" in filename.lower() or "实验" in filename:
            self.preset_combo.setCurrentIndex(2)  # Lab report
        elif "ppt" in filename.lower() or "presentation" in filename.lower():
            self.preset_combo.setCurrentIndex(3)  # Slides
        else:
            self.preset_combo.setCurrentIndex(0)  # Regular template

    def on_preset_changed(self, idx):
        preset = self.preset_defs[idx]
        fmt = preset["format"]
        key = preset["key"]

        # Determine placeholder row visibility
        show_date = "{date}" in fmt
        show_topic = "{topic}" in fmt
        show_version = "{version}" in fmt
        show_status = "{status}" in fmt
        show_keep = (key == "keep")

        # Toggle inputs container visibility dynamically
        self.row_date.setVisible(show_date)
        self.row_topic.setVisible(show_topic)
        self.row_version.setVisible(show_version)
        self.row_status.setVisible(show_status)
        self.row_keep_info.setVisible(show_keep)

        # Set default text values gracefully without destroying fields
        if show_date:
            self.input_date.setText(self._preset_default_value(key, "date"))
            
        if show_version:
            version_label = "版本:" if key not in ["image"] else "序号:"
            self.lbl_version.setText(version_label)
            self.input_version.setText(self._preset_default_value(key, "version"))

        if show_topic:
            self.input_topic.clear()
            if self.selected_file_path:
                stem = Path(self.selected_file_path).stem
                clean_stem = stem.replace(" ", "_").replace("-", "_")
                self.input_topic.setText(clean_stem)

        if self.selected_file_path:
            if show_date and key == "paper":
                self.input_date.setText(datetime.datetime.now().strftime("%Y"))
            elif show_date and key == "image":
                self.input_date.setText(datetime.datetime.now().strftime("%Y%m%d"))
            elif show_date and key == "exp":
                self.input_date.setText("Exp01")
            elif show_date:
                self.input_date.setText(datetime.datetime.now().strftime("%Y-%m-%d"))

        self.select_combo_by_prefix(self.dir_combo, preset["prefix"])

        # Auto select checkboxes
        if key == "paper":
            for cb in self.secondary_checkboxes:
                if cb.property("tag_value") == normalize_tag("学术论文"):
                    cb.setChecked(True)
        elif key == "exp":
            for cb in self.secondary_checkboxes:
                if cb.property("tag_value") == normalize_tag("实验报告"):
                    cb.setChecked(True)

        self.update_name_preview()

    def update_name_preview(self):
        if not self.selected_file_path:
            return
            
        ext = Path(self.selected_file_path).suffix
        preset_idx = self.preset_combo.currentIndex()
        preset = self.preset_defs[preset_idx]
        
        new_stem = self.render_template_name(preset["format"])

        new_filename = new_stem + ext
        self.lbl_name_preview.blockSignals(True)
        self.lbl_name_preview.setText(new_filename)
        self.lbl_name_preview.blockSignals(False)
        self.run_live_checks()

    def run_live_checks(self):
        if not self.selected_file_path:
            return

        new_filename = self.lbl_name_preview.text().strip()
        warnings = []
        
        # 1. Banned keywords
        if FileManager.is_banned_name(new_filename):
            warnings.append("违规拦截：文件名中含有'最终版/最新版/新建文档'等禁用词，请修改！")
            self.lbl_name_preview.setStyleSheet(STYLE_PREVIEW_WARNING)
            self.organize_btn.setEnabled(False)
        else:
            self.lbl_name_preview.setStyleSheet(STYLE_PREVIEW_NORMAL)
            self.organize_btn.setEnabled(True)

        # 2. Check depth
        target_dir = self.dir_combo.currentText()
        subf = self.input_subfolder.text().strip().replace("\\", "/")
        dest_rel_path = f"{target_dir}/{subf}/{new_filename}" if subf else f"{target_dir}/{new_filename}"
        
        is_violation, depth = FileManager.check_folder_depth_violation(dest_rel_path)
        if is_violation:
            warnings.append(f"层级警告：当前目录深度为 {depth} 层，已超过规范建议的 ≤4 层！保存后可能会拦截。")
            self.organize_btn.setStyleSheet("background-color: #EF4444; border: none; color: #FFFFFF;")
        else:
            self.organize_btn.setStyleSheet("") # Default QSS style

        self.lbl_naming_warning.setText("\n".join(warnings))

    def run_organize(self):
        if not self.selected_file_path or not os.path.exists(self.selected_file_path):
            QMessageBox.critical(self, "错误", "未选择有效文件，或文件不存在。")
            return

        new_filename = self.lbl_name_preview.text()
        target_dir = self.dir_combo.currentText()
        subf = self.input_subfolder.text().strip().replace("\\", "/").strip("/")
        
        dest_rel_path = f"{target_dir}/{subf}/{new_filename}" if subf else f"{target_dir}/{new_filename}"

        # 1. Verify before move
        try:
            final_rel_path = FileManager.organize_file(self.selected_file_path, dest_rel_path, new_filename)
        except ValueError as ve:
            QMessageBox.warning(self, "规范拦截", str(ve))
            return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"文件移动失败: {str(e)}")
            return

        # 2. Extract selected tags
        selected_tags = []
        for cb in self.primary_checkboxes + self.secondary_checkboxes + self.status_checkboxes:
            if cb.isChecked():
                selected_tags.append(cb.property("tag_value") or normalize_tag(cb.text()))

        # 3. Update database tags and notes
        db.update_file_tags(final_rel_path, selected_tags)
        db.update_file_description(final_rel_path, self.input_desc.toPlainText().strip())

        # 4. Notify success and refresh lists
        show_toast(self, f"文件已整理归档到 {final_rel_path}。", title="整理完成", level="success", duration=3600)
        
        self.selected_file_path = None
        self.scan_inbox()
    def select_combo_by_prefix(self, combo, prefix):
        for i in range(combo.count()):
            if combo.itemText(i).startswith(prefix):
                combo.setCurrentIndex(i)
                break

    def merge_inboxes(self):
        inbox_cn = Path(config.workspace_dir) / "00收集箱"
        inbox_en = Path(config.workspace_dir) / "00Inbox"
        
        if not (inbox_cn.exists() and inbox_en.exists()):
            return
            
        active_inbox_name = config.get_inbox_name()
        active_dir = Path(config.workspace_dir) / active_inbox_name
        inactive_dir = inbox_en if active_inbox_name == "00收集箱" else inbox_cn
        
        reply = QMessageBox.question(
            self, "确认一键合并收集箱",
            f"系统检测到您的工作空间里有中、英两个收集箱文件夹。\n\n"
            f"是否确认将非激活状态收集箱（{inactive_dir.name}）中的所有待整理文件一键合并迁移至当前激活的收集箱（{active_dir.name}），并删除空的旧文件夹？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            moved_count = 0
            try:
                for f in os.listdir(inactive_dir):
                    src_file = inactive_dir / f
                    if src_file.is_file():
                        dest_file = active_dir / f
                        import shutil
                        from file_manager import FileManager
                        FileManager.move_replace(src_file, dest_file, replace=False)
                        moved_count += 1
                
                # Delete empty inactive dir
                if not os.listdir(inactive_dir):
                    import shutil
                    shutil.rmtree(inactive_dir)
                else:
                    os.rmdir(inactive_dir)
                    
                show_toast(self, f"已合并 {moved_count} 个待整理文件到 {active_dir.name}。", title="合并成功", level="success", duration=3600)
            except Exception as e:
                QMessageBox.critical(self, "合并失败", f"合并中途发生错误:\n{str(e)}")
                
            self.scan_inbox()
            self.refresh_other_views_signal.emit()

    def refresh_directory_combo(self):
        # Block signals to avoid triggering name preview updates while reloading
        self.dir_combo.blockSignals(True)
        self.dir_combo.clear()
        inbox_name = config.get_inbox_name()
        for d in config.get_standard_dirs():
            if d != inbox_name:
                self.dir_combo.addItem(d)
        self.dir_combo.blockSignals(False)

    def build_tags_checklist(self):
        # 1. Clear existing items from self.tags_container_layout
        for i in reversed(range(self.tags_container_layout.count())):
            item = self.tags_container_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        # 2. Re-create columns
        # Primary Tags
        p_frame = QFrame()
        p_layout = QVBoxLayout(p_frame)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.addWidget(QLabel("一级分类:"))
        self.primary_checkboxes = []
        for t in config.tags["primary"]:
            cb = QCheckBox(display_tag(t))
            cb.setProperty("tag_value", normalize_tag(t))
            cb.stateChanged.connect(lambda state: self.update_semantic_recommendations())
            p_layout.addWidget(cb)
            self.primary_checkboxes.append(cb)
        self.tags_container_layout.addWidget(p_frame)

        # Secondary Tags
        s_frame = QFrame()
        s_layout = QVBoxLayout(s_frame)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.addWidget(QLabel("二级属性:"))
        self.secondary_checkboxes = []
        for t in config.tags["secondary"]:
            cb = QCheckBox(display_tag(t))
            cb.setProperty("tag_value", normalize_tag(t))
            cb.stateChanged.connect(lambda state: self.update_semantic_recommendations())
            s_layout.addWidget(cb)
            self.secondary_checkboxes.append(cb)
        self.tags_container_layout.addWidget(s_frame)

        # Status Tags
        st_frame = QFrame()
        st_layout = QVBoxLayout(st_frame)
        st_layout.setContentsMargins(0, 0, 0, 0)
        st_layout.addWidget(QLabel("状态标记:"))
        self.status_checkboxes = []
        for t in config.tags["status"]:
            cb = QCheckBox(display_tag(t))
            cb.setProperty("tag_value", normalize_tag(t))
            cb.stateChanged.connect(lambda state: self.update_semantic_recommendations())
            st_layout.addWidget(cb)
            self.status_checkboxes.append(cb)
        self.tags_container_layout.addWidget(st_frame)

    def update_semantic_recommendations(self):
        if not hasattr(self, "recomm_chips_layout"):
            return
            
        # 1. Clear previous chips
        for i in reversed(range(self.recomm_chips_layout.count())):
            item = self.recomm_chips_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
                
        # 2. Get recommendations
        topic = self.input_topic.text().strip()
        desc = self.input_desc.toPlainText().strip()
        
        # If both are empty, fallback to current filename
        if not topic and not desc and self.selected_file_path:
            topic = Path(self.selected_file_path).stem
            
        try:
            from semantic_analyzer import SemanticAnalyzer
            recommended_tags = SemanticAnalyzer.recommend_tags(topic, desc, top_k=3)
        except Exception as e:
            print(f"Error loading SemanticAnalyzer: {e}")
            recommended_tags = []
            
        theme = config.theme
        
        # 3. Create chips
        for tag in recommended_tags:
            # Check if tag is currently active
            is_checked = False
            for cb in self.primary_checkboxes + self.secondary_checkboxes + self.status_checkboxes:
                if cb.property("tag_value") == tag or cb.text() == tag.lstrip("#"):
                    is_checked = cb.isChecked()
                    break
                    
            btn = QPushButton(tag)
            btn.setObjectName("SemanticChip")
            btn.setProperty("tag_value", tag)
            
            # Premium glowing chip design
            if is_checked:
                # Active glowing state
                if theme == "dark":
                    btn.setStyleSheet("background-color: #6366F1; border: 1px solid #6366F1; color: #FFFFFF; font-size: 11px; font-weight: bold; border-radius: 10px; padding: 2px 8px;")
                elif theme == "zhongguose":
                    btn.setStyleSheet("background-color: #047857; border: 1px solid #047857; color: #FFFFFF; font-size: 11px; font-weight: bold; border-radius: 10px; padding: 2px 8px;")
                else:
                    btn.setStyleSheet("background-color: #4F46E5; border: 1px solid #4F46E5; color: #FFFFFF; font-size: 11px; font-weight: bold; border-radius: 10px; padding: 2px 8px;")
            else:
                # Inactive outlined state
                if theme == "dark":
                    btn.setStyleSheet("background-color: rgba(99, 102, 241, 0.08); border: 1px dashed rgba(99, 102, 241, 0.4); color: #818CF8; font-size: 11px; border-radius: 10px; padding: 2px 8px;")
                elif theme == "zhongguose":
                    btn.setStyleSheet("background-color: rgba(4, 120, 87, 0.08); border: 1px dashed rgba(4, 120, 87, 0.4); color: #059669; font-size: 11px; border-radius: 10px; padding: 2px 8px;")
                else:
                    btn.setStyleSheet("background-color: rgba(79, 70, 229, 0.06); border: 1px dashed rgba(79, 70, 229, 0.3); color: #4F46E5; font-size: 11px; border-radius: 10px; padding: 2px 8px;")
                    
            btn.setCursor(Qt.PointingHandCursor)
            # Safe binding
            btn.clicked.connect(lambda checked=False, t=tag: self.toggle_tag_checkbox(t))
            self.recomm_chips_layout.addWidget(btn)

    def toggle_tag_checkbox(self, tag_val):
        for cb in self.primary_checkboxes + self.secondary_checkboxes + self.status_checkboxes:
            if cb.property("tag_value") == tag_val or cb.text() == tag_val.lstrip("#"):
                cb.setChecked(not cb.isChecked())
        self.update_semantic_recommendations()

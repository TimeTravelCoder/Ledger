import datetime
import os
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QFrame, QCheckBox, QTextEdit, 
                             QMessageBox, QStackedWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal
from config import config, normalize_tag, display_tag
from db import db
from file_manager import FileManager

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
        border: 1px solid #EF4444;
        background-color: rgba(239, 68, 68, 0.10);
    }
"""


class InboxView(QWidget):
    refresh_other_views_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file_path = None
        self.init_ui()

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
        self.file_list_widget.setStyleSheet("border: none;")
        self.file_list_widget.itemSelectionChanged.connect(self.on_file_selected)
        left_layout.addWidget(self.file_list_widget)

        self.scan_inbox_btn = QPushButton("扫描收集箱")
        self.scan_inbox_btn.clicked.connect(self.scan_inbox)
        left_layout.addWidget(self.scan_inbox_btn)

        self.btn_merge_inboxes = QPushButton("一键合并双收集箱")
        self.btn_merge_inboxes.setObjectName("SuccessBtn")
        self.btn_merge_inboxes.clicked.connect(self.merge_inboxes)
        left_layout.addWidget(self.btn_merge_inboxes)

        main_layout.addWidget(left_panel, 1)

        # Right Column: Organize Panel
        self.right_stack = QStackedWidget()
        
        # 1. Placeholder View
        self.placeholder_view = QFrame()
        self.placeholder_view.setObjectName("CardPanel")
        ph_layout = QVBoxLayout(self.placeholder_view)
        ph_label = QLabel("请从左侧列表选择一个文件进行分类整理\n或者点击“扫描收集箱”刷新")
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
        self.preset_combo.addItems([
            "常规模版 (日期_主题_版本_状态)",
            "学术论文 (年份_论文名_作者)",
            "实验报告 (Exp序号_学科_实验名_版本)",
            "幻灯片 (日期_PPT名_版本)",
            "实验图片 (日期_图片名_序号)",
            "保持原名"
        ])
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo, 1)
        form_layout.addLayout(preset_layout)

        # Dynamic name input fields
        self.fields_container = QFrame()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setSpacing(8)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        
        # Initialize inputs
        self.input_date = QLineEdit()
        self.input_topic = QLineEdit()
        self.input_version = QLineEdit()
        self.input_status = QComboBox()
        
        self.input_date.textChanged.connect(self.update_name_preview)
        self.input_topic.textChanged.connect(self.update_name_preview)
        self.input_version.textChanged.connect(self.update_name_preview)
        self.input_status.currentIndexChanged.connect(self.update_name_preview)

        form_layout.addWidget(self.fields_container)

        # Name Preview & Live Rule Check
        preview_container = QFrame()
        preview_container.setStyleSheet("background-color: rgba(99, 102, 241, 0.05); border-radius: 8px; border: 1px dashed rgba(99, 102, 241, 0.3);")
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

        # Tags Checklist (Dynamic Hot Refresh)
        tags_title = QLabel("选择分类标签 (多选)")
        tags_title.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 5px;")
        form_layout.addWidget(tags_title)

        self.tags_container = QFrame()
        self.tags_container_layout = QHBoxLayout(self.tags_container)
        self.tags_container_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addWidget(self.tags_container)
        
        self.build_tags_checklist()

        # Description / Notes
        form_layout.addWidget(QLabel("备注 / 摘要 / 文献信息:"))
        self.input_desc = QTextEdit()
        self.input_desc.setFixedHeight(60)
        self.input_desc.setPlaceholderText("可在数据库中进行全文搜索，支持Obsidian笔记大纲...")
        form_layout.addWidget(self.input_desc)

        # Organize Button
        self.organize_btn = QPushButton("重命名并分类移动")
        self.organize_btn.setObjectName("PrimaryBtn")
        self.organize_btn.clicked.connect(self.run_organize)
        form_layout.addWidget(self.organize_btn)

        self.right_stack.addWidget(self.form_panel)
        main_layout.addWidget(self.right_stack, 2)

        self.scan_inbox()

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
                    item.setData(Qt.UserRole, str(inbox_path / f))
                    self.file_list_widget.addItem(item)
                    has_files = True
            
            # Select first item if any
            if has_files and self.file_list_widget.count() > 0:
                self.file_list_widget.setCurrentRow(0)
            else:
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
        filename = selected_item.text()
        
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
        # Clear old dynamic inputs
        for i in reversed(range(self.fields_layout.count())): 
            self.fields_layout.itemAt(i).widget().setParent(None)

        self.input_status.disconnect() if hasattr(self, 'input_status') else None
        
        # Create fields based on selection
        if idx == 0:  # Regular (Date_Topic_Version_Status)
            h1 = QHBoxLayout()
            h1.addWidget(QLabel("日期:"))
            self.input_date = QLineEdit(datetime.datetime.now().strftime("%Y-%m-%d"))
            h1.addWidget(self.input_date)
            
            h2 = QHBoxLayout()
            h2.addWidget(QLabel("主题名称 (建议无空格):"))
            self.input_topic = QLineEdit()
            h2.addWidget(self.input_topic)
            
            h3 = QHBoxLayout()
            h3.addWidget(QLabel("版本 (如 v1/v2/v1.0):"))
            self.input_version = QLineEdit("v1")
            h3.addWidget(self.input_version)
            
            h4 = QHBoxLayout()
            h4.addWidget(QLabel("状态:"))
            self.input_status = QComboBox()
            self.input_status.addItems(["", "Draft", "Review", "Done", "Final", "Release"])
            h4.addWidget(self.input_status, 1)

            self.fields_layout.addLayout(h1)
            self.fields_layout.addLayout(h2)
            self.fields_layout.addLayout(h3)
            self.fields_layout.addLayout(h4)

            # Auto connections
            self.input_date.textChanged.connect(self.update_name_preview)
            self.input_topic.textChanged.connect(self.update_name_preview)
            self.input_version.textChanged.connect(self.update_name_preview)
            self.input_status.currentIndexChanged.connect(self.update_name_preview)
            
            # Select target folder starting with 01 (Study)
            self.select_combo_by_prefix(self.dir_combo, "01")

        elif idx == 1:  # Paper (Year_PaperTitle_Author)
            h1 = QHBoxLayout()
            h1.addWidget(QLabel("发表年份:"))
            self.input_date = QLineEdit(datetime.datetime.now().strftime("%Y"))
            h1.addWidget(self.input_date)
            
            h2 = QHBoxLayout()
            h2.addWidget(QLabel("论文标题 (首字母大写CamelCase):"))
            self.input_topic = QLineEdit()
            h2.addWidget(self.input_topic)
            
            h3 = QHBoxLayout()
            h3.addWidget(QLabel("第一作者姓氏 (英文):"))
            self.input_version = QLineEdit()
            h3.addWidget(self.input_version)

            self.fields_layout.addLayout(h1)
            self.fields_layout.addLayout(h2)
            self.fields_layout.addLayout(h3)

            self.input_date.textChanged.connect(self.update_name_preview)
            self.input_topic.textChanged.connect(self.update_name_preview)
            self.input_version.textChanged.connect(self.update_name_preview)
            
            self.select_combo_by_prefix(self.dir_combo, "05")
            
            # Set default tag
            for cb in self.secondary_checkboxes:
                if cb.property("tag_value") == normalize_tag("学术论文"):
                    cb.setChecked(True)

        elif idx == 2:  # Exp Report (Exp序号_学科_实验名_版本)
            h1 = QHBoxLayout()
            h1.addWidget(QLabel("实验编号 (如 Exp01):"))
            self.input_date = QLineEdit("Exp01")
            h1.addWidget(self.input_date)
            
            h2 = QHBoxLayout()
            h2.addWidget(QLabel("学科与实验名称 (如 MPI_VectorAdd):"))
            self.input_topic = QLineEdit()
            h2.addWidget(self.input_topic)
            
            h3 = QHBoxLayout()
            h3.addWidget(QLabel("版本 (如 v1/v2):"))
            self.input_version = QLineEdit("v1")
            h3.addWidget(self.input_version)

            self.fields_layout.addLayout(h1)
            self.fields_layout.addLayout(h2)
            self.fields_layout.addLayout(h3)

            self.input_date.textChanged.connect(self.update_name_preview)
            self.input_topic.textChanged.connect(self.update_name_preview)
            self.input_version.textChanged.connect(self.update_name_preview)
            
            self.select_combo_by_prefix(self.dir_combo, "01")
            
            # Set default tag
            for cb in self.secondary_checkboxes:
                if cb.property("tag_value") == normalize_tag("实验报告"):
                    cb.setChecked(True)

        elif idx == 3:  # Slides (Date_PPT名_版本)
            h1 = QHBoxLayout()
            h1.addWidget(QLabel("汇报日期:"))
            self.input_date = QLineEdit(datetime.datetime.now().strftime("%Y-%m-%d"))
            h1.addWidget(self.input_date)
            
            h2 = QHBoxLayout()
            h2.addWidget(QLabel("汇报主题/幻灯片名:"))
            self.input_topic = QLineEdit()
            h2.addWidget(self.input_topic)
            
            h3 = QHBoxLayout()
            h3.addWidget(QLabel("版本 (如 v1/v2):"))
            self.input_version = QLineEdit("v1")
            h3.addWidget(self.input_version)

            self.fields_layout.addLayout(h1)
            self.fields_layout.addLayout(h2)
            self.fields_layout.addLayout(h3)

            self.input_date.textChanged.connect(self.update_name_preview)
            self.input_topic.textChanged.connect(self.update_name_preview)
            self.input_version.textChanged.connect(self.update_name_preview)
            
            self.select_combo_by_prefix(self.dir_combo, "08")

        elif idx == 4:  # Image (Date_图片名_序号)
            h1 = QHBoxLayout()
            h1.addWidget(QLabel("拍摄/生成日期:"))
            self.input_date = QLineEdit(datetime.datetime.now().strftime("%Y%m%d"))
            h1.addWidget(self.input_date)
            
            h2 = QHBoxLayout()
            h2.addWidget(QLabel("图片描述名称 (英文):"))
            self.input_topic = QLineEdit()
            h2.addWidget(self.input_topic)
            
            h3 = QHBoxLayout()
            h3.addWidget(QLabel("序号 (如 01/02):"))
            self.input_version = QLineEdit("01")
            h3.addWidget(self.input_version)

            self.fields_layout.addLayout(h1)
            self.fields_layout.addLayout(h2)
            self.fields_layout.addLayout(h3)

            self.input_date.textChanged.connect(self.update_name_preview)
            self.input_topic.textChanged.connect(self.update_name_preview)
            self.input_version.textChanged.connect(self.update_name_preview)
            
            self.select_combo_by_prefix(self.dir_combo, "07")

        elif idx == 5:  # Keep Original
            self.fields_layout.addWidget(QLabel("保持原有文件名称，只进行物理分类与标签元数据录入。"))
            if self.selected_file_path:
                self.input_topic = QLineEdit(Path(self.selected_file_path).stem)

        if self.selected_file_path:
            # Re-sanitize topic inputs
            stem = Path(self.selected_file_path).stem
            clean_stem = stem.replace(" ", "_").replace("-", "_")
            if idx in [0, 1, 2, 3, 4] and hasattr(self, 'input_topic'):
                self.input_topic.setText(clean_stem)

        self.update_name_preview()

    def update_name_preview(self):
        if not self.selected_file_path:
            return
            
        ext = Path(self.selected_file_path).suffix
        preset_idx = self.preset_combo.currentIndex()
        
        new_stem = ""
        
        if preset_idx == 0:  # Date_Topic_Version_Status
            date = self.input_date.text().strip()
            topic = self.input_topic.text().strip()
            ver = self.input_version.text().strip()
            status = self.input_status.currentText().strip()
            
            parts = [p for p in [date, topic, ver, status] if p]
            new_stem = "_".join(parts)
            
        elif preset_idx == 1:  # Year_PaperTitle_Author
            year = self.input_date.text().strip()
            title = self.input_topic.text().strip().replace(" ", "")  # Force camel case/no space
            author = self.input_version.text().strip()
            
            parts = [p for p in [year, title, author] if p]
            new_stem = "_".join(parts)
            
        elif preset_idx == 2:  # Exp01_MPI_VectorAdd_v2
            exp_id = self.input_date.text().strip()
            exp_name = self.input_topic.text().strip().replace(" ", "_")
            ver = self.input_version.text().strip()
            
            parts = [p for p in [exp_id, exp_name, ver] if p]
            new_stem = "_".join(parts)
            
        elif preset_idx == 3:  # Date_QuantumPresentation_v3
            date = self.input_date.text().strip()
            ppt_name = self.input_topic.text().strip().replace(" ", "")
            ver = self.input_version.text().strip()
            
            parts = [p for p in [date, ppt_name, ver] if p]
            new_stem = "_".join(parts)
            
        elif preset_idx == 4:  # Date_Experiment_Result01
            date = self.input_date.text().strip()
            img_name = self.input_topic.text().strip().replace(" ", "_")
            seq = self.input_version.text().strip()
            
            parts = [p for p in [date, img_name, seq] if p]
            new_stem = f"{date}_{img_name}{seq}" if date and img_name else "_".join(parts)
            
        elif preset_idx == 5:  # Keep original
            new_stem = Path(self.selected_file_path).stem

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
            warnings.append("❌ 违规拦截：文件名中含有'最终版/最新版/新建文档'等禁用词，请修改！")
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
            warnings.append(f"⚠️ 层级警告：当前目录深度为 {depth} 层，已超过规范建议的 ≤4 层！保存后可能会拦截。")
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
        QMessageBox.information(self, "整理完成", f"文件已成功整理归档！\n目标路径: {final_rel_path}")
        
        self.selected_file_path = None
        self.scan_inbox()
        self.refresh_other_views_signal.emit()

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
                        FileManager.move_replace(src_file, dest_file)
                        moved_count += 1
                
                # Delete empty inactive dir
                if not os.listdir(inactive_dir):
                    shutil.rmtree(inactive_dir)
                else:
                    os.rmdir(inactive_dir)
                    
                QMessageBox.information(self, "合并成功 🎉", f"已成功将 {moved_count} 个待整理文件合并移动到 '{active_dir.name}' 中，并清空删除了旧收集箱！")
            except Exception as e:
                QMessageBox.critical(self, "合并失败", f"合并中途发生错误:\n{str(e)}")
                
            self.scan_inbox()
            self.refresh_other_views_signal.emit()

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
            st_layout.addWidget(cb)
            self.status_checkboxes.append(cb)
        self.tags_container_layout.addWidget(st_frame)

    def refresh_directory_combo(self):
        # Block signals to avoid triggering name preview updates while reloading
        self.dir_combo.blockSignals(True)
        self.dir_combo.clear()
        inbox_name = config.get_inbox_name()
        for d in config.get_standard_dirs():
            if d != inbox_name:
                self.dir_combo.addItem(d)
        self.dir_combo.blockSignals(False)

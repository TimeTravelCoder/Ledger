import os
import datetime
import shutil
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeView, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLabel, QLineEdit, QPushButton, QFrame, 
                             QFileSystemModel, QDialog, QCheckBox, QTextEdit, 
                             QMessageBox, QComboBox, QGridLayout, QInputDialog)
from PySide6.QtCore import Qt, QModelIndex, Signal, QDir
from config import config, display_tag, normalize_tag
from db import db
from file_manager import FileManager

class WorkspaceTableWidget(QTableWidget):
    left_double_clicked = Signal(QModelIndex)
    right_double_clicked = Signal(QModelIndex)

    def mouseDoubleClickEvent(self, event):
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        index = self.indexAt(pos)
        if index.isValid():
            if event.button() == Qt.LeftButton:
                self.left_double_clicked.emit(index)
            elif event.button() == Qt.RightButton:
                self.right_double_clicked.emit(index)
        super().mouseDoubleClickEvent(event)

# Custom Dialog for creating a new file under standard workspace directories
class CreateFileDialog(QDialog):
    def __init__(self, current_folder_rel, parent=None):
        super().__init__(parent)
        self.current_folder_rel = current_folder_rel
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("创建新文档 / 文件")
        self.setMinimumWidth(480)
        self.setStyleSheet(self.parent().parent().styleSheet()) # Inherit theme stylesheet

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title Label
        title_lbl = QLabel("📂 新建工作空间文档")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #6366F1; margin-bottom: 5px;")
        layout.addWidget(title_lbl)

        # 1. Target Directory display
        dir_layout = QHBoxLayout()
        dir_lbl = QLabel("目标归档目录:")
        dir_lbl.setFixedWidth(100)
        dir_layout.addWidget(dir_lbl)
        self.dir_combo = QComboBox()
        
        # Populate all standard directories
        inbox_name = config.get_inbox_name()
        standard_dirs = config.get_standard_dirs()
        for d in standard_dirs:
            if d != inbox_name:
                self.dir_combo.addItem(d)
        
        # Pre-select based on currently open folder
        if self.current_folder_rel:
            # Find matching index
            for idx in range(self.dir_combo.count()):
                if self.dir_combo.itemText(idx).split("/")[0] == self.current_folder_rel.split("/")[0]:
                    self.dir_combo.setCurrentIndex(idx)
                    break
        dir_layout.addWidget(self.dir_combo, 1)
        layout.addLayout(dir_layout)

        # 2. Optional Subfolder field
        sub_layout = QHBoxLayout()
        sub_lbl = QLabel("子文件夹路径:")
        sub_lbl.setFixedWidth(100)
        sub_layout.addWidget(sub_lbl)
        self.input_subfolder = QLineEdit()
        # Extract existing nested subdirectory if any
        if self.current_folder_rel:
            parts = self.current_folder_rel.split("/")
            if len(parts) > 1:
                self.input_subfolder.setText("/".join(parts[1:]))
        self.input_subfolder.setPlaceholderText("例如: Math/Calculus (可选，自动创建)")
        sub_layout.addWidget(self.input_subfolder, 1)
        layout.addLayout(sub_layout)

        # 3. Filename field
        name_layout = QHBoxLayout()
        name_lbl = QLabel("文档名称:")
        name_lbl.setFixedWidth(100)
        name_layout.addWidget(name_lbl)
        self.input_filename = QLineEdit()
        self.input_filename.setPlaceholderText("输入文件名")
        name_layout.addWidget(self.input_filename, 1)
        
        # 4. File extension dropdown
        self.ext_combo = QComboBox()
        self.ext_combo.addItems([
            ".md (Markdown 文档)",
            ".txt (纯文本文件)",
            ".docx (Word 文档)",
            ".xlsx (Excel 表格)",
            ".pptx (PPT 幻灯片)",
            "自定义后缀"
        ])
        self.ext_combo.currentIndexChanged.connect(self.on_ext_changed)
        name_layout.addWidget(self.ext_combo)
        
        # Hidden custom extension field
        self.input_custom_ext = QLineEdit()
        self.input_custom_ext.setPlaceholderText(".pdf")
        self.input_custom_ext.setVisible(False)
        self.input_custom_ext.setFixedWidth(60)
        name_layout.addWidget(self.input_custom_ext)
        layout.addLayout(name_layout)

        # 5. Optional Initial Content
        layout.addWidget(QLabel("<b>文档初始内容 (可选，建档时自动写入):</b>"))
        self.input_content = QTextEdit()
        self.input_content.setPlaceholderText("在此处可以输入初始文档大纲、总结或备注信息...")
        self.input_content.setFixedHeight(120)
        layout.addWidget(self.input_content)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_confirm = QPushButton("确认创建")
        self.btn_confirm.setObjectName("PrimaryBtn")
        self.btn_confirm.clicked.connect(self.create_file)
        btn_layout.addWidget(self.btn_confirm)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def on_ext_changed(self, index):
        self.input_custom_ext.setVisible(index == 5)

    def create_file(self):
        filename = self.input_filename.text().strip()
        if not filename:
            QMessageBox.warning(self, "警告", "文件名不能为空！")
            return

        # Figure out extension
        ext_idx = self.ext_combo.currentIndex()
        if ext_idx == 0:
            ext = ".md"
        elif ext_idx == 1:
            ext = ".txt"
        elif ext_idx == 2:
            ext = ".docx"
        elif ext_idx == 3:
            ext = ".xlsx"
        elif ext_idx == 4:
            ext = ".pptx"
        else:
            ext = self.input_custom_ext.text().strip()
            if not ext.startswith("."):
                ext = f".{ext}"
            if len(ext) <= 1:
                QMessageBox.warning(self, "警告", "请输入有效的自定义文件后缀！")
                return

        # Ensure filename has extension
        if not filename.endswith(ext):
            filename = f"{filename}{ext}"

        # Check banned name
        if FileManager.is_banned_name(filename):
            QMessageBox.warning(self, "规范拦截", "文件名包含'最终版/新建文档'等违规字词，请重新命名！")
            return

        # Target relative path calculation
        target_dir = self.dir_combo.currentText()
        subf = self.input_subfolder.text().strip().replace("\\", "/").strip("/")
        
        dest_rel_path = f"{target_dir}/{subf}/{filename}" if subf else f"{target_dir}/{filename}"

        # Check depth violation
        is_violation, depth = FileManager.check_folder_depth_violation(dest_rel_path)
        if is_violation:
            QMessageBox.warning(self, "深度超出规范", f"当前路径深度为 {depth} 层，已超过 4 层上限，无法在此处创建文件！")
            return

        # Run creation
        content = self.input_content.toPlainText()
        success, msg = FileManager.create_file(dest_rel_path, content)
        
        if success:
            FileManager.scan_workspace_files()
            QMessageBox.information(self, "创建成功 🎉", f"文件已成功在工作空间创建并同步入库！\n路径: {dest_rel_path}")
            self.accept()
        else:
            QMessageBox.critical(self, "创建失败", msg)


# ─────────────────────────────────────────────────────────────────────────────
# Create Folder Dialog
# ─────────────────────────────────────────────────────────────────────────────
class CreateFolderDialog(QDialog):
    """Premium dialog to create a new folder under a standard workspace directory."""

    def __init__(self, current_folder_rel: str, parent=None):
        super().__init__(parent)
        self.current_folder_rel = current_folder_rel
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("新建文件夹")
        self.setMinimumWidth(500)
        try:
            self.setStyleSheet(self.parent().parent().styleSheet())
        except Exception:
            pass

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 20)

        # ── Title ──────────────────────────────────────────────────────────
        title_lbl = QLabel("📁 在工作空间中新建文件夹")
        title_lbl.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #6366F1; margin-bottom: 4px;"
        )
        layout.addWidget(title_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #4A6FA6;")
        layout.addWidget(sep)

        # ── Form grid ──────────────────────────────────────────────────────
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)
        form.setColumnStretch(1, 1)

        # Row 0: Target root directory
        lbl_root = QLabel("归档根目录:")
        lbl_root.setStyleSheet("font-weight: bold;")
        form.addWidget(lbl_root, 0, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.dir_combo = QComboBox()
        inbox_name = config.get_inbox_name()
        standard_dirs = config.get_standard_dirs()
        for d in standard_dirs:
            if d != inbox_name:
                self.dir_combo.addItem(d)

        # Pre-select directory matching current tree selection
        if self.current_folder_rel:
            top_level = self.current_folder_rel.split("/")[0]
            for idx in range(self.dir_combo.count()):
                if self.dir_combo.itemText(idx) == top_level:
                    self.dir_combo.setCurrentIndex(idx)
                    break
        form.addWidget(self.dir_combo, 0, 1)

        # Row 1: Subfolder path (within root)
        lbl_sub = QLabel("已有子目录路径:")
        lbl_sub.setStyleSheet("font-weight: bold;")
        form.addWidget(lbl_sub, 1, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.input_subpath = QLineEdit()
        self.input_subpath.setPlaceholderText("例如: 项目/2024  (留空则直接在根目录下创建)")
        # Pre-fill existing nested path if any
        if self.current_folder_rel:
            parts = self.current_folder_rel.split("/")
            if len(parts) > 1:
                self.input_subpath.setText("/".join(parts[1:]))
        form.addWidget(self.input_subpath, 1, 1)

        # Row 2: New folder name
        lbl_name = QLabel("新文件夹名称:")
        lbl_name.setStyleSheet("font-weight: bold;")
        form.addWidget(lbl_name, 2, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("请输入新文件夹的名称")
        form.addWidget(self.input_name, 2, 1)

        layout.addLayout(form)

        # ── Depth hint label ───────────────────────────────────────────────
        self.hint_lbl = QLabel("📏 最终路径预览: —")
        self.hint_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; padding-left: 4px;")
        layout.addWidget(self.hint_lbl)

        # Connect live preview
        self.dir_combo.currentTextChanged.connect(self._update_preview)
        self.input_subpath.textChanged.connect(self._update_preview)
        self.input_name.textChanged.connect(self._update_preview)
        self._update_preview()

        # ── Buttons ────────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_confirm = QPushButton("✅  确认创建")
        self.btn_confirm.setObjectName("PrimaryBtn")
        self.btn_confirm.clicked.connect(self.do_create_folder)
        btn_layout.addWidget(self.btn_confirm)

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    # ── Helpers ───────────────────────────────────────────────────────────
    def _build_rel_path(self) -> str:
        root = self.dir_combo.currentText().strip()
        sub = self.input_subpath.text().strip().replace("\\", "/").strip("/")
        name = self.input_name.text().strip()
        if sub:
            return f"{root}/{sub}/{name}"
        return f"{root}/{name}"

    def _update_preview(self):
        rel = self._build_rel_path()
        if not self.input_name.text().strip():
            self.hint_lbl.setText("📏 最终路径预览: —")
            return
        depth = len([p for p in rel.split("/") if p])
        color = "#F97316" if depth > 4 else "#34D399"
        self.hint_lbl.setText(
            f"📏 最终路径: <b style='color:{color};'>{rel}</b>  "
            f"<span style='color:{color};'>(深度 {depth}/4 层)</span>"
        )

    # ── Action ────────────────────────────────────────────────────────────
    def do_create_folder(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "文件夹名称不能为空！")
            return

        # Sanity: no path separators in name itself
        if "/" in name or "\\" in name:
            QMessageBox.warning(self, "提示", "文件夹名称中不能包含路径分隔符，请使用「已有子目录路径」字段指定父级路径！")
            return

        rel_path = self._build_rel_path()
        success, msg = FileManager.create_folder(rel_path)

        if success:
            QMessageBox.information(self, "创建成功 🎉", f"文件夹已成功创建！\n路径: {rel_path}")
            self.accept()
        else:
            QMessageBox.critical(self, "创建失败", msg)


class WorkspaceView(QWidget):
    refresh_other_views_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_folder_rel = ""
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # ── Toolbar Panel ─────────────────────────────────────────────────────
        top_panel = QFrame()
        top_panel.setObjectName("CardPanel")
        top_vbox = QVBoxLayout(top_panel)
        top_vbox.setContentsMargins(20, 16, 20, 14)
        top_vbox.setSpacing(12)

        # ── Row 1: Search + Status + Reset ────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Search icon + input wrapper
        search_wrapper = QFrame()
        search_wrapper.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 1.5px solid #334155;
                border-radius: 10px;
            }
        """)
        search_inner = QHBoxLayout(search_wrapper)
        search_inner.setContentsMargins(14, 0, 10, 0)
        search_inner.setSpacing(8)
        lbl_search_icon = QLabel("🔍")
        lbl_search_icon.setStyleSheet("background: transparent; border: none; font-size: 15px;")
        search_inner.addWidget(lbl_search_icon)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索文件名、备注关键词...")
        self.search_input.setFixedHeight(38)
        self.search_input.setStyleSheet("""
            QLineEdit { background: transparent; border: none; font-size: 14px; color: #F8FAFC; }
        """)
        self.search_input.textChanged.connect(self.run_search)
        search_inner.addWidget(self.search_input, 1)
        search_wrapper.setFixedHeight(44)
        row1.addWidget(search_wrapper, 1)

        # Status combo
        status_lbl = QLabel("状态筛选")
        status_lbl.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: 500;")
        row1.addWidget(status_lbl)
        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(42)
        self.status_combo.setMinimumWidth(110)
        self.refresh_status_combo()
        self.status_combo.currentIndexChanged.connect(self.run_search)
        row1.addWidget(self.status_combo)

        # Divider
        sep1 = QFrame(); sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet("color: #2D3748;"); row1.addWidget(sep1)

        # Reset button
        self.reset_search_btn = QPushButton("↺  重置筛选")
        self.reset_search_btn.setFixedHeight(42)
        self.reset_search_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1.5px solid #334155;
                border-radius: 10px;
                padding: 0 18px;
                color: #94A3B8;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                border-color: #6366F1;
                color: #C7D2FE;
                background: rgba(99,102,241,0.08);
            }
        """)
        self.reset_search_btn.clicked.connect(self.reset_filters)
        row1.addWidget(self.reset_search_btn)
        top_vbox.addLayout(row1)

        # ── Divider ────────────────────────────────────────────────────────────
        hdiv1 = QFrame(); hdiv1.setFrameShape(QFrame.HLine)
        hdiv1.setStyleSheet("color: #1E293B;"); top_vbox.addWidget(hdiv1)

        # ── Row 2: Large action buttons (centered) ────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        row2.setContentsMargins(0, 4, 0, 4)
        row2.addStretch()

        self.create_file_btn = QPushButton("📄   新建文件")
        self.create_file_btn.setFixedHeight(48)
        self.create_file_btn.setMinimumWidth(180)
        self.create_file_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #818CF8, stop:0.5 #6366F1, stop:1 #4F46E5);
                border: none;
                border-radius: 12px;
                padding: 0 28px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #A5B4FC, stop:0.5 #818CF8, stop:1 #6366F1);
            }
            QPushButton:pressed {
                background: #4338CA;
            }
        """)
        self.create_file_btn.clicked.connect(self.create_new_file)
        row2.addWidget(self.create_file_btn)

        self.create_folder_btn = QPushButton("📁   新建文件夹")
        self.create_folder_btn.setFixedHeight(48)
        self.create_folder_btn.setMinimumWidth(180)
        self.create_folder_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #38BDF8, stop:0.5 #0EA5E9, stop:1 #0284C7);
                border: none;
                border-radius: 12px;
                padding: 0 28px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7DD3FC, stop:0.5 #38BDF8, stop:1 #0EA5E9);
            }
            QPushButton:pressed {
                background: #0369A1;
            }
        """)
        self.create_folder_btn.clicked.connect(self.create_new_folder)
        row2.addWidget(self.create_folder_btn)

        row2.addStretch()
        top_vbox.addLayout(row2)

        # ── Divider ────────────────────────────────────────────────────────────
        hdiv2 = QFrame(); hdiv2.setFrameShape(QFrame.HLine)
        hdiv2.setStyleSheet("color: #1E293B;"); top_vbox.addWidget(hdiv2)

        # ── Row 3: Tag chips (scrollable) ─────────────────────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(10)
        row3.setContentsMargins(0, 2, 0, 2)

        tag_lbl = QLabel("标签筛选")
        tag_lbl.setStyleSheet(
            "color: #64748B; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;"
        )
        tag_lbl.setFixedWidth(56)
        row3.addWidget(tag_lbl)

        from PySide6.QtWidgets import QScrollArea as _QScrollArea
        self._tag_scroll = _QScrollArea()
        self._tag_scroll.setFrameShape(QFrame.NoFrame)
        self._tag_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._tag_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tag_scroll.setWidgetResizable(True)
        self._tag_scroll.setFixedHeight(36)
        self._tag_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:horizontal {
                height: 3px; background: transparent; margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: #475569; border-radius: 1px; min-width: 24px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """)

        self.tag_buttons_container = QWidget()
        self.tag_buttons_container.setStyleSheet("background: transparent;")
        self.tag_flow = QHBoxLayout(self.tag_buttons_container)
        self.tag_flow.setContentsMargins(2, 0, 2, 0)
        self.tag_flow.setSpacing(6)
        self.tag_flow.addStretch()

        self._tag_scroll.setWidget(self.tag_buttons_container)
        row3.addWidget(self._tag_scroll, 1)

        self.tag_btn_references = {}
        self.selected_filter_tags = set()

        top_vbox.addLayout(row3)



        main_layout.addWidget(top_panel)

        # 2. Main Content Split View (Left Tree, Right Table)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(15)

        # Left: Directory Tree
        tree_container = QFrame()
        tree_container.setObjectName("CardPanel")
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(10, 10, 10, 10)
        
        tree_title = QLabel("物理文件夹结构 (≤4层限制)")
        tree_title.setObjectName("CardTitle")
        tree_layout.addWidget(tree_title)

        # QFileSystemModel to navigate directories
        self.dir_model = QFileSystemModel()
        self.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot) if False else None # Done in setup
        
        self.dir_tree = QTreeView()
        self.dir_tree.setHeaderHidden(True)
        self.dir_tree.clicked.connect(self.on_tree_directory_clicked)
        tree_layout.addWidget(self.dir_tree)
        
        split_layout.addWidget(tree_container, 1)

        # Right: Files Grid
        grid_container = QFrame()
        grid_container.setObjectName("CardPanel")
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(10, 10, 10, 10)

        self.grid_title = QLabel("📂 全部文件列表")
        self.grid_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #6366F1; padding-bottom: 2px;")
        grid_layout.addWidget(self.grid_title)

        self.files_table = WorkspaceTableWidget()
        self.files_table.setColumnCount(5)
        self.files_table.setHorizontalHeaderLabels(["名称", "分类位置", "大小", "标签", "备份 (盘/云)"])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.files_table.left_double_clicked.connect(self.on_table_left_double_clicked)
        self.files_table.right_double_clicked.connect(self.on_table_right_double_clicked)
        grid_layout.addWidget(self.files_table)

        split_layout.addWidget(grid_container, 2)
        main_layout.addLayout(split_layout)

        # Populate
        self.setup_models()
        self.refresh_tags_cloud()
        self.run_search()

    def setup_models(self):
        ws_path = config.workspace_dir
        
        # File explorer tree setup
        from PySide6.QtCore import QDir
        self.dir_model.setRootPath(ws_path)
        self.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.AllEntries)
        
        # Filter tree columns to show name only
        self.dir_tree.setModel(self.dir_model)
        self.dir_tree.setRootIndex(self.dir_model.index(ws_path))
        
        # Hide Size, Type, Date columns from treeview
        for i in range(1, 4):
            self.dir_tree.hideColumn(i)

    def refresh_tags_cloud(self):
        # Remove all widgets and spacers from tag_flow completely
        while self.tag_flow.count():
            item = self.tag_flow.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self.tag_btn_references.clear()
        self.selected_filter_tags = set()

        # Fetch all tags from config (no limit — scroll area handles overflow)
        all_tags = config.tags["primary"] + config.tags["secondary"]
        for tag in all_tags:
            btn = QPushButton(display_tag(tag))
            btn.setCheckable(True)
            btn.setFixedHeight(26)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 2px 10px;
                    font-size: 11px;
                    border-radius: 13px;
                    border: 1px solid #334155;
                }
                QPushButton:checked {
                    background-color: #6366F1;
                    color: white;
                    border: 1px solid #6366F1;
                }
            """)
            btn.toggled.connect(lambda checked, t=tag: self.toggle_filter_tag(t, checked))
            self.tag_flow.addWidget(btn)
            self.tag_btn_references[tag] = btn
        # Trailing stretch keeps buttons left-aligned
        self.tag_flow.addStretch()


    def toggle_filter_tag(self, tag, checked):
        if checked:
            self.selected_filter_tags.add(tag)
        else:
            self.selected_filter_tags.discard(tag)
        self.run_search()

    def reset_filters(self):
        self.search_input.clear()
        self.status_combo.setCurrentIndex(0)
        self.selected_filter_tags.clear()
        for btn in self.tag_btn_references.values():
            btn.setChecked(False)
        
        # Reset folder selection
        self.current_folder_rel = ""
        self.grid_title.setText("📂 全部文件列表")
        self.dir_tree.clearSelection()
        
        self.run_search()

    def create_new_file(self):
        dialog = CreateFileDialog(self.current_folder_rel, self)
        if dialog.exec() == QDialog.Accepted:
            self.run_search()
            self.refresh_other_views_signal.emit()

    def create_new_folder(self):
        dialog = CreateFolderDialog(self.current_folder_rel, self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh the file-system tree so the new folder appears immediately
            self.setup_models()
            self.run_search()

    def on_tree_directory_clicked(self, index: QModelIndex):
        dir_path = self.dir_model.filePath(index)
        ws_root = Path(config.workspace_dir)
        
        if os.path.isdir(dir_path):
            try:
                rel = Path(dir_path).relative_to(ws_root)
                self.current_folder_rel = str(rel).replace("\\", "/")
                self.grid_title.setText(f"📂 目录 {self.current_folder_rel} 中的文件列表")
            except ValueError:
                self.current_folder_rel = ""
                self.grid_title.setText("📂 全部文件列表")
        else:
            # Clicked a file
            self.current_folder_rel = ""
            self.grid_title.setText("📂 全部文件列表")
            
        self.run_search()

    def run_search(self):
        query = self.search_input.text().strip()
        
        idx = self.status_combo.currentIndex()
        status_tag = self.status_combo.itemData(idx) if idx > 0 else None
        
        # Compound search via SQL
        results = db.search_files(
            query=query, 
            selected_tags=list(self.selected_filter_tags), 
            file_status=status_tag
        )

        # If current_folder_rel is set, filter SQL results to match current directory
        if self.current_folder_rel:
            filtered_results = []
            for r in results:
                # File is directly inside current_folder_rel, or in subfolders
                if r["filepath"].startswith(self.current_folder_rel + "/"):
                    filtered_results.append(r)
            results = filtered_results

        self.populate_table(results)

    def populate_table(self, file_records):
        self.files_table.setRowCount(0)
        
        for i, r in enumerate(file_records):
            self.files_table.insertRow(i)
            
            # File size readable
            sz = r["file_size"]
            sz_str = f"{sz / 1024:.1f} KB" if sz < 1024*1024 else f"{sz / (1024*1024):.1f} MB"
            
            # Backup icons
            disk_ok = "✅" if r["backup_disk_status"] else "❌"
            cloud_ok = "✅" if r["backup_cloud_status"] else "❌"
            backup_str = f"盘 {disk_ok} | 云 {cloud_ok}"
            tags_display = "--"
            if r["tags"]:
                tags_display = ", ".join(
                    display_tag(tag) for tag in r["tags"].split(",") if tag.strip()
                )
            
            item_name = QTableWidgetItem(r["filename"])
            item_path = QTableWidgetItem(r["filepath"])
            item_size = QTableWidgetItem(sz_str)
            item_tags = QTableWidgetItem(tags_display)
            item_backup = QTableWidgetItem(backup_str)
            
            # Store full record path inside name item for double click
            item_name.setData(Qt.UserRole, r["filepath"])
            
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            item_path.setFlags(item_path.flags() & ~Qt.ItemIsEditable)
            item_size.setFlags(item_size.flags() & ~Qt.ItemIsEditable)
            item_tags.setFlags(item_tags.flags() & ~Qt.ItemIsEditable)
            item_backup.setFlags(item_backup.flags() & ~Qt.ItemIsEditable)

            self.files_table.setItem(i, 0, item_name)
            self.files_table.setItem(i, 1, item_path)
            self.files_table.setItem(i, 2, item_size)
            self.files_table.setItem(i, 3, item_tags)
            self.files_table.setItem(i, 4, item_backup)

    def on_table_left_double_clicked(self, index):
        row = index.row()
        rel_path = self.files_table.item(row, 0).data(Qt.UserRole)
        
        if rel_path:
            ws_root = Path(config.workspace_dir)
            abs_path = ws_root / rel_path
            if abs_path.exists():
                try:
                    os.startfile(str(abs_path))
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"无法打开文件:\n{str(e)}")
            else:
                QMessageBox.warning(self, "警告", "文件在磁盘上不存在！")

    def on_table_right_double_clicked(self, index):
        row = index.row()
        rel_path = self.files_table.item(row, 0).data(Qt.UserRole)
        
        if rel_path:
            dialog = FileDetailsDialog(rel_path, self)
            if dialog.exec() == QDialog.Accepted:
                self.run_search()
                self.refresh_other_views_signal.emit()

    def refresh_status_combo(self):
        self.status_combo.blockSignals(True)
        self.status_combo.clear()
        self.status_combo.addItem("全部")
        for tag in config.tags["status"]:
            self.status_combo.addItem(display_tag(tag), tag)
        self.status_combo.blockSignals(False)

# Interactive Metadata/Tags Editor Dialog
class FileDetailsDialog(QDialog):
    def __init__(self, rel_path, parent=None):
        super().__init__(parent)
        self.rel_path = rel_path
        self.info = db.get_file_info(rel_path)
        self.init_ui()

    def init_ui(self):
        if not self.info:
            self.reject()
            return

        self.setWindowTitle(f"编辑文件属性 - {self.info['filename']}")
        self.setMinimumWidth(450)
        self.setStyleSheet(self.parent().parent().styleSheet()) # Inherit theme stylesheet

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # File metadata card
        meta_layout = QGridLayout()
        meta_layout.addWidget(QLabel("<b>文件名:</b>"), 0, 0)
        self.input_filename = QLineEdit(self.info["filename"])
        meta_layout.addWidget(self.input_filename, 0, 1)

        meta_layout.addWidget(QLabel("<b>物理路径:</b>"), 1, 0)
        meta_layout.addWidget(QLabel(self.info["filepath"]), 1, 1)

        sz = self.info["file_size"]
        sz_str = f"{sz / 1024:.1f} KB" if sz < 1024*1024 else f"{sz / (1024*1024):.1f} MB"
        meta_layout.addWidget(QLabel("<b>容量大小:</b>"), 2, 0)
        meta_layout.addWidget(QLabel(sz_str), 2, 1)

        mtime = datetime.datetime.fromtimestamp(self.info["modified_time"]).strftime("%Y-%m-%d %H:%M:%S")
        meta_layout.addWidget(QLabel("<b>修改时间:</b>"), 3, 0)
        meta_layout.addWidget(QLabel(mtime), 3, 1)
        
        layout.addLayout(meta_layout)

        # Tags checklist
        layout.addWidget(QLabel("<b>修改标签:</b>"))
        tags_scroll = QFrame()
        tags_scroll_layout = QGridLayout(tags_scroll)
        tags_scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        self.checkboxes = []
        all_tags = config.tags["primary"] + config.tags["secondary"] + config.tags["status"]
        current_tags = [t.strip() for t in self.info["tags"].split(",") if t.strip()]
        
        for idx, tag in enumerate(all_tags):
            cb = QCheckBox(display_tag(tag))
            cb.setProperty("tag_value", normalize_tag(tag))
            if tag in current_tags:
                cb.setChecked(True)
            self.checkboxes.append(cb)
            tags_scroll_layout.addWidget(cb, idx // 3, idx % 3)
            
        layout.addWidget(tags_scroll)

        # Description Notes
        layout.addWidget(QLabel("<b>文件备注 / Obsidian 大纲:</b>"))
        self.input_desc = QTextEdit()
        self.input_desc.setFixedHeight(80)
        self.input_desc.setText(self.info["description"])
        layout.addWidget(self.input_desc)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存修改")
        btn_save.setObjectName("PrimaryBtn")
        btn_save.clicked.connect(self.save_metadata)
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        # Danger delete btn
        btn_delete = QPushButton("物理删除")
        btn_delete.setObjectName("DangerBtn")
        btn_delete.clicked.connect(self.delete_file)
        btn_layout.addWidget(btn_delete)

        layout.addLayout(btn_layout)

    def save_metadata(self):
        new_name = self.input_filename.text().strip()
        if not new_name:
            QMessageBox.warning(self, "警告", "文件名不能为空！")
            return
            
        # Check banned keywords
        if FileManager.is_banned_name(new_name):
            QMessageBox.warning(self, "规范拦截", "文件名包含禁用词，请修改！")
            return

        # Check tags
        selected_tags = [cb.property("tag_value") or normalize_tag(cb.text()) for cb in self.checkboxes if cb.isChecked()]
        new_desc = self.input_desc.toPlainText().strip()

        # If name changed, rename physically
        if new_name != self.info["filename"]:
            ws_root = Path(config.workspace_dir)
            src_abs = ws_root / self.info["filepath"]
            dest_abs = src_abs.parent / new_name
            
            try:
                # Physically rename
                shutil.move(str(src_abs), str(dest_abs))
                # Update SQLite record
                new_rel = str(dest_abs.relative_to(ws_root)).replace("\\", "/")
                db.rename_file_record(self.info["filepath"], new_rel, new_name)
                self.rel_path = new_rel
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")
                return

        # Save metadata
        db.update_file_tags(self.rel_path, selected_tags)
        db.update_file_description(self.rel_path, new_desc)
        
        QMessageBox.information(self, "成功", "文件属性保存成功！")
        self.accept()

    def delete_file(self):
        reply = QMessageBox.question(self, "警告 - 物理删除", 
                                     "此操作将永久从磁盘删除该文件！\n确认要删除吗？", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            ws_root = Path(config.workspace_dir)
            abs_path = ws_root / self.rel_path
            try:
                if abs_path.exists():
                    os.remove(abs_path)
                db.delete_file_record(self.rel_path)
                QMessageBox.information(self, "成功", "文件已成功从磁盘和数据库中删除！")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除文件失败: {str(e)}")

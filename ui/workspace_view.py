import os
import datetime
import shutil
import tempfile
from pathlib import Path
from urllib.parse import quote
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeView, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLabel, QLineEdit, QPushButton, QFrame, 
                             QFileSystemModel, QDialog, QCheckBox, QTextEdit, 
                             QMessageBox, QComboBox, QGridLayout, QInputDialog,
                             QListWidget, QListWidgetItem, QSplitter, QAbstractItemView,
                             QTabWidget, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, QModelIndex, Signal, QDir, QUrl, QSize
from PySide6.QtGui import QDesktopServices, QPixmap, QIcon, QColor, QPainter, QFont
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from config import config, display_tag, normalize_tag
from db import db
from file_manager import FileManager
from ui.icon_utils import format_bytes, line_icon, make_empty_item

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
        title_lbl = QLabel("新建工作空间文档")
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
        self.btn_confirm.setIcon(line_icon("file", "#FFFFFF", 16))
        self.btn_confirm.setIconSize(QSize(16, 16))
        self.btn_confirm.clicked.connect(self.create_file)
        btn_layout.addWidget(self.btn_confirm)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setIcon(line_icon("delete", size=16))
        self.btn_cancel.setIconSize(QSize(16, 16))
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
            QMessageBox.information(self, "创建成功", f"文件已成功在工作空间创建并同步入库！\n路径: {dest_rel_path}")
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
        title_lbl = QLabel("在工作空间中新建文件夹")
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
        self.hint_lbl = QLabel("最终路径预览: —")
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

        self.btn_confirm = QPushButton("确认创建")
        self.btn_confirm.setObjectName("PrimaryBtn")
        self.btn_confirm.setIcon(line_icon("folder", "#FFFFFF", 16))
        self.btn_confirm.setIconSize(QSize(16, 16))
        self.btn_confirm.clicked.connect(self.do_create_folder)
        btn_layout.addWidget(self.btn_confirm)

        btn_cancel = QPushButton("取消")
        btn_cancel.setIcon(line_icon("delete", size=16))
        btn_cancel.setIconSize(QSize(16, 16))
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
            self.hint_lbl.setText("最终路径预览: —")
            return
        depth = len([p for p in rel.split("/") if p])
        color = "#F97316" if depth > 4 else "#34D399"
        self.hint_lbl.setText(
            f"最终路径: <b style='color:{color};'>{rel}</b>  "
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
            QMessageBox.information(self, "创建成功", f"文件夹已成功创建！\n路径: {rel_path}")
            self.accept()
        else:
            QMessageBox.critical(self, "创建失败", msg)


class WorkspaceView(QWidget):
    refresh_other_views_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_folder_rel = ""
        self.current_preview_rel_path = ""
        self.preview_pdf_temp_path = None
        self.file_icon_cache = {}
        self.duplicate_groups = {}
        self.init_ui()

    def get_file_type_icon(self, filename):
        suffix = Path(str(filename)).suffix.lower()
        label, color = {
            ".pdf": ("PDF", "#DC2626"),
            ".doc": ("DOC", "#2563EB"),
            ".docx": ("DOC", "#2563EB"),
            ".txt": ("TXT", "#64748B"),
            ".md": ("MD", "#7C3AED"),
            ".png": ("IMG", "#059669"),
            ".jpg": ("IMG", "#059669"),
            ".jpeg": ("IMG", "#059669"),
            ".gif": ("IMG", "#059669"),
            ".py": ("PY", "#D97706"),
            ".js": ("JS", "#CA8A04"),
            ".ts": ("TS", "#0284C7"),
            ".xlsx": ("XLS", "#16A34A"),
            ".xls": ("XLS", "#16A34A"),
            ".ppt": ("PPT", "#EA580C"),
            ".pptx": ("PPT", "#EA580C"),
            ".csv": ("CSV", "#0F766E"),
            ".json": ("JSON", "#4A6FA6"),
        }.get(suffix, ("FILE", "#4A6FA6"))

        cache_key = (label, color)
        if cache_key in self.file_icon_cache:
            return self.file_icon_cache[cache_key]

        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(3, 3, 26, 26, 6, 6)
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", 6 if len(label) > 3 else 7)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, label)
        painter.end()

        icon = QIcon(pixmap)
        self.file_icon_cache[cache_key] = icon
        return icon

    def describe_file_type(self, filename):
        suffix = Path(str(filename)).suffix.lower()
        return {
            ".pdf": "PDF 文档",
            ".doc": "Word 文档",
            ".docx": "Word 文档",
            ".txt": "文本文件",
            ".md": "Markdown",
            ".png": "图片",
            ".jpg": "图片",
            ".jpeg": "图片",
            ".gif": "图片",
            ".py": "Python 代码",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".xlsx": "Excel 表格",
            ".xls": "Excel 表格",
            ".ppt": "演示文稿",
            ".pptx": "演示文稿",
            ".csv": "CSV 数据",
            ".json": "JSON 数据",
        }.get(suffix, suffix.upper().lstrip(".") or "普通文件")

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # ── Compact Toolbar Panel ─────────────────────────────────────────────
        top_panel = QFrame()
        top_panel.setObjectName("ToolbarPanel")
        top_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        top_panel.setMaximumHeight(112)
        top_vbox = QVBoxLayout(top_panel)
        top_vbox.setContentsMargins(12, 8, 12, 8)
        top_vbox.setSpacing(6)

        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(8)

        search_wrapper = QFrame()
        search_wrapper.setObjectName("SearchBox")
        search_inner = QHBoxLayout(search_wrapper)
        search_inner.setContentsMargins(12, 0, 8, 0)
        search_inner.setSpacing(6)
        lbl_search_icon = QLabel()
        lbl_search_icon.setPixmap(line_icon("search", size=16).pixmap(16, 16))
        lbl_search_icon.setStyleSheet("background: transparent; border: none;")
        search_inner.addWidget(lbl_search_icon)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("ToolbarSearchInput")
        self.search_input.setPlaceholderText("搜索文件名、备注关键词...")
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self.run_search)
        search_inner.addWidget(self.search_input, 1)
        search_wrapper.setFixedHeight(36)
        toolbar_row.addWidget(search_wrapper, 1)

        status_lbl = QLabel("状态筛选")
        status_lbl.setObjectName("ToolbarLabel")
        self.toolbar_status_label = status_lbl
        toolbar_row.addWidget(self.toolbar_status_label)
        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(30)
        self.status_combo.setMinimumWidth(110)
        self.refresh_status_combo()
        self.status_combo.currentIndexChanged.connect(self.run_search)
        toolbar_row.addWidget(self.status_combo)

        self.reset_search_btn = QPushButton("重置")
        self.reset_search_btn.setObjectName("ToolbarBtn")
        self.reset_search_btn.setIcon(line_icon("refresh", size=16))
        self.reset_search_btn.setIconSize(QSize(16, 16))
        self.reset_search_btn.setFixedHeight(30)
        self.reset_search_btn.clicked.connect(self.reset_filters)
        toolbar_row.addWidget(self.reset_search_btn)

        self.create_file_btn = QPushButton("新建文件")
        self.create_file_btn.setObjectName("ToolbarPrimaryBtn")
        self.create_file_btn.setIcon(line_icon("file", "#FFFFFF", 16))
        self.create_file_btn.setIconSize(QSize(16, 16))
        self.create_file_btn.setFixedHeight(30)
        self.create_file_btn.clicked.connect(self.create_new_file)
        toolbar_row.addWidget(self.create_file_btn)

        self.create_folder_btn = QPushButton("新建文件夹")
        self.create_folder_btn.setObjectName("ToolbarBtn")
        self.create_folder_btn.setIcon(line_icon("folder", size=16))
        self.create_folder_btn.setIconSize(QSize(16, 16))
        self.create_folder_btn.setFixedHeight(30)
        self.create_folder_btn.clicked.connect(self.create_new_folder)
        toolbar_row.addWidget(self.create_folder_btn)
        top_vbox.addLayout(toolbar_row)

        tag_row = QHBoxLayout()
        tag_row.setSpacing(6)
        tag_row.setContentsMargins(0, 0, 0, 0)

        tag_lbl = QLabel("标签筛选")
        tag_lbl.setObjectName("ToolbarLabel")
        tag_lbl.setFixedWidth(56)
        self.toolbar_tag_label = tag_lbl
        tag_row.addWidget(self.toolbar_tag_label)

        self._tag_scroll = QScrollArea()
        self._tag_scroll.setFrameShape(QFrame.NoFrame)
        self._tag_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._tag_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tag_scroll.setWidgetResizable(True)
        self._tag_scroll.setFixedHeight(28)

        self.tag_buttons_container = QWidget()
        self.tag_buttons_container.setStyleSheet("background: transparent;")
        self.tag_flow = QHBoxLayout(self.tag_buttons_container)
        self.tag_flow.setContentsMargins(2, 0, 2, 0)
        self.tag_flow.setSpacing(6)
        self.tag_flow.addStretch()

        self._tag_scroll.setWidget(self.tag_buttons_container)
        tag_row.addWidget(self._tag_scroll, 1)

        self.tag_btn_references = {}
        self.selected_filter_tags = set()

        top_vbox.addLayout(tag_row)



        main_layout.addWidget(top_panel)

        # 2. Main Content Split View (Left Tree, Center Table, Right Preview)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(8)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(4)

        # Left: Directory Tree
        tree_container = QFrame()
        tree_container.setObjectName("CardPanel")
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(10, 8, 10, 8)
        
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
        
        self.main_splitter.addWidget(tree_container)

        # Center: Files Grid + Batch tools
        grid_container = QFrame()
        grid_container.setObjectName("CardPanel")
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(10, 8, 10, 8)

        self.grid_title = QLabel("全部文件列表")
        self.grid_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #6366F1; padding-bottom: 2px;")
        grid_layout.addWidget(self.grid_title)

        self.files_table = WorkspaceTableWidget()
        self.files_table.setColumnCount(5)
        self.files_table.setHorizontalHeaderLabels(["名称", "分类位置", "大小", "标签", "备份 (盘/云)"])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.files_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.files_table.setMinimumHeight(260)
        self.files_table.setAlternatingRowColors(True)
        self.files_table.setShowGrid(False)
        self.files_table.setIconSize(QSize(24, 24))
        self.files_table.verticalHeader().setVisible(False)
        self.files_table.verticalHeader().setDefaultSectionSize(36)
        self.files_table.horizontalHeader().setHighlightSections(False)
        self.files_table.left_double_clicked.connect(self.on_table_left_double_clicked)
        self.files_table.right_double_clicked.connect(self.on_table_right_double_clicked)
        self.files_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        grid_layout.addWidget(self.files_table)

        self.file_empty_label = QLabel("暂无文件。可以调整筛选条件，或从收集箱导入后再查看。")
        self.file_empty_label.setObjectName("EmptyState")
        self.file_empty_label.setAlignment(Qt.AlignCenter)
        self.file_empty_label.setWordWrap(True)
        self.file_empty_label.hide()
        grid_layout.addWidget(self.file_empty_label)

        self.batch_panel = QFrame()
        self.batch_panel.setObjectName("BatchToolbar")
        self.batch_panel.setProperty("active", False)
        batch_layout = QHBoxLayout(self.batch_panel)
        batch_layout.setContentsMargins(10, 8, 10, 8)
        batch_layout.setSpacing(8)

        self.selection_status_label = QLabel("当前未选择文件")
        self.selection_status_label.setObjectName("BatchStatus")
        self.selection_status_label.setWordWrap(True)
        self.selection_status_label.setMinimumWidth(150)
        batch_layout.addWidget(self.selection_status_label, 1)

        self.batch_tag_label = QLabel("标签")
        batch_layout.addWidget(self.batch_tag_label)
        self.batch_tags_input = QLineEdit()
        self.batch_tags_input.setFixedWidth(180)
        self.batch_tags_input.setPlaceholderText("如：论文, 课程学习")
        batch_layout.addWidget(self.batch_tags_input)
        self.batch_apply_tags_btn = QPushButton("追加标签")
        self.batch_apply_tags_btn.setObjectName("ToolbarBtn")
        self.batch_apply_tags_btn.setIcon(line_icon("tag", size=16))
        self.batch_apply_tags_btn.setIconSize(QSize(16, 16))
        self.batch_apply_tags_btn.clicked.connect(self.apply_batch_tags)
        batch_layout.addWidget(self.batch_apply_tags_btn)

        self.batch_move_label = QLabel("移动到")
        batch_layout.addWidget(self.batch_move_label)
        self.batch_target_dir = QComboBox()
        self.batch_target_dir.setFixedWidth(150)
        for d in config.get_standard_dirs():
            if d != config.get_inbox_name():
                self.batch_target_dir.addItem(d)
        batch_layout.addWidget(self.batch_target_dir)
        self.batch_move_btn = QPushButton("批量移动")
        self.batch_move_btn.setObjectName("ToolbarBtn")
        self.batch_move_btn.setIcon(line_icon("move", size=16))
        self.batch_move_btn.setIconSize(QSize(16, 16))
        self.batch_move_btn.clicked.connect(self.apply_batch_move)
        batch_layout.addWidget(self.batch_move_btn)

        self.batch_duplicate_label = QLabel("重复")
        batch_layout.addWidget(self.batch_duplicate_label)
        self.duplicate_mode_combo = QComboBox()
        self.duplicate_mode_combo.setFixedWidth(90)
        self.duplicate_mode_combo.addItems(["文件名", "大小", "哈希"])
        batch_layout.addWidget(self.duplicate_mode_combo)
        self.duplicate_check_btn = QPushButton("扫描重复")
        self.duplicate_check_btn.setObjectName("ToolbarBtn")
        self.duplicate_check_btn.setIcon(line_icon("scan", size=16))
        self.duplicate_check_btn.setIconSize(QSize(16, 16))
        self.duplicate_check_btn.clicked.connect(self.show_duplicates)
        batch_layout.addWidget(self.duplicate_check_btn)

        self.rule_hint_label = QLabel("自动归类未启用")
        self.rule_hint_label.setObjectName("BatchHint")
        self.rule_hint_label.setWordWrap(True)
        batch_layout.addWidget(self.rule_hint_label, 1)
        self.rule_apply_btn = QPushButton("按建议归类")
        self.rule_apply_btn.setObjectName("ToolbarBtn")
        self.rule_apply_btn.setIcon(line_icon("success", size=16))
        self.rule_apply_btn.setIconSize(QSize(16, 16))
        self.rule_apply_btn.clicked.connect(self.apply_rule_suggestion)
        batch_layout.addWidget(self.rule_apply_btn)

        self.batch_control_widgets = [
            self.batch_tags_input,
            self.batch_apply_tags_btn,
            self.batch_target_dir,
            self.batch_move_btn,
            self.rule_apply_btn,
        ]
        grid_layout.addWidget(self.batch_panel)
        self.main_splitter.addWidget(grid_container)

        # Right: Preview Panel
        preview_container = QFrame()
        preview_container.setObjectName("CardPanel")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(10, 8, 10, 8)

        self.preview_title = QLabel("预览面板")
        self.preview_title.setObjectName("CardTitle")
        preview_layout.addWidget(self.preview_title)

        self.preview_info_card = QFrame()
        self.preview_info_card.setObjectName("PreviewInfoCard")
        preview_info_layout = QVBoxLayout(self.preview_info_card)
        preview_info_layout.setContentsMargins(10, 8, 10, 8)
        preview_info_layout.setSpacing(6)

        preview_header = QHBoxLayout()
        preview_header.setContentsMargins(0, 0, 0, 0)
        preview_header.setSpacing(8)
        self.preview_file_icon = QLabel()
        self.preview_file_icon.setFixedSize(36, 36)
        self.preview_file_icon.setPixmap(self.get_file_type_icon("").pixmap(32, 32))
        preview_header.addWidget(self.preview_file_icon)

        preview_name_box = QVBoxLayout()
        preview_name_box.setContentsMargins(0, 0, 0, 0)
        preview_name_box.setSpacing(2)
        self.preview_name_label = QLabel("未选择文件")
        self.preview_name_label.setObjectName("PreviewFileName")
        self.preview_name_label.setWordWrap(True)
        self.preview_file_label = QLabel("请选择文件")
        self.preview_file_label.setObjectName("PreviewFilePath")
        self.preview_file_label.setWordWrap(True)
        preview_name_box.addWidget(self.preview_name_label)
        preview_name_box.addWidget(self.preview_file_label)
        preview_header.addLayout(preview_name_box, 1)
        preview_info_layout.addLayout(preview_header)

        preview_meta_layout = QHBoxLayout()
        preview_meta_layout.setContentsMargins(0, 0, 0, 0)
        preview_meta_layout.setSpacing(6)
        self.preview_info_type = QLabel("类型: --")
        self.preview_info_size = QLabel("大小: --")
        for lbl in [self.preview_info_type, self.preview_info_size]:
            lbl.setObjectName("PreviewMetaChip")
            preview_meta_layout.addWidget(lbl)
        preview_meta_layout.addStretch()
        preview_info_layout.addLayout(preview_meta_layout)

        self.preview_info_path = QLabel("路径: --")
        self.preview_info_path.setObjectName("PreviewInfoPath")
        for lbl in [self.preview_info_path]:
            lbl.setWordWrap(True)
            preview_info_layout.addWidget(lbl)
        preview_layout.addWidget(self.preview_info_card)

        self.preview_tabs = QTabWidget()
        preview_layout.addWidget(self.preview_tabs, 1)

        self.preview_stack = QFrame()
        preview_stack_layout = QVBoxLayout(self.preview_stack)
        preview_stack_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlainText("未选择文件。\n从中间文件列表选择一个文件后，这里会显示内容预览。")
        preview_stack_layout.addWidget(self.preview_text)

        self.preview_image = QLabel("图片预览")
        self.preview_image.setAlignment(Qt.AlignCenter)
        self.preview_image.setMinimumHeight(260)
        self.preview_image.hide()
        preview_stack_layout.addWidget(self.preview_image)

        self.preview_pdf_doc = QPdfDocument(self)
        self.preview_pdf = QPdfView()
        self.preview_pdf.setDocument(self.preview_pdf_doc)
        self.preview_pdf.setMinimumHeight(260)
        self.preview_pdf.hide()
        preview_stack_layout.addWidget(self.preview_pdf)
        self.preview_tabs.addTab(self.preview_stack, "文件预览")

        self.duplicates_list = QListWidget()
        self.duplicates_list.setObjectName("DuplicateList")
        self.duplicates_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.duplicates_list.setSpacing(6)
        self.duplicates_list.setUniformItemSizes(False)
        self.duplicates_list.itemDoubleClicked.connect(self.on_duplicate_item_double_clicked)
        self.preview_tabs.addTab(self.duplicates_list, "重复检测")

        self.duplicate_tools = QFrame()
        duplicate_tools_layout = QHBoxLayout(self.duplicate_tools)
        duplicate_tools_layout.setContentsMargins(0, 0, 0, 0)
        duplicate_tools_layout.setSpacing(8)
        self.duplicate_hint_label = QLabel("选择重复文件后删除；建议每组至少保留 1 个。")
        self.duplicate_hint_label.setObjectName("MutedText")
        duplicate_tools_layout.addWidget(self.duplicate_hint_label, 1)

        self.keep_one_btn = QPushButton("删除选中的重复文件")
        self.keep_one_btn.setObjectName("DangerBtn")
        self.keep_one_btn.setIcon(line_icon("delete", "#FFFFFF", 16))
        self.keep_one_btn.setIconSize(QSize(16, 16))
        self.keep_one_btn.clicked.connect(self.delete_selected_duplicate_files)
        duplicate_tools_layout.addWidget(self.keep_one_btn)
        preview_layout.addWidget(self.duplicate_tools)

        self.preview_open_btn = QPushButton("在系统中打开")
        self.preview_open_btn.setIcon(line_icon("open", size=16))
        self.preview_open_btn.setIconSize(QSize(16, 16))
        self.preview_open_btn.clicked.connect(self.open_current_preview_file)
        preview_layout.addWidget(self.preview_open_btn)

        self.main_splitter.addWidget(preview_container)
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setStretchFactor(2, 4)
        self.main_splitter.setChildrenCollapsible(False)

        split_layout.addWidget(self.main_splitter)
        main_layout.addLayout(split_layout)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

        # Populate
        self.configure_responsive_toolbar()
        self.setup_models()
        self.refresh_tags_cloud()
        self.update_batch_toolbar_state(0)
        self.run_search()

    def configure_responsive_toolbar(self):
        self.responsive_buttons = [
            self.reset_search_btn,
            self.create_file_btn,
            self.create_folder_btn,
            self.batch_apply_tags_btn,
            self.batch_move_btn,
            self.duplicate_check_btn,
            self.rule_apply_btn,
            self.keep_one_btn,
            self.preview_open_btn,
        ]
        for btn in self.responsive_buttons:
            btn.setProperty("expanded_text", btn.text())
            btn.setToolTip(btn.text())
        self.responsive_labels = [
            self.toolbar_status_label,
            self.toolbar_tag_label,
            self.batch_tag_label,
            self.batch_move_label,
            self.batch_duplicate_label,
        ]
        self.toolbar_compact = None
        self.apply_toolbar_responsive()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_toolbar_responsive()

    def apply_toolbar_responsive(self):
        if not hasattr(self, "responsive_buttons"):
            return
        compact = self.width() < 980
        self.toolbar_compact = compact
        for btn in self.responsive_buttons:
            text = btn.property("expanded_text") or btn.toolTip() or btn.text()
            btn.setText("" if compact else text)
            btn.setToolTip(text)
            btn.setProperty("compact", compact)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        for label in self.responsive_labels:
            label.setVisible(not compact)
        self.status_combo.setMinimumWidth(88 if compact else 110)
        self.status_combo.setMaximumWidth(96 if compact else 16777215)
        self.batch_tags_input.setFixedWidth(120 if compact else 180)
        self.batch_target_dir.setFixedWidth(116 if compact else 150)

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
        self.grid_title.setText("全部文件列表")
        self.dir_tree.clearSelection()
        
        self.run_search()

    def get_selected_rel_paths(self):
        rows = sorted({index.row() for index in self.files_table.selectionModel().selectedRows()})
        rel_paths = []
        for row in rows:
            item = self.files_table.item(row, 0)
            if item:
                rel = item.data(Qt.UserRole)
                if rel:
                    rel_paths.append(rel)
        return rel_paths

    def set_operation_status(self, message):
        self.selection_status_label.setText(message)

    def update_batch_toolbar_state(self, selected_count):
        active = selected_count > 0
        self.batch_panel.setProperty("active", active)
        self.batch_panel.style().unpolish(self.batch_panel)
        self.batch_panel.style().polish(self.batch_panel)

        status = f"已选择 {selected_count} 个文件" if active else "未选择文件，批量工具保持待命"
        self.selection_status_label.setText(status)
        for widget in self.batch_control_widgets:
            widget.setEnabled(active)

    def on_table_selection_changed(self):
        selected = self.get_selected_rel_paths()
        if not selected:
            self.clear_preview_resources()
            self.preview_file_icon.setPixmap(self.get_file_type_icon("").pixmap(32, 32))
            self.preview_name_label.setText("未选择文件")
            self.preview_file_label.setText("请选择文件")
            self.preview_info_type.setText("类型: --")
            self.preview_info_size.setText("大小: --")
            self.preview_info_path.setText("路径: --")
            self.preview_text.show()
            self.preview_image.hide()
            self.preview_pdf.hide()
            self.preview_text.setPlainText("未选择文件。\n从中间文件列表选择一个文件后，这里会显示内容预览。")
            self.update_batch_toolbar_state(0)
            self.current_preview_rel_path = ""
            return

        first_rel = selected[0]
        self.current_preview_rel_path = first_rel
        self.load_preview(first_rel)
        self.update_batch_toolbar_state(len(selected))
        self.refresh_rule_hint(first_rel)

    def load_preview(self, rel_path):
        ws_root = Path(config.workspace_dir)
        abs_path = ws_root / rel_path
        self.preview_file_icon.setPixmap(self.get_file_type_icon(abs_path.name).pixmap(32, 32))
        self.preview_name_label.setText(abs_path.name)
        self.preview_file_label.setText(rel_path)
        self.preview_info_type.setText(f"类型: {self.describe_file_type(abs_path.name)}")
        try:
            size = abs_path.stat().st_size
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
        except Exception:
            size_str = "--"
        self.preview_info_size.setText(f"大小: {size_str}")
        self.preview_info_path.setText(f"路径: {rel_path}")
        self.clear_preview_resources(keep_label=True)
        self.preview_text.show()
        self.preview_image.hide()
        self.preview_pdf.hide()
        self.preview_text.clear()

        if not abs_path.exists():
            self.preview_text.setPlainText("文件不存在。")
            return

        ext = abs_path.suffix.lower()
        if ext in [".md", ".txt", ".py", ".json", ".csv"]:
            try:
                self.preview_text.setPlainText(abs_path.read_text(encoding="utf-8")[:4000])
            except UnicodeDecodeError:
                self.preview_text.setPlainText(abs_path.read_text(encoding="gbk", errors="ignore")[:4000])
        elif ext in [".png", ".jpg", ".jpeg"]:
            pixmap = QPixmap(str(abs_path))
            if not pixmap.isNull():
                self.preview_text.hide()
                self.preview_image.setPixmap(pixmap.scaled(420, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.preview_image.show()
            else:
                self.preview_text.setPlainText("无法加载图片预览。")
        elif ext == ".pdf":
            try:
                old_doc = self.preview_pdf.document()
                if old_doc is not None:
                    self.preview_pdf.setDocument(None)
                    old_doc.deleteLater()
                fd, temp_path = tempfile.mkstemp(suffix=".pdf")
                os.close(fd)
                shutil.copy2(str(abs_path), temp_path)
                self.preview_pdf_temp_path = temp_path
                self.preview_pdf_doc = QPdfDocument(self)
                self.preview_pdf.setDocument(self.preview_pdf_doc)
                self.preview_text.hide()
                self.preview_pdf_doc.load(temp_path)
                self.preview_pdf.show()
            except Exception as e:
                self.preview_text.setPlainText(f"PDF 预览失败: {e}")
        elif ext == ".docx":
            self.preview_text.setPlainText("DOCX 预览暂以系统打开方式支持。\n点击下方按钮可在默认程序中打开。")
        else:
            self.preview_text.setPlainText("暂不支持该格式的内嵌预览，可点击下方按钮在系统中打开。")

    def refresh_rule_hint(self, rel_path):
        if not getattr(config, "auto_rule_enabled", False):
            self.rule_hint_label.setText("自动归类未启用")
            return
        name, target_dir = FileManager.suggest_rule_target(Path(rel_path).name)
        if target_dir:
            self.rule_hint_label.setText(f"建议: {name} -> {target_dir}")
        else:
            self.rule_hint_label.setText("未匹配到规则")

    def clear_preview_resources(self, keep_label=False):
        try:
            old_doc = self.preview_pdf.document()
            self.preview_pdf.setDocument(None)
            if old_doc is not None:
                old_doc.deleteLater()
        except Exception:
            pass
        self.preview_pdf.hide()
        self.preview_image.hide()
        if not keep_label:
            self.preview_text.show()
            self.preview_text.clear()
        if self.preview_pdf_temp_path and os.path.exists(self.preview_pdf_temp_path):
            try:
                os.remove(self.preview_pdf_temp_path)
            except Exception:
                pass
        self.preview_pdf_temp_path = None

    def open_current_preview_file(self):
        if not self.current_preview_rel_path:
            return
        ws_root = Path(config.workspace_dir)
        abs_path = ws_root / self.current_preview_rel_path
        if abs_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(abs_path)))

    def apply_batch_tags(self):
        rel_paths = self.get_selected_rel_paths()
        if not rel_paths:
            self.set_operation_status("请先选择至少一个文件。")
            return
        raw = self.batch_tags_input.text().strip()
        tags = [normalize_tag(tag.strip()) for tag in raw.replace(";", ",").split(",") if tag.strip()]
        if not tags:
            self.set_operation_status("请输入要追加的标签。")
            return
        FileManager.bulk_update_tags(rel_paths, tags, mode="append")
        self.run_search()
        self.refresh_other_views_signal.emit()
        self.set_operation_status(f"已为 {len(rel_paths)} 个文件追加标签。")

    def apply_batch_move(self):
        rel_paths = self.get_selected_rel_paths()
        if not rel_paths:
            self.set_operation_status("请先选择至少一个文件。")
            return
        target_dir = self.batch_target_dir.currentText().strip()
        moved = FileManager.bulk_move_files(rel_paths, target_dir)
        self.selection_status_label.setText(f"批量移动完成，共 {len(moved)} 个文件。")
        self.run_search()
        self.refresh_other_views_signal.emit()
        self.set_operation_status(f"已批量移动 {len(moved)} 个文件到 {target_dir}。")

    def apply_rule_suggestion(self):
        if not getattr(config, "auto_rule_enabled", False):
            self.set_operation_status("请先在设置页启用规则归类。")
            return
        rel_paths = self.get_selected_rel_paths()
        if not rel_paths:
            self.set_operation_status("请先选择一个文件。")
            return
        moved = 0
        for rel_path in rel_paths:
            name, target_dir = FileManager.suggest_rule_target(Path(rel_path).name)
            if target_dir:
                try:
                    FileManager.bulk_move_files([rel_path], target_dir)
                    moved += 1
                except Exception:
                    pass
        self.run_search()
        self.refresh_other_views_signal.emit()
        self.set_operation_status(f"已按规则归类 {moved} 个文件。")

    def refresh_rule_hint_for_current_selection(self):
        if self.current_preview_rel_path:
            self.refresh_rule_hint(self.current_preview_rel_path)

    def show_duplicates(self, activate=True):
        modes = {"文件名": "filename", "大小": "size", "哈希": "hash"}
        mode = modes[self.duplicate_mode_combo.currentText()]
        duplicates = FileManager.find_duplicates(mode=mode)
        self.duplicates_list.clear()
        self.duplicate_groups = {}
        if not duplicates:
            self.duplicates_list.addItem(make_empty_item("未发现重复文件", "当前规则下没有需要处理的重复项。", "success"))
            self.set_operation_status("未发现重复文件。")
            if activate:
                self.preview_tabs.setCurrentWidget(self.duplicates_list)
            return

        for index, (group_key, records) in enumerate(duplicates.items(), start=1):
            group_id = f"group-{index}"
            total_size = sum(record.get("file_size", 0) or 0 for record in records)
            largest_size = max((record.get("file_size", 0) or 0 for record in records), default=0)
            reclaim_size = max(0, total_size - largest_size)
            sample_paths = " | ".join(record["filepath"] for record in records[:2])
            if len(records) > 2:
                sample_paths += f" | 另 {len(records) - 2} 个"
            header = QListWidgetItem()
            header.setFlags(Qt.ItemIsEnabled)
            header.setSizeHint(QSize(0, 112))
            header.setData(Qt.UserRole, {"group_id": group_id})
            self.duplicates_list.addItem(header)
            self.duplicates_list.setItemWidget(
                header,
                self.create_duplicate_group_card(
                    group_id=group_id,
                    index=index,
                    group_key=group_key,
                    records=records,
                    total_size=total_size,
                    reclaim_size=reclaim_size,
                    sample_paths=sample_paths,
                )
            )
            self.duplicate_groups[group_id] = {
                "records": records,
                "children": [],
                "collapsed": False,
            }
            for record in records:
                rel_path = record["filepath"]
                item = QListWidgetItem(f"{Path(rel_path).name}    {format_bytes(record.get('file_size', 0))}\n{rel_path}")
                item.setIcon(self.get_file_type_icon(rel_path))
                item.setSizeHint(QSize(0, 54))
                item.setToolTip(rel_path)
                item.setData(Qt.UserRole, rel_path)
                item.setData(Qt.UserRole + 1, group_id)
                self.duplicates_list.addItem(item)
                self.duplicate_groups[group_id]["children"].append(item)
        self.set_operation_status(f"发现 {len(duplicates)} 组重复文件，选择要删除的重复项。")
        if activate:
            self.preview_tabs.setCurrentWidget(self.duplicates_list)

    def create_duplicate_group_card(self, group_id, index, group_key, records, total_size, reclaim_size, sample_paths):
        card = QFrame()
        card.setObjectName("DuplicateGroupCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel()
        icon_label.setPixmap(line_icon("duplicate", size=22).pixmap(22, 22))
        top_row.addWidget(icon_label)

        title = QLabel(f"重复组 {index} · {len(records)} 个文件")
        title.setObjectName("DuplicateGroupTitle")
        top_row.addWidget(title, 1)

        meta = QLabel(f"总计 {format_bytes(total_size)} · 可清理约 {format_bytes(reclaim_size)}")
        meta.setObjectName("DuplicateGroupMeta")
        top_row.addWidget(meta)
        layout.addLayout(top_row)

        detail = QLabel(f"匹配值: {group_key}\n路径: {sample_paths}")
        detail.setObjectName("DuplicateGroupDetail")
        detail.setWordWrap(True)
        layout.addWidget(detail)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.addStretch()
        select_btn = QPushButton("选择重复项")
        select_btn.setObjectName("ToolbarBtn")
        select_btn.setIcon(line_icon("success", size=14))
        select_btn.setIconSize(QSize(14, 14))
        select_btn.clicked.connect(lambda: self.select_duplicate_group(group_id, include_first=False))
        action_row.addWidget(select_btn)

        keep_btn = QPushButton("保留首个")
        keep_btn.setObjectName("ToolbarPrimaryBtn")
        keep_btn.setIcon(line_icon("delete", "#FFFFFF", 14))
        keep_btn.setIconSize(QSize(14, 14))
        keep_btn.clicked.connect(lambda: self.delete_duplicate_group_except_first(group_id))
        action_row.addWidget(keep_btn)

        toggle_btn = QPushButton("折叠")
        toggle_btn.setObjectName("ToolbarBtn")
        toggle_btn.clicked.connect(lambda: self.toggle_duplicate_group(group_id, toggle_btn))
        action_row.addWidget(toggle_btn)
        layout.addLayout(action_row)
        return card

    def select_duplicate_group(self, group_id, include_first=False):
        group = self.duplicate_groups.get(group_id)
        if not group:
            return
        self.duplicates_list.clearSelection()
        children = group["children"] if include_first else group["children"][1:]
        for item in children:
            item.setSelected(True)
        self.set_operation_status(f"已选择本组 {len(children)} 个可处理重复项。")

    def toggle_duplicate_group(self, group_id, button):
        group = self.duplicate_groups.get(group_id)
        if not group:
            return
        group["collapsed"] = not group["collapsed"]
        for item in group["children"]:
            item.setHidden(group["collapsed"])
        button.setText("展开" if group["collapsed"] else "折叠")

    def delete_duplicate_group_except_first(self, group_id):
        group = self.duplicate_groups.get(group_id)
        if not group:
            return
        paths = [record["filepath"] for record in group["records"][1:]]
        if not paths:
            self.set_operation_status("该重复组没有可删除的其余文件。")
            return
        self.delete_duplicate_paths(paths, label="该重复组中除首个外的文件")

    def on_duplicate_item_double_clicked(self, item):
        rel_path = item.data(Qt.UserRole)
        if not isinstance(rel_path, str) or not rel_path:
            return
        self.current_preview_rel_path = rel_path
        self.load_preview(rel_path)
        self.preview_tabs.setCurrentWidget(self.preview_stack)

    def _get_duplicate_selected_paths(self):
        selected = []
        for item in self.duplicates_list.selectedItems():
            rel_path = item.data(Qt.UserRole)
            if isinstance(rel_path, str) and rel_path:
                selected.append(rel_path)
        return selected

    def delete_selected_duplicate_files(self):
        target_paths = self._get_duplicate_selected_paths()
        if not target_paths:
            target_paths = self.get_selected_rel_paths()
        if not target_paths and self.current_preview_rel_path:
            target_paths = [self.current_preview_rel_path]
        target_paths = list(dict.fromkeys(target_paths))

        if not target_paths:
            self.set_operation_status("请先选择一个文件。")
            return
        self.delete_duplicate_paths(target_paths, label="选中的文件")

    def delete_duplicate_paths(self, target_paths, label="选中的文件"):
        target_paths = list(dict.fromkeys(target_paths))
        preview = "\n".join(target_paths[:5])
        if len(target_paths) > 5:
            preview += f"\n... 以及 {len(target_paths) - 5} 个文件"
        reply = QMessageBox.question(self, "确认删除文件",
                                     f"确认删除{label}（共 {len(target_paths)} 个）吗？\n{preview}\n此操作会永久删除磁盘上的文件。",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        deleted = 0
        try:
            for target_rel_path in target_paths:
                FileManager.delete_file(target_rel_path)
                deleted += 1
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除文件失败: {str(e)}")
            return
        self.clear_preview_resources()
        self.current_preview_rel_path = ""
        self.run_search()
        self.show_duplicates(activate=False)
        self.refresh_other_views_signal.emit()
        self.set_operation_status(f"已删除 {deleted} 个文件。")

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
                self.grid_title.setText(f"目录 {self.current_folder_rel} 中的文件列表")
            except ValueError:
                self.current_folder_rel = ""
                self.grid_title.setText("全部文件列表")
        else:
            # Clicked a file
            self.current_folder_rel = ""
            self.grid_title.setText("全部文件列表")
            
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
        self.file_empty_label.setVisible(len(file_records) == 0)
        
        for i, r in enumerate(file_records):
            self.files_table.insertRow(i)
            
            # File size readable
            sz = r["file_size"]
            sz_str = format_bytes(sz)
            
            # Backup icons
            disk_ok = "已备份" if r["backup_disk_status"] else "未备份"
            cloud_ok = "已备份" if r["backup_cloud_status"] else "未备份"
            backup_str = f"硬盘: {disk_ok} | 云端: {cloud_ok}"
            backup_complete = bool(r["backup_disk_status"] and r["backup_cloud_status"])
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
            item_backup.setIcon(line_icon("success" if backup_complete else "warning", size=16))
            
            # Store full record path inside name item for double click
            item_name.setData(Qt.UserRole, r["filepath"])
            item_name.setIcon(self.get_file_type_icon(r["filename"]))
            
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

    def delete_file(self):
        reply = QMessageBox.question(self, "警告 - 物理删除",
                                     "此操作将永久从磁盘删除该文件！\n确认要删除吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.clear_preview_resources()
            try:
                FileManager.delete_file(self.rel_path)
                QMessageBox.information(self, "成功", "文件已成功从磁盘和数据库中删除！")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除文件失败: {str(e)}")

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
            try:
                FileManager.delete_file(self.rel_path)
                QMessageBox.information(self, "成功", "文件已成功从磁盘和数据库中删除！")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除文件失败: {str(e)}")

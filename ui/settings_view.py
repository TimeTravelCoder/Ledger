import os
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QPushButton, QFrame, 
                             QCheckBox, QMessageBox, QFileDialog, QTextEdit, 
                             QComboBox, QScrollArea, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from config import config, DEFAULT_TAGS, normalize_tags, display_tag, NAME_PRESET_BASES
from file_manager import FileManager

class SettingsView(QWidget):
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
        
        inner_layout = QVBoxLayout(scroll_content)
        inner_layout.setContentsMargins(24, 24, 24, 24)
        inner_layout.setSpacing(20)
        
        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)
        

        # Header
        header = QLabel("系统参数设置")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        inner_layout.addWidget(header)

        # 1. Directory Settings Card
        dir_card = QFrame()
        dir_card.setObjectName("CardPanel")
        dir_layout = QVBoxLayout(dir_card)
        dir_layout.setContentsMargins(15, 15, 15, 15)
        dir_layout.setSpacing(15)

        dir_title = QLabel("路径参数配置")
        dir_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        dir_layout.addWidget(dir_title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Workspace Root
        grid.addWidget(QLabel("主工作空间目录 (Workspace):"), 0, 0)
        self.input_ws_path = QLineEdit(config.workspace_dir)
        grid.addWidget(self.input_ws_path, 0, 1)
        self.btn_browse_ws = QPushButton("浏览...")
        self.btn_browse_ws.clicked.connect(self.browse_workspace)
        grid.addWidget(self.btn_browse_ws, 0, 2)

        # Downloads Folder
        grid.addWidget(QLabel("浏览器下载目录 (Downloads):"), 1, 0)
        self.input_dl_path = QLineEdit(config.downloads_dir)
        grid.addWidget(self.input_dl_path, 1, 1)
        self.btn_browse_dl = QPushButton("浏览...")
        self.btn_browse_dl.clicked.connect(self.browse_downloads)
        grid.addWidget(self.btn_browse_dl, 1, 2)

        dir_layout.addLayout(grid)

        # Monitored toggle
        self.cb_monitor_dl = QCheckBox("在后台自动监控 Downloads 文件夹的变化 (自动弹出提醒)")
        self.cb_monitor_dl.setChecked(config.monitored_downloads)
        self.cb_monitor_dl.stateChanged.connect(self.save_monitored)
        dir_layout.addWidget(self.cb_monitor_dl)

        self.theme_hint = QLabel(f"当前主题: {config.theme}")
        self.theme_hint.setStyleSheet("color: #85B3CB; font-size: 11px;")
        dir_layout.addWidget(self.theme_hint)

        # Initializer Button
        init_layout = QHBoxLayout()
        self.btn_init_ws = QPushButton("一键初始化/修复标准目录结构")
        self.btn_init_ws.setObjectName("PrimaryBtn")
        self.btn_init_ws.clicked.connect(self.run_init_workspace)
        init_layout.addWidget(self.btn_init_ws)
        
        self.btn_save_paths = QPushButton("应用路径并重新加载")
        self.btn_save_paths.clicked.connect(self.save_paths)
        init_layout.addWidget(self.btn_save_paths)
        dir_layout.addLayout(init_layout)

        inner_layout.addWidget(dir_card)

        # 1.5 New Workspace Wizard Card
        wizard_card = QFrame()
        wizard_card.setObjectName("CardPanel")
        wizard_layout = QVBoxLayout(wizard_card)
        wizard_layout.setContentsMargins(15, 15, 15, 15)
        wizard_layout.setSpacing(15)

        wizard_title = QLabel("新建工作空间向导 (一键生成中/英文规范)")
        wizard_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #6366F1;")
        wizard_layout.addWidget(wizard_title)

        wizard_desc = QLabel("选择任意盘符或目录，系统将在此目录下创建 'Workspace' 文件夹，并自动初始化 12 个分类模板目录。")
        wizard_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        wizard_layout.addWidget(wizard_desc)

        wiz_grid = QGridLayout()
        wiz_grid.setSpacing(10)

        wiz_grid.addWidget(QLabel("选择目标路径:"), 0, 0)
        self.input_wiz_path = QLineEdit()
        self.input_wiz_path.setPlaceholderText("选择任一磁盘目录，例如 D:/ 或 E:/KnowledgeHub")
        wiz_grid.addWidget(self.input_wiz_path, 0, 1)
        self.btn_wiz_browse = QPushButton("选择盘符/目录...")
        self.btn_wiz_browse.clicked.connect(self.browse_wizard_path)
        wiz_grid.addWidget(self.btn_wiz_browse, 0, 2)

        wiz_grid.addWidget(QLabel("标准分类模版规范:"), 1, 0)
        self.wiz_lang_combo = QComboBox()
        self.wiz_lang_combo.addItems([
            "中文标准模版 (00_收集箱, 01_课程学习, 02_课题研究...)",
            "英文标准模版 (00_Inbox, 01_Study, 02_Research...)",
            "自建自定义分类模版 (使用下方设置的自建分类模板)"
        ])
        wiz_grid.addWidget(self.wiz_lang_combo, 1, 1, 1, 2)

        wizard_layout.addLayout(wiz_grid)

        self.btn_run_wiz = QPushButton("一键生成工作空间文件夹")
        self.btn_run_wiz.setObjectName("SuccessBtn")
        self.btn_run_wiz.clicked.connect(self.run_workspace_wizard)
        wizard_layout.addWidget(self.btn_run_wiz)

        inner_layout.addWidget(wizard_card)

        # 2. Tag System Customization Card
        tag_card = QFrame()
        tag_card.setObjectName("CardPanel")
        tag_layout = QVBoxLayout(tag_card)
        tag_layout.setContentsMargins(15, 15, 15, 15)
        tag_layout.setSpacing(15)

        tag_title = QLabel("自定义标签字典体系")
        tag_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        tag_layout.addWidget(tag_title)

        tag_desc = QLabel("以逗号分隔输入标签；写不写 # 都可以，系统会自动兼容。")
        tag_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        tag_layout.addWidget(tag_desc)

        tag_grid = QGridLayout()
        tag_grid.setSpacing(10)

        # Primary Tags
        tag_grid.addWidget(QLabel("一级分类标签:"), 0, 0)
        self.input_p_tags = QLineEdit(",".join(display_tag(tag) for tag in config.tags["primary"]))
        tag_grid.addWidget(self.input_p_tags, 0, 1)

        # Secondary Tags
        tag_grid.addWidget(QLabel("二级属性标签:"), 1, 0)
        self.input_s_tags = QLineEdit(",".join(display_tag(tag) for tag in config.tags["secondary"]))
        tag_grid.addWidget(self.input_s_tags, 1, 1)

        # Status Tags
        tag_grid.addWidget(QLabel("状态标记标签:"), 2, 0)
        self.input_st_tags = QLineEdit(",".join(display_tag(tag) for tag in config.tags["status"]))
        tag_grid.addWidget(self.input_st_tags, 2, 1)

        tag_layout.addLayout(tag_grid)

        # Save tags button
        tag_btn_layout = QHBoxLayout()
        self.btn_save_tags = QPushButton("保存标签修改")
        self.btn_save_tags.clicked.connect(self.save_tags)
        tag_btn_layout.addWidget(self.btn_save_tags)
        
        self.btn_reset_tags = QPushButton("恢复默认标签规范")
        self.btn_reset_tags.clicked.connect(self.reset_tags_to_default)
        tag_btn_layout.addWidget(self.btn_reset_tags)
        
        tag_layout.addLayout(tag_btn_layout)
        inner_layout.addWidget(tag_card)

        # 3. Custom Category Template Card
        custom_card = QFrame()
        custom_card.setObjectName("CardPanel")
        custom_layout = QVBoxLayout(custom_card)
        custom_layout.setContentsMargins(15, 15, 15, 15)
        custom_layout.setSpacing(15)

        custom_title = QLabel("自建分类目录模板与规范")
        custom_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #10B981;")
        custom_layout.addWidget(custom_title)

        custom_desc = QLabel("启用自建模板后，系统将使用您自定义的分类文件夹结构。各个文件夹以英文逗号分隔。")
        custom_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        custom_layout.addWidget(custom_desc)

        self.cb_use_custom_dirs = QCheckBox("启用自建分类模板 (不勾选则默认使用标准中/英文模板)")
        self.cb_use_custom_dirs.setChecked(config.use_custom_dirs)
        self.cb_use_custom_dirs.stateChanged.connect(self.save_use_custom_dirs)
        custom_layout.addWidget(self.cb_use_custom_dirs)

        grid_custom = QHBoxLayout()
        grid_custom.addWidget(QLabel("自建目录结构 (英文逗号分隔):"))
        self.input_custom_dirs = QLineEdit(", ".join(config.custom_standard_dirs))
        if not config.custom_standard_dirs:
            # Fallback placeholder showing an example
            self.input_custom_dirs.setPlaceholderText("例如: 00收集箱, 01学习, 02工作, 03生活, 04娱乐, 99临时缓冲")
        grid_custom.addWidget(self.input_custom_dirs, 1)
        custom_layout.addLayout(grid_custom)

        custom_btn_layout = QHBoxLayout()
        self.btn_save_custom_dirs = QPushButton("保存并应用自建分类模板")
        self.btn_save_custom_dirs.setObjectName("PrimaryBtn")
        self.btn_save_custom_dirs.clicked.connect(self.save_custom_dirs)
        custom_btn_layout.addWidget(self.btn_save_custom_dirs)
        custom_layout.addLayout(custom_btn_layout)

        inner_layout.addWidget(custom_card)

        # 4. Auto Rule Routing Card
        rule_card = QFrame()
        rule_card.setObjectName("CardPanel")
        rule_layout = QVBoxLayout(rule_card)
        rule_layout.setContentsMargins(15, 15, 15, 15)
        rule_layout.setSpacing(12)

        rule_title = QLabel("规则归类自动化")
        rule_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #6366F1;")
        rule_layout.addWidget(rule_title)

        self.cb_auto_rule = QCheckBox("启用关键词 / 后缀自动归类")
        self.cb_auto_rule.setChecked(config.auto_rule_enabled)
        self.cb_auto_rule.stateChanged.connect(self.save_auto_rule_enabled)
        rule_layout.addWidget(self.cb_auto_rule)

        self.rule_scroll = QScrollArea()
        self.rule_scroll.setWidgetResizable(True)
        self.rule_scroll.setFrameShape(QFrame.NoFrame)
        self.rule_scroll.setMinimumHeight(220)
        self.rule_scroll_content = QWidget()
        self.rule_scroll_layout = QVBoxLayout(self.rule_scroll_content)
        self.rule_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.rule_scroll_layout.setSpacing(8)
        self.rule_scroll.setWidget(self.rule_scroll_content)
        rule_layout.addWidget(self.rule_scroll)

        self.populate_rule_list()

        rule_btn_layout = QHBoxLayout()
        self.btn_save_rules = QPushButton("保存规则")
        self.btn_save_rules.setObjectName("PrimaryBtn")
        self.btn_save_rules.clicked.connect(self.save_auto_rules)
        rule_btn_layout.addWidget(self.btn_save_rules)
        rule_layout.addLayout(rule_btn_layout)

        inner_layout.addWidget(rule_card)

        # 5. Naming Preset Templates Card
        preset_card = QFrame()
        preset_card.setObjectName("CardPanel")
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(15, 15, 15, 15)
        preset_layout.setSpacing(12)

        preset_title = QLabel("命名规范模板")
        preset_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #6366F1;")
        preset_layout.addWidget(preset_title)

        preset_desc = QLabel("支持自定义添加模板；格式变量示例：{date} {topic} {version} {status} {stem}")
        preset_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        preset_desc.setWordWrap(True)
        preset_layout.addWidget(preset_desc)

        self.preset_list = QListWidget()
        self.preset_list.setMinimumHeight(220)
        preset_layout.addWidget(self.preset_list)

        self.populate_name_presets()

        preset_edit = QGridLayout()
        preset_edit.setSpacing(8)
        self.input_preset_label = QLineEdit()
        self.input_preset_label.setPlaceholderText("模板名称")
        self.input_preset_prefix = QLineEdit()
        self.input_preset_prefix.setPlaceholderText("目录前缀，例如 01 / 05 / 08")
        self.input_preset_format = QLineEdit()
        self.input_preset_format.setPlaceholderText("格式，例如 {date}_{topic}_{version}")
        preset_edit.addWidget(QLabel("名称"), 0, 0)
        preset_edit.addWidget(self.input_preset_label, 0, 1)
        preset_edit.addWidget(QLabel("前缀"), 0, 2)
        preset_edit.addWidget(self.input_preset_prefix, 0, 3)
        preset_edit.addWidget(QLabel("格式"), 1, 0)
        preset_edit.addWidget(self.input_preset_format, 1, 1, 1, 3)
        preset_layout.addLayout(preset_edit)

        preset_btn_layout = QHBoxLayout()
        self.btn_preset_add = QPushButton("新增模板")
        self.btn_preset_add.clicked.connect(self.add_name_preset)
        preset_btn_layout.addWidget(self.btn_preset_add)
        self.btn_preset_delete = QPushButton("删除模板")
        self.btn_preset_delete.clicked.connect(self.delete_name_preset)
        preset_btn_layout.addWidget(self.btn_preset_delete)
        self.btn_preset_save = QPushButton("保存模板")
        self.btn_preset_save.setObjectName("PrimaryBtn")
        self.btn_preset_save.clicked.connect(self.save_name_presets)
        preset_btn_layout.addWidget(self.btn_preset_save)
        preset_layout.addLayout(preset_btn_layout)

        inner_layout.addWidget(preset_card)

        inner_layout.addStretch()

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
        
        if not ws or not dl:
            QMessageBox.warning(self, "错误", "路径不能为空！")
            return
            
        config.workspace_dir = ws
        config.downloads_dir = dl
        config.save()

        # Reload database connection dynamically in db.py!
        from db import db
        db.close() # Connection will reopen automatically at the new path
        
        QMessageBox.information(self, "应用成功", "新路径参数已成功生效并加载！")
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
            QMessageBox.information(self, "成功", f"标准目录结构初始化成功！\n共创建 12 个规范分类文件夹。\n根路径: {config.workspace_dir}")
        else:
            QMessageBox.critical(self, "错误", msg)
            
        self.refresh_other_views_signal.emit()

    def save_tags(self):
        p_str = self.input_p_tags.text().strip()
        s_str = self.input_s_tags.text().strip()
        st_str = self.input_st_tags.text().strip()

        # Sanitize commas and spaces
        def parse_tags_input(raw_str):
            # Split by comma or semicolon
            parts = raw_str.replace(";", ",").split(",")
            return normalize_tags(parts)

        config.tags["primary"] = parse_tags_input(p_str)
        config.tags["secondary"] = parse_tags_input(s_str)
        config.tags["status"] = parse_tags_input(st_str)
        
        config.save()
        QMessageBox.information(self, "成功", "自定义标签字典保存成功！所有界面已同步刷新。")
        self.refresh_other_views_signal.emit()

    def reset_tags_to_default(self):
        reply = QMessageBox.question(self, "确认重置", "是否确定将您的标签字典重置为系统出厂规范定义？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            config.tags = DEFAULT_TAGS.copy()
            config.save()
            
            # Refresh inputs
            self.input_p_tags.setText(",".join(display_tag(tag) for tag in config.tags["primary"]))
            self.input_s_tags.setText(",".join(display_tag(tag) for tag in config.tags["secondary"]))
            self.input_st_tags.setText(",".join(display_tag(tag) for tag in config.tags["status"]))
            
            QMessageBox.information(self, "成功", "标签字典已重置为规范默认设置！")
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
        if idx == 0:
            chosen_lang = "cn"
            config.use_custom_dirs = False
        elif idx == 1:
            chosen_lang = "en"
            config.use_custom_dirs = False
        else:
            config.use_custom_dirs = True
            if not config.custom_standard_dirs:
                QMessageBox.warning(self, "警告", "请先在下方配置并保存您的“自建分类目录模板”！")
                return
        
        reply = QMessageBox.question(
            self, "确认生成工作空间", 
            f"系统即将在以下位置生成全新的规范工作空间：\n👉 {target_path}\n\n文件夹规范：{self.wiz_lang_combo.currentText()}\n是否确认生成并自动切换至此工作空间？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # 1. Physically create workspace and directories
            success, msg = FileManager.init_workspace(custom_ws_dir=str(target_path), custom_lang=chosen_lang)
            if not success:
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
            
            QMessageBox.information(
                self, "生成成功 🎉", 
                f"新工作空间已成功生成并自动切换！\n当前工作空间：\n👉 {target_path}"
            )
            
            self.input_wiz_path.clear()
            self.refresh_other_views_signal.emit()

    def save_use_custom_dirs(self, state):
        config.use_custom_dirs = bool(state)
        config.save()
        self.refresh_other_views_signal.emit()

    def populate_rule_list(self):
        while self.rule_scroll_layout.count():
            item = self.rule_scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.rule_widgets = []
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
        QMessageBox.information(self, "成功", "规则归类配置已保存。")
        self.refresh_other_views_signal.emit()

    def populate_name_presets(self):
        self.preset_list.clear()
        self.name_presets = []
        for base in NAME_PRESET_BASES:
            self.name_presets.append({
                "label": base["label"],
                "prefix": base["prefix"],
                "format": base["default_format"],
                "base": True
            })
        for item in getattr(config, "custom_name_templates", []):
            self.name_presets.append({
                "label": item.get("label", "自定义"),
                "prefix": item.get("prefix", "01"),
                "format": item.get("format", "{date}_{topic}"),
                "base": False
            })
        for preset in self.name_presets:
            li = QListWidgetItem(f"{preset['label']} | 前缀: {preset['prefix']} | 格式: {preset['format']}")
            li.setData(Qt.UserRole, preset)
            self.preset_list.addItem(li)

    def add_name_preset(self):
        self.name_presets.append({"label": "新模板", "prefix": "01", "format": "{date}_{topic}", "base": False})
        self.sync_name_preset_inputs()

    def delete_name_preset(self):
        row = self.preset_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中一个模板。")
            return
        preset = self.preset_list.item(row).data(Qt.UserRole)
        if preset and preset.get("base"):
            QMessageBox.information(self, "提示", "基础模板不能删除。")
            return
        custom = [p for p in self.name_presets if p.get("label") != preset.get("label")]
        self.name_presets = custom
        self.sync_name_preset_inputs()

    def sync_name_preset_inputs(self):
        custom = [p for p in self.name_presets if not p.get("base")]
        config.custom_name_templates = custom
        self.populate_name_presets()

    def save_name_presets(self):
        config.custom_name_templates = [p for p in self.name_presets if not p.get("base")]
        config.save()
        QMessageBox.information(self, "成功", "命名模板已保存。")
        self.refresh_other_views_signal.emit()

    def save_custom_dirs(self):
        raw_dirs = self.input_custom_dirs.text().strip()
        if not raw_dirs:
            QMessageBox.warning(self, "警告", "自建目录结构不能为空！")
            return
            
        parts = [p.strip() for p in raw_dirs.replace("；", ",").replace(";", ",").split(",") if p.strip()]
        if not parts:
            QMessageBox.warning(self, "警告", "自建目录结构格式不正确！")
            return
            
        config.custom_standard_dirs = parts
        config.save()
        QMessageBox.information(self, "成功", "自建分类模板保存成功！可在上方“一键初始化/修复标准目录结构”或“新建工作空间向导”中直接套用。")
        self.refresh_other_views_signal.emit()

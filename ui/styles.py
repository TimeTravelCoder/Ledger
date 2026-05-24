def get_stylesheet(theme="dark"):
    """
    Returns a highly polished, custom QSS stylesheet for either dark or light theme.
    """
    if theme == "dark":
        # Premium Cyber Dark theme - Neon indigo accent
        bg_primary = "#090D16"
        bg_secondary = "#0F172A"
        bg_tertiary = "#1E293B"
        bg_glass = "rgba(15, 23, 42, 0.45)"
        text_primary = "#F1F5F9"
        text_secondary = "#94A3B8"
        text_disabled = "#475569"
        border_color = "rgba(255, 255, 255, 0.08)"
        border_glass = "rgba(255, 255, 255, 0.06)"
        border_hover = "#818CF8"
        accent_color = "#6366F1"
        success_color = "#34D399"
        success_hover = "#10B981"
        warning_color = "#F59E0B"
        error_color = "#F43F5E"
        error_hover = "#EF4444"
        shadow_effect = "rgba(99, 102, 241, 0.25)"
        text_on_accent = "#FFFFFF"
    elif theme == "zhongguose":
        # Elegant Traditional Chinese Jade Green theme
        bg_primary = "#F4F7F5"
        bg_secondary = "#FCFBF9"
        bg_tertiary = "#EBF2EE"
        bg_glass = "rgba(252, 251, 249, 0.65)"
        text_primary = "#1E2D24"
        text_secondary = "#3D5B48"
        text_disabled = "#8FA89B"
        border_color = "rgba(180, 200, 190, 0.45)"
        border_glass = "rgba(180, 200, 190, 0.35)"
        border_hover = "#059669"
        accent_color = "#047857"
        success_color = "#10B981"
        success_hover = "#059669"
        warning_color = "#D97706"
        error_color = "#DC2626"
        error_hover = "#EF4444"
        shadow_effect = "rgba(4, 120, 87, 0.12)"
        text_on_accent = "#FFFFFF"
    else:
        # Modern Premium Slate Light theme
        bg_primary = "#F8FAFC"
        bg_secondary = "#FFFFFF"
        bg_tertiary = "#F1F5F9"
        bg_glass = "rgba(255, 255, 255, 0.55)"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        text_disabled = "#94A3B8"
        border_color = "rgba(15, 23, 42, 0.08)"
        border_glass = "rgba(15, 23, 42, 0.06)"
        border_hover = "#6366F1"
        accent_color = "#4F46E5"
        success_color = "#10B981"
        success_hover = "#059669"
        warning_color = "#F59E0B"
        error_color = "#EF4444"
        error_hover = "#DC2626"
        shadow_effect = "rgba(79, 70, 229, 0.12)"
        text_on_accent = "#FFFFFF"

    qss = f"""
    /* General Application Styling */
    QWidget {{
        font-family: "Segoe UI", "Microsoft YaHei", "Inter", sans-serif;
        font-size: 13px;
        color: {text_primary};
        background-color: transparent;
    }}

    QMainWindow {{
        background-color: {bg_primary};
    }}

    /* Sidebar Styling */
    QFrame#Sidebar {{
        background-color: {bg_secondary};
        border-right: 1px solid {border_color};
    }}

    QLabel#SidebarTitle {{
        font-size: 16px;
        font-weight: bold;
        color: {text_primary};
        padding: 10px;
    }}

    /* Sidebar Navigation Buttons */
    QPushButton#SidebarBtn {{
        text-align: left;
        padding: 11px 14px;
        border: none;
        border-radius: 8px;
        color: {text_secondary};
        font-weight: 500;
        margin: 4px 10px;
        icon-size: 18px;
    }}

    QPushButton#SidebarBtn:hover {{
        background-color: {bg_tertiary};
        color: {text_primary};
    }}

    QPushButton#SidebarBtn:checked {{
        background: {accent_color};
        color: {text_on_accent};
        font-weight: bold;
    }}

    QPushButton#SidebarBtn[compact="true"] {{
        text-align: center;
        padding: 12px 10px;
        margin: 5px 12px;
    }}

    /* Theme Toggle Button */
    QPushButton#ThemeToggleBtn {{
        background-color: {bg_tertiary};
        border: 1px solid {border_color};
        border-radius: 6px;
        padding: 6px 12px;
        color: {text_primary};
        font-weight: 500;
    }}
    QPushButton#ThemeToggleBtn:hover {{
        border-color: {accent_color};
        background-color: {bg_secondary};
    }}

    QPushButton#ThemeToggleBtn[compact="true"] {{
        padding: 8px;
        margin: 0 6px;
    }}

    /* Main Container Panel */
    QFrame#MainContainer {{
        background-color: {bg_primary};
        padding: 20px;
    }}

    /* Modern Dashboard Card Panel with Glassmorphism */
    QFrame#CardPanel {{
        background-color: {bg_glass};
        border: 1px solid {border_glass};
        border-radius: 12px;
    }}

    QFrame#PreviewInfoCard {{
        background-color: {bg_glass};
        border: 1px solid {border_glass};
        border-radius: 10px;
    }}

    QFrame#ToolbarPanel {{
        background-color: {bg_glass};
        border: 1px solid {border_glass};
        border-radius: 14px;
    }}

    QFrame#SearchBox {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 12px;
    }}

    QFrame#SearchBox:hover {{
        border-color: {accent_color};
    }}

    QFrame#ToolbarFilterCluster {{
        background-color: transparent;
        border: none;
    }}

    QFrame#ToolbarActionCluster {{
        background-color: transparent;
        border: none;
    }}

    QFrame#TagRail {{
        background-color: transparent;
        border: none;
    }}

    QFrame#BatchToolbar {{
        background-color: {bg_primary};
        border: 1px solid {border_color};
        border-radius: 12px;
    }}

    QFrame#BatchToolbar[active="true"] {{
        background-color: {bg_glass};
        border: 1px solid {accent_color};
    }}

    QFrame#BatchToolbarGroup {{
        background-color: {bg_glass};
        border: 1px solid {border_glass};
        border-radius: 10px;
    }}

    QFrame#BatchToolbar[active="true"] QFrame#BatchToolbarGroup {{
        background-color: {bg_primary};
        border-color: {border_hover};
    }}

    QFrame#InsightStrip {{
        background-color: {bg_glass};
        border: 1px solid {border_glass};
        border-radius: 12px;
    }}

    QFrame#DuplicateGroupCard {{
        background-color: {bg_primary};
        border: 1px solid {border_color};
        border-radius: 10px;
    }}

    QFrame#RenamePreviewCard {{
        background-color: {bg_primary};
        border: 1px dashed {border_hover};
        border-radius: 10px;
    }}

    QLabel#CardTitle {{
        font-size: 12px;
        font-weight: bold;
        color: {text_secondary};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    QLabel#CardValue {{
        font-size: 24px;
        font-weight: bold;
        color: {text_primary};
    }}

    QLabel#MetricIcon {{
        background-color: {bg_tertiary};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 5px;
    }}

    QLabel#InsightChip {{
        background-color: {bg_primary};
        border: 1px solid {border_color};
        border-radius: 10px;
        padding: 5px 10px;
        color: {text_secondary};
        font-size: 12px;
        font-weight: 700;
    }}

    QLabel#PreviewFileName {{
        font-size: 13px;
        font-weight: 700;
        color: {text_primary};
    }}

    QLabel#PreviewFilePath, QLabel#PreviewInfoPath {{
        font-size: 11px;
        color: {text_disabled};
    }}

    QLabel#PreviewMetaChip {{
        background-color: {bg_tertiary};
        border: 1px solid {border_color};
        border-radius: 9px;
        padding: 3px 8px;
        color: {text_secondary};
        font-size: 11px;
    }}

    /* Input Fields (QLineEdit, QTextEdit) */
    QLineEdit, QTextEdit, QLineEdit:read-only, QTextEdit:read-only {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 8px 12px;
        color: {text_primary};
        selection-background-color: {accent_color};
    }}

    QLineEdit:focus, QTextEdit:focus {{
        border: 1px solid {border_hover};
    }}

    QLineEdit:disabled, QTextEdit:disabled {{
        background-color: {bg_primary};
        color: {text_disabled};
        border-color: {border_color};
    }}

    QLineEdit#ErrorInput {{
        border: 1px solid {error_color};
    }}

    QLineEdit#SuccessInput {{
        border: 1px solid {success_color};
    }}

    QLineEdit#ToolbarSearchInput {{
        background-color: transparent;
        border: none;
        padding: 6px 2px;
        font-size: 13px;
        font-weight: 600;
    }}

    QLabel#MutedText {{
        color: {text_disabled};
        font-size: 12px;
    }}

    QLabel#SettingsCardTitle {{
        font-size: 14px;
        font-weight: 700;
        color: {accent_color};
        border-bottom: 2px solid {bg_tertiary};
        padding-bottom: 6px;
    }}

    /* Tag Capsules Pools */
    QFrame#TagCapsule_primary {{
        background-color: rgba(79, 70, 229, 0.08);
        border: 1px solid {accent_color};
        border-radius: 12px;
    }}

    QFrame#TagCapsule_primary QLabel {{
        color: {accent_color};
    }}

    QFrame#TagCapsule_secondary {{
        background-color: rgba(5, 150, 105, 0.08);
        border: 1px solid {success_color};
        border-radius: 12px;
    }}

    QFrame#TagCapsule_secondary QLabel {{
        color: {success_color};
    }}

    QFrame#TagCapsule_status {{
        background-color: rgba(217, 119, 6, 0.08);
        border: 1px solid {warning_color};
        border-radius: 12px;
    }}

    QFrame#TagCapsule_status QLabel {{
        color: {warning_color};
    }}

    QPushButton#CapsuleCloseBtn {{
        border: none;
        background: transparent;
        color: {text_disabled};
        font-size: 13px;
        font-weight: bold;
        padding: 0px 2px;
    }}

    QPushButton#CapsuleCloseBtn:hover {{
        color: {error_color};
    }}

    QLineEdit#TagQuickAddInput {{
        font-size: 12px;
        padding: 6px 10px;
    }}

    /* Sleek line progress bar for disk usage */
    QProgressBar#DiskUsageBar {{
        border: none;
        border-radius: 4px;
        background-color: {bg_tertiary};
        height: 8px;
    }}

    QProgressBar#DiskUsageBar::chunk {{
        background-color: {accent_color};
        border-radius: 4px;
    }}

    QLabel#ToolbarLabel, QLabel#BatchHint {{
        color: {text_disabled};
        font-size: 12px;
        font-weight: 600;
    }}

    QPushButton#FilterChip {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 14px;
        padding: 4px 11px;
        color: {text_secondary};
        font-size: 11px;
        font-weight: 700;
    }}

    QPushButton#FilterChip:hover {{
        background-color: {bg_tertiary};
        border-color: {border_hover};
        color: {text_primary};
    }}

    QPushButton#FilterChip:checked {{
        background: {accent_color};
        border: 1px solid {accent_color};
        color: {text_on_accent};
        font-weight: bold;
    }}

    QPushButton#FilterChip:checked:hover {{
        background: {border_hover};
        border: 1px solid {border_hover};
        color: {text_on_accent};
    }}

    QLabel#BatchStatus {{
        color: {text_secondary};
        font-size: 12px;
        font-weight: 700;
    }}

    QLabel#EmptyState {{
        background-color: {bg_primary};
        border: 1px dashed {border_color};
        border-radius: 12px;
        padding: 12px;
        color: {text_disabled};
        font-size: 12px;
        font-weight: 600;
    }}

    QLabel#DuplicateGroupTitle {{
        color: {text_primary};
        font-size: 13px;
        font-weight: 800;
    }}

    QLabel#DuplicateGroupMeta {{
        color: {text_secondary};
        font-size: 12px;
        font-weight: 700;
    }}

    QLabel#DuplicateGroupDetail {{
        color: {text_disabled};
        font-size: 11px;
    }}

    /* Normal Push Buttons */
    QPushButton {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 8px 16px;
        color: {text_primary};
        font-weight: 600;
    }}

    QPushButton:hover {{
        background-color: {bg_tertiary};
        border-color: {accent_color};
    }}

    QPushButton:pressed {{
        background: {accent_color};
        color: {text_on_accent};
    }}

    QPushButton#PrimaryBtn {{
        background: {accent_color};
        border: none;
        color: {text_on_accent};
    }}

    QPushButton#PrimaryBtn:hover {{
        background: {border_hover};
    }}

    QPushButton#ToolbarBtn {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 10px;
        padding: 6px 11px;
        color: {text_primary};
        font-weight: 700;
    }}

    QPushButton#ToolbarBtn:hover {{
        background-color: {bg_tertiary};
        border-color: {accent_color};
    }}

    QPushButton#ToolbarBtn[compact="true"], QPushButton#ToolbarPrimaryBtn[compact="true"] {{
        padding: 6px 8px;
        min-width: 30px;
    }}

    QPushButton#ToolbarPrimaryBtn {{
        background: {accent_color};
        border: none;
        border-radius: 10px;
        padding: 6px 12px;
        color: {text_on_accent};
        font-weight: 700;
    }}

    QPushButton#ToolbarPrimaryBtn:hover {{
        background: {border_hover};
    }}

    QPushButton#SuccessBtn {{
        background: {success_color};
        border: none;
        color: #FFFFFF;
    }}
    QPushButton#SuccessBtn:hover {{
        background: {success_hover};
    }}
    QPushButton#SuccessBtn:pressed {{
        background: {success_color};
    }}

    QPushButton#DangerBtn {{
        background: {error_color};
        border: none;
        color: #FFFFFF;
    }}
    QPushButton#DangerBtn:hover {{
        background: {error_hover};
    }}
    QPushButton#DangerBtn:pressed {{
        background: {error_color};
    }}

    /* Checkbox & Radio Buttons */
    QCheckBox {{
        spacing: 8px;
        color: {text_primary};
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {border_color};
        border-radius: 4px;
        background-color: {bg_secondary};
    }}

    QCheckBox::indicator:hover {{
        border-color: {accent_color};
    }}

    QCheckBox::indicator:checked {{
        background-color: {accent_color};
        border-color: {accent_color};
        image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white' width='18px' height='18px'%3E%3Cpath d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E");
    }}

    /* ComboBox (Dropdown) */
    QComboBox {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 6px 12px;
        color: {text_primary};
        combobox-popup: 0;
    }}

    QComboBox:hover {{
        border-color: {accent_color};
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left-width: 0px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }}

    QComboBox::down-arrow {{
        image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2394A3B8' width='12px' height='12px'%3E%3Cpath d='M7 10l5 5 5-5H7z'/%3E%3C/svg%3E");
    }}

    QComboBox QAbstractItemView {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 8px;
        selection-background-color: {accent_color};
        selection-color: #FFFFFF;
        outline: 0;
    }}

    /* Table Widget Styling */
    QTableWidget, QTableView {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 12px;
        gridline-color: transparent;
        alternate-background-color: {bg_primary};
        selection-background-color: {accent_color};
        selection-color: #FFFFFF;
        outline: 0;
    }}

    QHeaderView::section {{
        background-color: {bg_secondary};
        color: {text_secondary};
        padding: 10px;
        border: none;
        border-bottom: 1px solid {border_color};
        font-weight: bold;
        text-align: left;
    }}

    QTableWidget::item {{
        padding: 9px 12px;
        border-bottom: 1px solid {bg_primary};
    }}

    QTableWidget::item:hover {{
        background-color: {bg_tertiary};
    }}

    QTableWidget::item:alternate {{
        background-color: {bg_primary};
    }}

    QTableWidget::item:selected {{
        background-color: {accent_color};
        color: #FFFFFF;
    }}

    /* Tree View Styling (Directory Explorer) */
    QTreeView {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 12px;
        outline: 0;
        padding: 5px;
    }}

    QTreeView::item {{
        padding: 6px;
        border-radius: 4px;
    }}

    QTreeView::item:hover {{
        background-color: {bg_tertiary};
    }}

    QTreeView::item:selected {{
        background-color: {accent_color};
        color: #FFFFFF;
    }}

    QListWidget#DuplicateList {{
        background-color: {bg_secondary};
        border: none;
        outline: 0;
    }}

    QListWidget#DuplicateList::item {{
        background-color: {bg_primary};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 8px 10px;
        margin: 3px 2px;
        color: {text_primary};
    }}

    QListWidget#DuplicateList::item:hover {{
        background-color: {bg_tertiary};
        border-color: {border_hover};
    }}

    QListWidget#DuplicateList::item:selected {{
        background-color: {accent_color};
        border-color: {accent_color};
        color: #FFFFFF;
    }}

    QListWidget#FileList, QListWidget#SettingsList {{
        background-color: {bg_secondary};
        border: none;
        outline: 0;
    }}

    QListWidget#FileList::item, QListWidget#SettingsList::item {{
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 8px 10px;
        margin: 2px 0;
        color: {text_primary};
    }}

    QListWidget#FileList::item:hover, QListWidget#SettingsList::item:hover {{
        background-color: {bg_tertiary};
        border-color: {border_color};
    }}

    QListWidget#FileList::item:selected, QListWidget#SettingsList::item:selected {{
        background-color: {accent_color};
        border-color: {accent_color};
        color: #FFFFFF;
    }}

    QMenu {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 10px;
        padding: 8px;
        color: {text_primary};
    }}

    QMenu::item {{
        padding: 8px 14px 8px 12px;
        border-radius: 7px;
        margin: 1px 0;
    }}

    QMenu::item:selected {{
        background-color: {bg_tertiary};
        color: {text_primary};
    }}

    QMenu::separator {{
        height: 1px;
        background: {border_color};
        margin: 6px 10px;
    }}

    QFrame#ToastCard {{
        background-color: {bg_secondary};
        border: 1px solid {border_color};
        border-radius: 14px;
    }}

    QFrame#ToastCard[level="success"] {{
        border-color: {success_color};
    }}

    QFrame#ToastCard[level="warning"] {{
        border-color: {warning_color};
    }}

    QFrame#ToastCard[level="error"] {{
        border-color: {error_color};
    }}

    QLabel#ToastIcon {{
        background-color: {bg_tertiary};
        border: 1px solid {border_color};
        border-radius: 15px;
        padding: 5px;
    }}

    QLabel#ToastTitle {{
        color: {text_primary};
        font-size: 13px;
        font-weight: 800;
    }}

    QLabel#ToastMessage {{
        color: {text_secondary};
        font-size: 12px;
        line-height: 1.35em;
    }}

    QPushButton#ToastCloseBtn {{
        background: transparent;
        border: none;
        color: {text_disabled};
        min-width: 24px;
        max-width: 24px;
        padding: 2px;
        font-size: 12px;
        font-weight: 700;
    }}

    QPushButton#ToastCloseBtn:hover {{
        background-color: {bg_tertiary};
        color: {text_primary};
        border-radius: 10px;
    }}

    /* ScrollBar Styling */
    QScrollBar:vertical {{
        border: none;
        background-color: {bg_primary};
        width: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {border_color};
        min-height: 20px;
        border-radius: 5px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {accent_color};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}

    QScrollBar:horizontal {{
        border: none;
        background-color: {bg_primary};
        height: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {border_color};
        min-width: 20px;
        border-radius: 5px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {accent_color};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none;
        background: none;
    }}

    QProgressBar {{
        border: 1px solid {border_color};
        border-radius: 6px;
        text-align: center;
        background: {bg_primary};
        color: {text_primary};
        height: 18px;
    }}
    QProgressBar::chunk {{
        background-color: {accent_color};
        border-radius: 5px;
    }}

    /* Dialogs / Message Boxes */
    QDialog {{
        background-color: {bg_primary};
    }}

    QMessageBox {{
        background-color: {bg_secondary};
    }}

    /* Tab Widget styling if needed */
    QTabWidget::pane {{
        border: 1px solid {border_color};
        border-radius: 8px;
        background-color: {bg_secondary};
    }}

    QTabBar::tab {{
        background-color: {bg_primary};
        color: {text_secondary};
        border: 1px solid {border_color};
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 16px;
        margin-right: 4px;
    }}

    QTabBar::tab:hover {{
        background-color: {bg_tertiary};
    }}

    QTabBar::tab:selected {{
        background-color: {bg_secondary};
        color: {text_primary};
        border-color: {border_color};
        border-bottom: 1px solid {bg_secondary};
        font-weight: bold;
    }}
    """
    return qss

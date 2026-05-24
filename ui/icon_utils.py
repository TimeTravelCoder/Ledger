from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QAbstractItemView


_FILE_ICON_CACHE = {}


_TYPE_META = {
    ".pdf": ("PDF", "#DC2626", "PDF \u6587\u6863"),
    ".doc": ("DOC", "#2563EB", "Word \u6587\u6863"),
    ".docx": ("DOC", "#2563EB", "Word \u6587\u6863"),
    ".txt": ("TXT", "#64748B", "\u6587\u672c\u6587\u4ef6"),
    ".md": ("MD", "#7C3AED", "Markdown"),
    ".png": ("IMG", "#059669", "\u56fe\u7247"),
    ".jpg": ("IMG", "#059669", "\u56fe\u7247"),
    ".jpeg": ("IMG", "#059669", "\u56fe\u7247"),
    ".gif": ("IMG", "#059669", "\u56fe\u7247"),
    ".py": ("PY", "#D97706", "Python \u4ee3\u7801"),
    ".js": ("JS", "#CA8A04", "JavaScript"),
    ".ts": ("TS", "#0284C7", "TypeScript"),
    ".xlsx": ("XLS", "#16A34A", "Excel \u8868\u683c"),
    ".xls": ("XLS", "#16A34A", "Excel \u8868\u683c"),
    ".ppt": ("PPT", "#EA580C", "\u6f14\u793a\u6587\u7a3f"),
    ".pptx": ("PPT", "#EA580C", "\u6f14\u793a\u6587\u7a3f"),
    ".csv": ("CSV", "#0F766E", "CSV \u6570\u636e"),
    ".json": ("JSON", "#4A6FA6", "JSON \u6570\u636e"),
    ".zip": ("ZIP", "#A16207", "\u538b\u7f29\u5305"),
    ".rar": ("RAR", "#A16207", "\u538b\u7f29\u5305"),
    ".7z": ("7Z", "#A16207", "\u538b\u7f29\u5305"),
}


def file_type_meta(filename):
    suffix = Path(str(filename)).suffix.lower()
    return _TYPE_META.get(
        suffix,
        ("FILE", "#4A6FA6", suffix.upper().lstrip(".") or "\u666e\u901a\u6587\u4ef6"),
    )


def file_type_icon(filename):
    label, color, _ = file_type_meta(filename)
    cache_key = (label, color)
    if cache_key in _FILE_ICON_CACHE:
        return _FILE_ICON_CACHE[cache_key]

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
    _FILE_ICON_CACHE[cache_key] = icon
    return icon


def describe_file_type(filename):
    return file_type_meta(filename)[2]


def decorate_table(table, row_height=36, icon_size=24):
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setIconSize(QSize(icon_size, icon_size))
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)


def set_button_icon(button, standard_icon, size=16):
    button.setIcon(button.style().standardIcon(standard_icon))
    button.setIconSize(QSize(size, size))

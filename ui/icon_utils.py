from pathlib import Path

from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QListWidgetItem


_FILE_ICON_CACHE = {}
_LINE_ICON_CACHE = {}
_WORKSPACE_FOLDER_ICON_CACHE = {}


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


def format_bytes(num_bytes):
    try:
        value = float(num_bytes or 0)
    except (TypeError, ValueError):
        value = 0.0
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return "0 B"


def line_icon(name, color=None, size=24):
    """Return a small linear icon drawn with one visual language."""
    if color is None:
        try:
            from config import config
            if config.theme == "dark":
                color = "#AAD9F2"
            elif config.theme == "zhongguose":
                color = "#4A6E56"
            else:
                color = "#475569"
        except Exception:
            color = "#AAD9F2"

    cache_key = (name, color, size)
    if cache_key in _LINE_ICON_CACHE:
        return _LINE_ICON_CACHE[cache_key]

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    scale = size / 24

    def x(value):
        return value * scale

    pen = QPen(QColor(color), max(1.4, 1.8 * scale), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if name == "dashboard":
        painter.drawRoundedRect(QRectF(x(4), x(4), x(7), x(7)), x(1.5), x(1.5))
        painter.drawRoundedRect(QRectF(x(13), x(4), x(7), x(4)), x(1.5), x(1.5))
        painter.drawRoundedRect(QRectF(x(13), x(10), x(7), x(10)), x(1.5), x(1.5))
        painter.drawRoundedRect(QRectF(x(4), x(13), x(7), x(7)), x(1.5), x(1.5))
    elif name == "inbox":
        painter.drawRoundedRect(QRectF(x(4), x(6), x(16), x(13)), x(2.2), x(2.2))
        painter.drawLine(x(4), x(12), x(9), x(12))
        painter.drawLine(x(15), x(12), x(20), x(12))
        painter.drawLine(x(9), x(12), x(10.5), x(15))
        painter.drawLine(x(13.5), x(15), x(15), x(12))
    elif name == "workspace":
        painter.drawRoundedRect(QRectF(x(3.5), x(7), x(17), x(12)), x(2), x(2))
        painter.drawLine(x(5), x(7), x(8), x(4.5))
        painter.drawLine(x(8), x(4.5), x(12), x(4.5))
        painter.drawLine(x(12), x(4.5), x(14), x(7))
    elif name == "backup":
        painter.drawArc(QRectF(x(5), x(5), x(14), x(14)), 35 * 16, 270 * 16)
        painter.drawLine(x(6), x(7), x(5), x(12))
        painter.drawLine(x(6), x(7), x(10.5), x(7.5))
    elif name == "settings":
        painter.drawEllipse(QRectF(x(8), x(8), x(8), x(8)))
        for sx, sy, ex, ey in [(12, 3.5, 12, 6), (12, 18, 12, 20.5), (3.5, 12, 6, 12), (18, 12, 20.5, 12), (5.5, 5.5, 7.2, 7.2), (16.8, 16.8, 18.5, 18.5), (18.5, 5.5, 16.8, 7.2), (7.2, 16.8, 5.5, 18.5)]:
            painter.drawLine(x(sx), x(sy), x(ex), x(ey))
    elif name == "search":
        painter.drawEllipse(QRectF(x(5), x(5), x(10), x(10)))
        painter.drawLine(x(13), x(13), x(19), x(19))
    elif name == "refresh":
        painter.drawArc(QRectF(x(5), x(5), x(14), x(14)), 45 * 16, 250 * 16)
        painter.drawLine(x(17.5), x(6.5), x(18.5), x(11))
        painter.drawLine(x(17.5), x(6.5), x(13.2), x(7.4))
    elif name == "file":
        painter.drawRoundedRect(QRectF(x(6), x(4), x(12), x(16)), x(1.6), x(1.6))
        painter.drawLine(x(14), x(4), x(18), x(8))
        painter.drawLine(x(14), x(4), x(14), x(8))
        painter.drawLine(x(14), x(8), x(18), x(8))
    elif name == "folder":
        painter.drawRoundedRect(QRectF(x(3.5), x(7), x(17), x(12)), x(2), x(2))
        painter.drawLine(x(5), x(7), x(8), x(5))
        painter.drawLine(x(8), x(5), x(12), x(5))
    elif name == "tag":
        painter.drawRoundedRect(QRectF(x(4), x(6), x(14), x(11)), x(2), x(2))
        painter.drawLine(x(18), x(6), x(21), x(9))
        painter.drawLine(x(18), x(17), x(21), x(14))
        painter.drawEllipse(QRectF(x(7), x(9), x(2), x(2)))
    elif name == "move":
        painter.drawLine(x(4), x(12), x(18), x(12))
        painter.drawLine(x(14), x(7.5), x(18.5), x(12))
        painter.drawLine(x(14), x(16.5), x(18.5), x(12))
        painter.drawRoundedRect(QRectF(x(3), x(5), x(8), x(14)), x(2), x(2))
    elif name == "scan":
        painter.drawRoundedRect(QRectF(x(5), x(5), x(14), x(14)), x(2), x(2))
        painter.drawLine(x(4), x(12), x(20), x(12))
        painter.drawLine(x(8), x(8), x(16), x(8))
        painter.drawLine(x(8), x(16), x(13), x(16))
    elif name == "delete":
        painter.drawLine(x(7), x(8), x(17), x(8))
        painter.drawLine(x(10), x(8), x(10), x(18))
        painter.drawLine(x(14), x(8), x(14), x(18))
        painter.drawRoundedRect(QRectF(x(8), x(8), x(8), x(11)), x(1.5), x(1.5))
        painter.drawLine(x(9), x(5), x(15), x(5))
    elif name == "open":
        painter.drawRoundedRect(QRectF(x(5), x(6), x(13), x(13)), x(2), x(2))
        painter.drawLine(x(12), x(5), x(19), x(5))
        painter.drawLine(x(19), x(5), x(19), x(12))
        painter.drawLine(x(19), x(5), x(11), x(13))
    elif name == "success":
        painter.drawEllipse(QRectF(x(4), x(4), x(16), x(16)))
        painter.drawLine(x(8), x(12.5), x(11), x(15.5))
        painter.drawLine(x(11), x(15.5), x(16.5), x(8.5))
    elif name == "warning":
        painter.drawLine(x(12), x(4), x(21), x(19))
        painter.drawLine(x(21), x(19), x(3), x(19))
        painter.drawLine(x(3), x(19), x(12), x(4))
        painter.drawLine(x(12), x(9), x(12), x(13))
        painter.drawPoint(x(12), x(16))
    elif name == "duplicate":
        painter.drawRoundedRect(QRectF(x(7), x(5), x(11), x(13)), x(2), x(2))
        painter.drawRoundedRect(QRectF(x(4), x(8), x(11), x(11)), x(2), x(2))
    elif name == "theme":
        painter.drawEllipse(QRectF(x(5), x(5), x(14), x(14)))
        painter.drawArc(QRectF(x(8), x(3), x(10), x(18)), 90 * 16, 180 * 16)
    elif name == "info":
        painter.drawEllipse(QRectF(x(4), x(4), x(16), x(16)))
        painter.drawLine(x(12), x(11), x(12), x(16))
        painter.drawPoint(x(12), x(8))
    elif name == "logo":
        # Draw a beautiful, premium, vector stacked-document logo
        painter.drawRoundedRect(QRectF(x(3.5), x(3.5), x(11), x(14)), x(1.8), x(1.8))
        painter.drawRoundedRect(QRectF(x(9.5), x(6.5), x(11), x(14)), x(1.8), x(1.8))
        # Add beautiful stylized text line indicators inside documents
        painter.drawLine(x(6), x(7.5), x(12), x(7.5))
        painter.drawLine(x(6), x(11.5), x(10), x(11.5))
        painter.drawLine(x(12), x(10.5), x(18), x(10.5))
        painter.drawLine(x(12), x(14.5), x(16), x(14.5))
    else:
        painter.drawRoundedRect(QRectF(x(5), x(5), x(14), x(14)), x(3), x(3))

    painter.end()
    icon = QIcon(pixmap)
    _LINE_ICON_CACHE[cache_key] = icon
    return icon


def workspace_folder_icon(color="#4A6FA6", warning=False, size=20):
    cache_key = (color, warning, size)
    if cache_key in _WORKSPACE_FOLDER_ICON_CACHE:
        return _WORKSPACE_FOLDER_ICON_CACHE[cache_key]

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    scale = size / 20

    def x(value):
        return value * scale

    base_color = QColor(color)
    fill_color = QColor(color)
    fill_color.setAlpha(70)
    painter.setPen(QPen(base_color, max(1.2, 1.6 * scale), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(fill_color)
    painter.drawRoundedRect(QRectF(x(2), x(6), x(16), x(11)), x(2.4), x(2.4))
    painter.drawRoundedRect(QRectF(x(3), x(4), x(7), x(4.8)), x(1.8), x(1.8))

    accent = QColor(color)
    accent.setAlpha(120)
    painter.fillRect(QRectF(x(4), x(9), x(12), x(1.8)), accent)

    if warning:
        warning_color = QColor("#F59E0B")
        painter.setPen(Qt.NoPen)
        painter.setBrush(warning_color)
        painter.drawEllipse(QRectF(x(12.3), x(11.2), x(5), x(5)))
        painter.setPen(QPen(QColor("#FFFFFF"), max(1.0, 1.2 * scale), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(x(14.8), x(12.7), x(14.8), x(14.8))
        painter.drawPoint(x(14.8), x(16))

    painter.end()
    icon = QIcon(pixmap)
    _WORKSPACE_FOLDER_ICON_CACHE[cache_key] = icon
    return icon


def make_empty_item(title, subtitle="", icon_name="info"):
    text = title if not subtitle else f"{title}\n{subtitle}"
    item = QListWidgetItem(line_icon(icon_name, "#85B3CB", 24), text)
    item.setFlags(Qt.ItemIsEnabled)
    item.setSizeHint(QSize(0, 78))
    return item

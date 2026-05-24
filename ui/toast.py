from PySide6.QtCore import QEasingCurve, QObject, QEvent, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ui.icon_utils import line_icon


_LEVEL_META = {
    "info": {"icon": "info", "color": "#4A6FA6", "fallback": QMessageBox.Information},
    "success": {"icon": "success", "color": "#059669", "fallback": QMessageBox.Information},
    "warning": {"icon": "warning", "color": "#D97706", "fallback": QMessageBox.Warning},
    "error": {"icon": "warning", "color": "#DC2626", "fallback": QMessageBox.Critical},
}


class ToastCard(QFrame):
    closed = Signal(object)

    def __init__(self, message, title="", level="info", duration=3200, parent=None):
        super().__init__(parent)
        self.level = level if level in _LEVEL_META else "info"
        self.duration = max(1200, int(duration))
        self._closing = False

        self.setObjectName("ToastCard")
        self.setProperty("level", self.level)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(328)

        opacity = QGraphicsOpacityEffect(self)
        opacity.setOpacity(0.0)
        self.setGraphicsEffect(opacity)
        self.opacity_effect = opacity

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_anim.setDuration(180)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_anim.finished.connect(self._on_animation_finished)

        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.close_animated)

        self._build_ui(message=message, title=title)

    def _build_ui(self, message, title):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 10, 10)
        layout.setSpacing(10)

        icon_meta = _LEVEL_META[self.level]
        self.icon_label = QLabel()
        self.icon_label.setObjectName("ToastIcon")
        self.icon_label.setFixedSize(30, 30)
        self.icon_label.setPixmap(line_icon(icon_meta["icon"], icon_meta["color"], 18).pixmap(18, 18))
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label, 0, Qt.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        if title:
            title_label = QLabel(title)
            title_label.setObjectName("ToastTitle")
            title_label.setWordWrap(True)
            text_layout.addWidget(title_label)

        message_label = QLabel(message)
        message_label.setObjectName("ToastMessage")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_layout.addWidget(message_label)
        layout.addLayout(text_layout, 1)

        close_btn = QPushButton("x")
        close_btn.setObjectName("ToastCloseBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close_animated)
        layout.addWidget(close_btn, 0, Qt.AlignTop)

    def show_animated(self):
        self.show()
        self.raise_()
        self.fade_anim.stop()
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        self.close_timer.start(self.duration)

    def close_animated(self):
        if self._closing:
            return
        self._closing = True
        self.close_timer.stop()
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def _on_animation_finished(self):
        if self._closing:
            self.closed.emit(self)
            self.deleteLater()


class ToastManager(QObject):
    def __init__(self, host):
        super().__init__(host)
        self.host = host
        self.toasts = []
        host.installEventFilter(self)

    def show_toast(self, message, title="", level="info", duration=3200):
        toast = ToastCard(message=message, title=title, level=level, duration=duration, parent=self.host)
        toast.closed.connect(self._remove_toast)
        self.toasts.append(toast)
        self._reposition_toasts()
        toast.show_animated()
        return toast

    def _remove_toast(self, toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
            self._reposition_toasts()

    def _reposition_toasts(self):
        if not self.toasts:
            return
        right_margin = 18
        bottom_margin = 18
        spacing = 10
        y = self.host.height() - bottom_margin
        for toast in reversed(self.toasts):
            toast.adjustSize()
            x = max(12, self.host.width() - toast.width() - right_margin)
            y -= toast.height()
            toast.move(x, max(12, y))
            y -= spacing

    def eventFilter(self, watched, event):
        if watched is self.host and event.type() in {QEvent.Resize, QEvent.Show, QEvent.WindowStateChange}:
            self._reposition_toasts()
        return super().eventFilter(watched, event)


def show_toast(parent, message, title="", level="info", duration=3200):
    window = parent.window() if parent else None
    if window and hasattr(window, "show_toast"):
        window.show_toast(message=message, title=title, level=level, duration=duration)
        return True

    icon = _LEVEL_META.get(level, _LEVEL_META["info"])["fallback"]
    QMessageBox(icon, title or "提示", message, parent=parent).exec()
    return False

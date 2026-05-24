from PySide6.QtCore import QObject, QEvent, QPropertyAnimation, QEasingCurve, QPoint, Slot
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget
from PySide6.QtGui import QColor

class HoverPhysicsFilter(QObject):
    """
    Event filter that applies a highly responsive physical hover animation
    on PySide6 widgets by smoothly morphing its drop shadow offset, blur radius,
    and injecting a harmonic accent glow.
    """
    def __init__(self, parent=None, glow_color="#6366F1", lift_distance=4, shadow_blur=18):
        super().__init__(parent)
        self.glow_color = QColor(glow_color)
        self.lift_distance = lift_distance
        self.shadow_blur = shadow_blur
        self.animations = {}

    def eventFilter(self, obj, event):
        if not obj.isWidgetType():
            return super().eventFilter(obj, event)

        if event.type() == QEvent.Enter:
            self.apply_hover_effect(obj)
        elif event.type() == QEvent.Leave:
            self.remove_hover_effect(obj)

        return super().eventFilter(obj, event)

    def apply_hover_effect(self, widget: QWidget):
        from config import config
        theme = getattr(config, "theme", "dark")
        if theme == "dark":
            self.glow_color = QColor("#6366F1")
        elif theme == "zhongguose":
            self.glow_color = QColor("#047857")
        else:
            self.glow_color = QColor("#4F46E5")

        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsDropShadowEffect):
            effect = QGraphicsDropShadowEffect(widget)
            effect.setOffset(0, 1)
            effect.setBlurRadius(6)
            effect.setColor(QColor(0, 0, 0, 30))
            widget.setGraphicsEffect(effect)

        anim_id = id(widget)

        # Animate blurRadius
        anim_blur = QPropertyAnimation(effect, b"blurRadius")
        anim_blur.setDuration(220)
        anim_blur.setStartValue(effect.blurRadius())
        anim_blur.setEndValue(self.shadow_blur)
        anim_blur.setEasingCurve(QEasingCurve.OutCubic)

        # Animate offset
        anim_offset = QPropertyAnimation(effect, b"offset")
        anim_offset.setDuration(220)
        anim_offset.setStartValue(effect.offset())
        anim_offset.setEndValue(QPoint(0, self.lift_distance))
        anim_offset.setEasingCurve(QEasingCurve.OutCubic)

        # Animate color glow fade-in
        anim_color = QPropertyAnimation(effect, b"color")
        anim_color.setDuration(220)
        anim_color.setStartValue(effect.color())

        glow_translucent = QColor(self.glow_color)
        glow_translucent.setAlpha(70) # Beautiful semi-translucent neon aura
        anim_color.setEndValue(glow_translucent)
        anim_color.setEasingCurve(QEasingCurve.OutCubic)

        # Stop any ongoing animation for this widget to prevent stuttering
        if anim_id in self.animations:
            for anim in self.animations[anim_id]:
                anim.stop()

        anim_blur.start()
        anim_offset.start()
        anim_color.start()

        self.animations[anim_id] = [anim_blur, anim_offset, anim_color]

    def remove_hover_effect(self, widget: QWidget):
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsDropShadowEffect):
            return

        anim_id = id(widget)

        anim_blur = QPropertyAnimation(effect, b"blurRadius")
        anim_blur.setDuration(180)
        anim_blur.setStartValue(effect.blurRadius())
        anim_blur.setEndValue(6)
        anim_blur.setEasingCurve(QEasingCurve.OutQuad)

        anim_offset = QPropertyAnimation(effect, b"offset")
        anim_offset.setDuration(180)
        anim_offset.setStartValue(effect.offset())
        anim_offset.setEndValue(QPoint(0, 1))
        anim_offset.setEasingCurve(QEasingCurve.OutQuad)

        anim_color = QPropertyAnimation(effect, b"color")
        anim_color.setDuration(180)
        anim_color.setStartValue(effect.color())
        anim_color.setEndValue(QColor(0, 0, 0, 30))
        anim_color.setEasingCurve(QEasingCurve.OutQuad)

        if anim_id in self.animations:
            for anim in self.animations[anim_id]:
                anim.stop()

        anim_blur.start()
        anim_offset.start()
        anim_color.start()

        self.animations[anim_id] = [anim_blur, anim_offset, anim_color]

def apply_hover_physics(widgets, glow_color="#6366F1", lift_distance=4, shadow_blur=18):
    """
    Utility function to bind physical hover animations onto list of widgets.
    """
    if not widgets:
        return None
    filter_obj = HoverPhysicsFilter(widgets[0].window(), glow_color, lift_distance, shadow_blur)
    for w in widgets:
        w.installEventFilter(filter_obj)
        if not hasattr(w, "_hover_filters"):
            w._hover_filters = []
        w._hover_filters.append(filter_obj)
    return filter_obj

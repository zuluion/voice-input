import math
from PySide6.QtCore import Qt, QRectF, QPointF, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect, QApplication

class FloatingCapsule(QWidget):
    STATE_PREPARING = "PREPARING"
    STATE_LISTENING = "LISTENING"
    STATE_REFINING = "REFINING"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.current_state = self.STATE_PREPARING
        self.raw_bar_levels = [0.1, 0.1, 0.1, 0.1, 0.1]
        self.bar_heights = [0.1, 0.1, 0.1, 0.1, 0.1]
        self.status_text = "Preparing..."
        self.capsule_width = 190
        self.capsule_height = 56
        self.position = "bottom_center"

        self.pulse_phase = 0.0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.setInterval(33)  # 30 FPS for smooth pulsing & breathing
        self.pulse_timer.timeout.connect(self._on_pulse_tick)

        self.resize(self.capsule_width, self.capsule_height)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self._fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._fade_anim.setDuration(220)
        self._fade_anim.finished.connect(self._on_fade_finished)

    def set_position(self, position_str: str) -> None:
        self.position = position_str or "bottom_center"
        self.reposition()

    def reposition(self) -> None:
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geom = screen.availableGeometry()

        if self.position == "top_center":
            x = geom.x() + (geom.width() - self.capsule_width) // 2
            y = geom.y() + 60
        elif self.position == "center":
            x = geom.x() + (geom.width() - self.capsule_width) // 2
            y = geom.y() + (geom.height() - self.capsule_height) // 2
        else:  # bottom_center
            x = geom.x() + (geom.width() - self.capsule_width) // 2
            y = geom.y() + geom.height() - self.capsule_height - 60

        self.move(x, y)

    def _on_fade_finished(self) -> None:
        if self.opacity_effect.opacity() == 0.0:
            self.hide()

    def set_state(self, state: str) -> None:
        self.current_state = state
        if state == self.STATE_PREPARING:
            self.status_text = "Preparing..."
            self.pulse_timer.start()
        elif state == self.STATE_LISTENING:
            self.status_text = "Listening..."
            self.pulse_timer.start()
        elif state == self.STATE_REFINING:
            self.status_text = "Refining..."
            self.pulse_timer.start()
        self.update_width()
        self.update()

    def set_volume_levels(self, levels: list) -> None:
        if self.current_state == self.STATE_LISTENING and len(levels) == 5:
            self.raw_bar_levels = levels
            self.update()

    def set_status_text(self, text: str) -> None:
        self.status_text = text if text else "Listening..."
        self.update_width()
        self.update()

    def update_width(self) -> None:
        font_metrics = self.fontMetrics()
        text_w = font_metrics.horizontalAdvance(self.status_text)
        target_w = max(190, min(560, text_w + 105))
        if target_w != self.capsule_width:
            self.capsule_width = target_w
            self.resize(self.capsule_width, self.capsule_height)
            self.reposition()

    def _on_pulse_tick(self) -> None:
        self.pulse_phase += 0.15
        if self.current_state == self.STATE_PREPARING:
            for i in range(5):
                val = 0.2 + 0.6 * (0.5 + 0.5 * math.sin(self.pulse_phase - i * 0.6))
                self.bar_heights[i] = val
        elif self.current_state == self.STATE_LISTENING:
            for i in range(5):
                raw = self.raw_bar_levels[i]
                idle_wave = 0.15 + 0.1 * math.sin(self.pulse_phase - i * 0.5)
                self.bar_heights[i] = max(idle_wave, raw)
        elif self.current_state == self.STATE_REFINING:
            for i in range(5):
                val = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(self.pulse_phase * 0.8 - i * 0.4))
                self.bar_heights[i] = val
        self.update()

    def show_capsule(self) -> None:
        print(f"[Capsule UI] Showing floating capsule at '{self.position}' (State: {self.current_state})")
        self.reposition()
        self.show()
        self.raise_()

        self._fade_anim.stop()
        self._fade_anim.setStartValue(self.opacity_effect.opacity())
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.start()

    def hide_capsule(self) -> None:
        print(f"[Capsule UI] Hiding floating capsule")
        self.pulse_timer.stop()
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self.opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.InCubic)
        self._fade_anim.start()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Background Rounded Rectangle
        bg_rect = QRectF(2, 2, self.capsule_width - 4, self.capsule_height - 4)
        bg_color = QColor(20, 24, 33, 235)
        border_color = QColor(255, 255, 255, 30)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.5))
        painter.drawRoundedRect(bg_rect, 26, 26)

        # 2. Left Status Element (Red REC Dot with Breathing Glow when LISTENING)
        dot_x = 22.0
        dot_y = self.capsule_height / 2.0
        dot_radius = 4.5

        if self.current_state == self.STATE_PREPARING:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(245, 158, 11)))
            painter.drawEllipse(QPointF(dot_x, dot_y), dot_radius, dot_radius)
        elif self.current_state == self.STATE_LISTENING:
            glow_expand = 2.0 + 2.0 * (0.5 + 0.5 * math.sin(self.pulse_phase * 1.5))
            glow_alpha = int(70 + 50 * (0.5 + 0.5 * math.sin(self.pulse_phase * 1.5)))
            glow_color = QColor(239, 68, 68, glow_alpha)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QPointF(dot_x, dot_y), dot_radius + glow_expand, dot_radius + glow_expand)

            painter.setBrush(QBrush(QColor(239, 68, 68)))
            painter.drawEllipse(QPointF(dot_x, dot_y), dot_radius, dot_radius)
        elif self.current_state == self.STATE_REFINING:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(168, 85, 247)))
            painter.drawEllipse(QPointF(dot_x, dot_y), dot_radius, dot_radius)

        # 3. Draw 5 Waveform Bars
        bar_area_x = 36.0
        bar_w = 4.0
        bar_gap = 5.0
        max_h = 24.0
        center_y = self.capsule_height / 2.0

        if self.current_state == self.STATE_PREPARING:
            bar_color = QColor(245, 158, 11)  # Amber
        elif self.current_state == self.STATE_REFINING:
            bar_color = QColor(168, 85, 247)  # Purple
        else:
            bar_color = QColor(99, 102, 241)   # Indigo

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bar_color))

        for i, h_ratio in enumerate(self.bar_heights):
            h = max(6.0, h_ratio * max_h)
            bx = bar_area_x + i * (bar_w + bar_gap)
            by = center_y - h / 2.0
            painter.drawRoundedRect(QRectF(bx, by, bar_w, h), 2.0, 2.0)

        # 4. Draw Text
        text_x = bar_area_x + 5 * (bar_w + bar_gap) + 12
        text_rect = QRectF(text_x, 0, self.capsule_width - text_x - 16, self.capsule_height)

        if self.current_state == self.STATE_PREPARING:
            text_color = QColor(251, 191, 36) # Amber text
        else:
            text_color = QColor(243, 244, 246) # White text

        painter.setPen(text_color)
        font = QFont("Segoe UI", 11, QFont.Medium)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.status_text)

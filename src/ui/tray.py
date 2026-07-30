import os
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QWidget
from src.i18n import i18n
from src.utils.version import get_logo_path

def create_default_icon() -> QIcon:
    logo_path = get_logo_path()
    if logo_path and os.path.exists(logo_path):
        icon = QIcon(logo_path)
        if not icon.isNull():
            return icon

    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(99, 102, 241))
    painter.setPen(QColor(255, 255, 255))
    painter.drawEllipse(2, 2, 28, 28)
    painter.setBrush(QColor(255, 255, 255))
    painter.drawEllipse(12, 10, 8, 12)
    painter.end()
    return QIcon(pixmap)

class SystemTrayApp(QObject):
    open_settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(create_default_icon(), parent)
        self.tray_icon.setToolTip(i18n.t("app_title"))

        self.menu = QMenu(parent)

        self.enable_action = self.menu.addAction(i18n.t("tray_enabled"))
        self.enable_action.setCheckable(True)
        self.enable_action.setChecked(True)

        self.menu.addSeparator()

        self.settings_action = self.menu.addAction(i18n.t("tray_settings"))
        self.settings_action.triggered.connect(self.open_settings_requested.emit)

        self.menu.addSeparator()

        self.quit_action = self.menu.addAction(i18n.t("tray_quit"))
        self.quit_action.triggered.connect(self.quit_requested.emit)

        self.tray_icon.setContextMenu(self.menu)

    def show(self) -> None:
        self.tray_icon.show()

    def is_enabled(self) -> bool:
        return self.enable_action.isChecked()

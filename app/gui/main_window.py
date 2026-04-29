"""Main application window."""

from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QMainWindow
from app.controller.main_controller import MainController
from app.gui.ui_main_window import Ui_MainWindow
from app.utils.resources import resource_string


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._apply_icons()
        self.controller = MainController(self)

    def _apply_icons(self):
        icon_map = {
            self.playButton: "app/assets/icons/play-btn.svg",
            self.stopButton: "app/assets/icons/stop.svg",
            self.openSettingsButton: "app/assets/icons/sliders.svg",
            self.openSecondWindowButton: "app/assets/icons/toolbar.svg",
        }
        for widget, icon_path in icon_map.items():
            widget.setIcon(QIcon(resource_string(icon_path)))

        self.actionSettings.setIcon(
            QIcon(resource_string("app/assets/icons/sliders.svg"))
        )
        self.actionOpenScraper.setIcon(
            QIcon(resource_string("app/assets/icons/toolbar.svg"))
        )
        self.actionExportAudio.setIcon(
            QIcon(resource_string("app/assets/icons/play-btn.svg"))
        )

    def closeEvent(self, event: QCloseEvent):
        self.controller.shutdown()
        super().closeEvent(event)

"""main_window.py
_summary_

_extended_summary_
"""

from PyQt6.QtWidgets import QMainWindow
from app.controller.main_controller import MainController
from app.gui.ui_main_window import Ui_MainWindow


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.second_window = None
        self.controller = MainController(self)

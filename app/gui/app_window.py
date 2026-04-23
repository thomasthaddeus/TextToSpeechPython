"""app_window.py
_summary_

_extended_summary_
"""

from PyQt6.QtWidgets import QMainWindow
from app.controller.compute_controller import ComputeController
from app.gui.ui_compute_window import Ui_MainWindow


class ComputeAppWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.controller = ComputeController(self)

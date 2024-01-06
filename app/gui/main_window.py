"""main_window.py
_summary_

_extended_summary_
"""

from PyQt6.QtWidgets import QMainWindow
import main_window
from second_window import SecondApp
from controller.main_controller import MainController

class MainApp(QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.openSecondWindowButton.clicked.connect(self.open_second_window)
        self.second_window = None
        self.controller = MainController(self)

    def open_second_window(self):
        if not self.second_window or not self.second_window.isVisible():
            self.second_window = SecondApp(self)
            self.second_window.show()

# QApplication should be in main.py

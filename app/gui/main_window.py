from PyQt6.QtWidgets import QMainWindow
import main_window
from second_window import SecondApp

class MainApp(QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.openSecondWindowButton.clicked.connect(self.open_second_window)
        self.second_window = None

    def open_second_window(self):
        if not self.second_window or not self.second_window.isVisible():
            self.second_window = SecondApp(self)
            self.second_window.show()

# QApplication should be in main.py

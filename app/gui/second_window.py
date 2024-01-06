from PyQt6.QtWidgets import QDialog
import second_window

class SecondApp(QDialog, second_window.Ui_Dialog):
    def __init__(self, parent=None):
        super(SecondApp, self).__init__(parent)
        self.setupUi(self)

# No QApplication here; should be in main.py

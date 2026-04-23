from PyQt6.QtWidgets import QDialog
from app.gui.ui_second_window import Ui_Dialog


class SecondApp(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(SecondApp, self).__init__(parent)
        self.setupUi(self)

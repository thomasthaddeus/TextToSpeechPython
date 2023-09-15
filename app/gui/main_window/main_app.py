"""
_summary_

_extended_summary_
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog
import main_window
import second_window

class MainApp(QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.openSecondWindowButton.clicked.connect(self.open_second_window)

    def open_second_window(self):
        self.second_window = SecondApp(self)
        self.second_window.show()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainApp()
    main_win.show()
    sys.exit(app.exec_())

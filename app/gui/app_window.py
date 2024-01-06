import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
import design
import mylib

class ComputeAppWindow(QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.computeButton.clicked.connect(self.on_compute)

    def on_compute(self):
        try:
            x = float(self.inputField.text())
            result = mylib.compute(x)
            self.resultLabel.setText(str(result))
        except ValueError:
            self.resultLabel.setText("Invalid input")

# The QApplication creation and execution should be moved to main.py

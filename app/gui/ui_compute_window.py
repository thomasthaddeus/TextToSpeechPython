"""Qt widgets for the compute demo window."""

from PyQt6.QtWidgets import (
    QLineEdit,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Ui_MainWindow:
    """
    Minimal in-repo UI definition for the compute demo window.
    """

    def setupUi(self, main_window):
        main_window.setWindowTitle("Compute Demo")
        central_widget = QWidget(main_window)
        layout = QVBoxLayout(central_widget)

        self.inputField = QLineEdit(central_widget)
        self.inputField.setPlaceholderText("Enter a number")
        layout.addWidget(self.inputField)

        self.computeButton = QPushButton("Compute", central_widget)
        layout.addWidget(self.computeButton)

        self.resultLabel = QLabel("", central_widget)
        layout.addWidget(self.resultLabel)

        main_window.setCentralWidget(central_widget)

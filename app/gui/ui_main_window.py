"""Qt widgets for the main application window."""

from PyQt6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Ui_MainWindow:
    """
    Minimal in-repo UI definition for the main window.
    """

    def setupUi(self, main_window):
        main_window.setWindowTitle("Text To Speech")
        central_widget = QWidget(main_window)
        layout = QVBoxLayout(central_widget)

        self.openSecondWindowButton = QPushButton(
            "Open Secondary Window",
            central_widget,
        )
        layout.addWidget(self.openSecondWindowButton)

        main_window.setCentralWidget(central_widget)

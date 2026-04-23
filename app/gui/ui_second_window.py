"""Qt widgets for the secondary dialog."""

from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
)


class Ui_Dialog:
    """
    Minimal in-repo UI definition for the secondary dialog.
    """

    def setupUi(self, dialog):
        dialog.setWindowTitle("Secondary Window")
        layout = QVBoxLayout(dialog)
        self.infoLabel = QLabel(
            "Secondary window is ready for additional features.",
            dialog,
        )
        layout.addWidget(self.infoLabel)

"""Qt widgets for the PPTX import dialog."""

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class Ui_Dialog:
    """
    UI definition for the PPTX import dialog.
    """

    def setupUi(self, dialog):
        dialog.setWindowTitle("Import PowerPoint Notes")
        layout = QVBoxLayout(dialog)
        self.infoLabel = QLabel(
            "Choose a PowerPoint file and preview extracted slides and notes.",
            dialog,
        )
        layout.addWidget(self.infoLabel)

        path_row = QHBoxLayout()
        self.filePathEdit = QLineEdit(dialog)
        self.filePathEdit.setPlaceholderText("Path to .pptx file")
        self.browseButton = QPushButton("Browse", dialog)
        self.loadButton = QPushButton("Load", dialog)
        path_row.addWidget(self.filePathEdit)
        path_row.addWidget(self.browseButton)
        path_row.addWidget(self.loadButton)
        layout.addLayout(path_row)

        self.previewLabel = QLabel("Preview", dialog)
        layout.addWidget(self.previewLabel)

        self.previewTextEdit = QTextEdit(dialog)
        self.previewTextEdit.setReadOnly(True)
        layout.addWidget(self.previewTextEdit)

        action_row = QHBoxLayout()
        self.importButton = QPushButton("Import Into Main Editor", dialog)
        self.closeButton = QPushButton("Close", dialog)
        action_row.addWidget(self.importButton)
        action_row.addWidget(self.closeButton)
        layout.addLayout(action_row)

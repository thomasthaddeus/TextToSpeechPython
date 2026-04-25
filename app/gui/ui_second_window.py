"""Qt widgets for the document import dialog."""
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)


class Ui_Dialog:
    """
    UI definition for the document import dialog.
    """

    def setupUi(self, dialog):
        dialog.setWindowTitle("Import Document")
        layout = QVBoxLayout(dialog)
        self.infoLabel = QLabel(
            "Choose a supported document file and preview extracted sections.",
            dialog,
        )
        layout.addWidget(self.infoLabel)

        path_row = QHBoxLayout()
        self.filePathEdit = QLineEdit(dialog)
        self.filePathEdit.setPlaceholderText(
            "Path to .txt, .docx, .pdf, .html, .rtf, .epub, .xlsx, .csv, or .pptx file"
        )
        self.browseButton = QPushButton("Browse", dialog)
        self.loadButton = QPushButton("Load", dialog)
        path_row.addWidget(self.filePathEdit)
        path_row.addWidget(self.browseButton)
        path_row.addWidget(self.loadButton)
        layout.addLayout(path_row)

        self.previewLabel = QLabel("Preview", dialog)
        layout.addWidget(self.previewLabel)

        mode_row = QHBoxLayout()
        self.selectionHelpLabel = QLabel(
            "Select document rows and choose what to import or batch export:",
            dialog,
        )
        self.contentModeComboBox = QComboBox(dialog)
        self.contentModeComboBox.addItems(
            [
                "Prefer Secondary Text",
                "Secondary Text Only",
                "Primary Text Only",
                "Combine Primary and Secondary Text",
            ]
        )
        mode_row.addWidget(self.selectionHelpLabel)
        mode_row.addWidget(self.contentModeComboBox)
        layout.addLayout(mode_row)

        selection_row = QHBoxLayout()
        self.selectAllButton = QPushButton("Select All", dialog)
        self.clearSelectionButton = QPushButton("Clear Selection", dialog)
        selection_row.addWidget(self.selectAllButton)
        selection_row.addWidget(self.clearSelectionButton)
        selection_row.addStretch(1)
        layout.addLayout(selection_row)

        self.previewTable = QTableWidget(0, 3, dialog)
        self.previewTable.setHorizontalHeaderLabels(
            ["Item", "Primary Text", "Secondary Text"]
        )
        self.previewTable.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.previewTable.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.previewTable.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.previewTable.verticalHeader().setVisible(False)
        self.previewTable.horizontalHeader().setStretchLastSection(True)
        self.previewTable.setAlternatingRowColors(True)
        layout.addWidget(self.previewTable)

        action_row = QHBoxLayout()
        self.importButton = QPushButton("Import Selected", dialog)
        self.batchExportButton = QPushButton("Batch Export Selected", dialog)
        self.closeButton = QPushButton("Close", dialog)
        action_row.addWidget(self.importButton)
        action_row.addWidget(self.batchExportButton)
        action_row.addWidget(self.closeButton)
        layout.addLayout(action_row)

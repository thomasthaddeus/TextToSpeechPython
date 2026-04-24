"""Qt widgets for the PPTX import dialog."""
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

        mode_row = QHBoxLayout()
        self.selectionHelpLabel = QLabel(
            "Select slide rows and choose what to import or batch export:",
            dialog,
        )
        self.contentModeComboBox = QComboBox(dialog)
        self.contentModeComboBox.addItems(
            [
                "Prefer Notes",
                "Notes Only",
                "Slide Text Only",
                "Combine Slide Text and Notes",
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
            ["Slide", "Slide Text", "Notes"]
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

"""Qt widgets for the main application window."""

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt


class Ui_MainWindow:
    """
    Richer in-repo UI definition inspired by the donor project.
    """

    def setupUi(self, main_window):
        main_window.setWindowTitle("Text To Speech")
        central_widget = QWidget(main_window)
        root_layout = QVBoxLayout(central_widget)

        self.editorSplitter = QSplitter(Qt.Orientation.Horizontal, central_widget)
        self.textEdit = QTextEdit(self.editorSplitter)
        self.textEdit.setPlaceholderText(
            "Type or paste text here, or import PowerPoint notes from the scraper."
        )
        self.ssmlPreview = QTextEdit(self.editorSplitter)
        self.ssmlPreview.setReadOnly(True)
        self.ssmlPreview.setPlaceholderText("Generated SSML preview appears here.")
        self.editorSplitter.addWidget(self.textEdit)
        self.editorSplitter.addWidget(self.ssmlPreview)
        self.editorSplitter.setSizes([700, 500])
        root_layout.addWidget(self.editorSplitter)

        controls_layout = QGridLayout()

        self.audioControlsGroup = QGroupBox("Actions", central_widget)
        action_row = QHBoxLayout(self.audioControlsGroup)
        self.previewButton = QPushButton("Preview SSML", self.audioControlsGroup)
        self.cleanTextButton = QPushButton("Clean Text", self.audioControlsGroup)
        self.playButton = QPushButton("Generate && Play", self.audioControlsGroup)
        self.generateButton = QPushButton("Generate File", self.audioControlsGroup)
        self.stopButton = QPushButton("Stop", self.audioControlsGroup)
        self.openSecondWindowButton = QPushButton(
            "Import PPTX",
            self.audioControlsGroup,
        )
        self.openSettingsButton = QPushButton(
            "Settings",
            self.audioControlsGroup,
        )
        for button in (
            self.previewButton,
            self.cleanTextButton,
            self.playButton,
            self.generateButton,
            self.stopButton,
            self.openSecondWindowButton,
            self.openSettingsButton,
        ):
            action_row.addWidget(button)
        controls_layout.addWidget(self.audioControlsGroup, 0, 0, 1, 2)

        self.statusGroup = QGroupBox("Current Output", central_widget)
        status_layout = QHBoxLayout(self.statusGroup)
        self.voiceSummaryLabel = QLabel("Voice: en-US-GuyNeural", self.statusGroup)
        self.rateSummaryLabel = QLabel("Rate: medium", self.statusGroup)
        self.volumeSummaryLabel = QLabel("Speech Volume: medium", self.statusGroup)
        self.outputSummaryLabel = QLabel("Output: data/dynamic/audio", self.statusGroup)
        for label in (
            self.voiceSummaryLabel,
            self.rateSummaryLabel,
            self.volumeSummaryLabel,
            self.outputSummaryLabel,
        ):
            status_layout.addWidget(label)
        controls_layout.addWidget(self.statusGroup, 1, 0, 1, 2)

        self.playbackGroup = QGroupBox("Playback Volume", central_widget)
        playback_layout = QHBoxLayout(self.playbackGroup)
        self.playbackVolumeSlider = QSlider(Qt.Orientation.Horizontal, self.playbackGroup)
        self.playbackVolumeSlider.setRange(0, 100)
        self.playbackVolumeSlider.setValue(80)
        self.playbackVolumeValueLabel = QLabel("80%", self.playbackGroup)
        playback_layout.addWidget(self.playbackVolumeSlider)
        playback_layout.addWidget(self.playbackVolumeValueLabel)
        controls_layout.addWidget(self.playbackGroup, 2, 0, 1, 2)

        self.historyGroup = QGroupBox("Recent Audio", central_widget)
        history_layout = QVBoxLayout(self.historyGroup)
        self.historyList = QListWidget(self.historyGroup)
        self.historyList.setAlternatingRowColors(True)
        self.historyList.setSelectionMode(
            QListWidget.SelectionMode.NoSelection
        )
        history_layout.addWidget(self.historyList)
        controls_layout.addWidget(self.historyGroup, 3, 0, 1, 2)

        root_layout.addLayout(controls_layout)

        main_window.setCentralWidget(central_widget)

        self.menubar = QMenuBar(main_window)
        self.menuFile = QMenu("File", self.menubar)
        self.menuTools = QMenu("Tools", self.menubar)
        self.menuHelp = QMenu("Help", self.menubar)
        self.actionOpenText = QAction("Open Text File", main_window)
        self.actionSaveText = QAction("Save Text File", main_window)
        self.actionExportAudio = QAction("Export Audio", main_window)
        self.actionExit = QAction("Exit", main_window)
        self.actionSettings = QAction("Settings", main_window)
        self.actionOpenScraper = QAction("Import PPTX", main_window)
        self.actionAbout = QAction("About", main_window)

        self.menuFile.addAction(self.actionOpenText)
        self.menuFile.addAction(self.actionSaveText)
        self.menuFile.addAction(self.actionExportAudio)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuTools.addAction(self.actionSettings)
        self.menuTools.addAction(self.actionOpenScraper)
        self.menuHelp.addAction(self.actionAbout)

        self.menubar.addMenu(self.menuFile)
        self.menubar.addMenu(self.menuTools)
        self.menubar.addMenu(self.menuHelp)
        main_window.setMenuBar(self.menubar)

        self.statusbar = QStatusBar(main_window)
        main_window.setStatusBar(self.statusbar)

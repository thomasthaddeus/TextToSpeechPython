"""Qt widgets for the main application window."""

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QGroupBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QListWidget,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
from app.gui.settings_dialog import SettingsEditor
from app.model.app_settings import AppSettings
from app.model.ssml.ssml_config import SSMLConfig


class Ui_MainWindow:
    """
    Richer in-repo UI definition inspired by the donor project.
    """

    def setupUi(self, main_window):
        main_window.setWindowTitle("Text To Speech")
        central_widget = QWidget(main_window)
        outer_layout = QHBoxLayout(central_widget)
        main_panel = QWidget(central_widget)
        root_layout = QVBoxLayout(main_panel)
        outer_layout.addWidget(main_panel, 1)

        self.audioControlsGroup = QGroupBox("Actions", central_widget)
        action_row = QHBoxLayout(self.audioControlsGroup)
        self.previewButton = QPushButton("Preview SSML", self.audioControlsGroup)
        self.cleanTextButton = QPushButton("Clean Text", self.audioControlsGroup)
        self.playButton = QPushButton("Generate && Play", self.audioControlsGroup)
        self.generateButton = QPushButton("Generate File", self.audioControlsGroup)
        self.stopButton = QPushButton("Stop", self.audioControlsGroup)
        self.cancelTaskButton = QPushButton("Cancel Task", self.audioControlsGroup)
        self.cancelTaskButton.setEnabled(False)
        self.openSecondWindowButton = QPushButton(
            "Import Document",
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
            self.cancelTaskButton,
            self.openSecondWindowButton,
            self.openSettingsButton,
        ):
            action_row.addWidget(button)

        self.playbackVolumeSlider = QSlider(
            Qt.Orientation.Horizontal,
            self.audioControlsGroup,
        )
        self.playbackVolumeSlider.setRange(0, 100)
        self.playbackVolumeSlider.setValue(80)
        self.playbackVolumeSlider.setToolTip("Playback Volume")
        self.playbackVolumeValueLabel = QLabel("80%", self.audioControlsGroup)
        action_row.addStretch(1)
        action_row.addWidget(self.playbackVolumeSlider)
        action_row.addWidget(self.playbackVolumeValueLabel)

        root_layout.addWidget(self.audioControlsGroup)

        self.narrationControlsGroup = QGroupBox("Narration Section", central_widget)
        narration_row = QHBoxLayout(self.narrationControlsGroup)
        self.narrationSpeakerEdit = QLineEdit(self.narrationControlsGroup)
        self.narrationSpeakerEdit.setPlaceholderText("Speaker")
        self.narrationVoiceCombo = QComboBox(self.narrationControlsGroup)
        self.narrationVoiceCombo.setEditable(True)
        self.narrationVoiceCombo.addItems(SSMLConfig().list_voices())
        self.narrationRateCombo = QComboBox(self.narrationControlsGroup)
        self.narrationRateCombo.addItems(
            ["default", "x-slow", "slow", "medium", "fast", "x-fast"]
        )
        self.narrationVolumeCombo = QComboBox(self.narrationControlsGroup)
        self.narrationVolumeCombo.addItems(
            ["default", "silent", "x-soft", "soft", "medium", "loud", "x-loud"]
        )
        self.narrationPauseCombo = QComboBox(self.narrationControlsGroup)
        self.narrationPauseCombo.addItems(["none", "250ms", "500ms", "1s", "2s"])
        self.applyNarrationButton = QPushButton(
            "Apply To Selection",
            self.narrationControlsGroup,
        )
        for label_text, widget in (
            ("Speaker", self.narrationSpeakerEdit),
            ("Voice", self.narrationVoiceCombo),
            ("Rate", self.narrationRateCombo),
            ("Volume", self.narrationVolumeCombo),
            ("Pause", self.narrationPauseCombo),
        ):
            narration_row.addWidget(QLabel(label_text, self.narrationControlsGroup))
            narration_row.addWidget(widget)
        narration_row.addStretch(1)
        narration_row.addWidget(self.applyNarrationButton)
        root_layout.addWidget(self.narrationControlsGroup)

        self.actionHintLabel = QLabel(
            "Type or import text to enable preview and generation actions.",
            central_widget,
        )
        self.actionHintLabel.setObjectName("actionHintLabel")
        self.actionHintLabel.setWordWrap(True)
        root_layout.addWidget(self.actionHintLabel)

        content_row = QHBoxLayout()

        self.editorSplitter = QSplitter(Qt.Orientation.Horizontal, central_widget)
        self.textEdit = QTextEdit(self.editorSplitter)
        self.textEdit.setPlaceholderText(
            "Type or paste text here, or import text from a supported document."
        )
        self.ssmlPreview = QTextEdit(self.editorSplitter)
        self.ssmlPreview.setReadOnly(True)
        self.ssmlPreview.setPlaceholderText("Generated SSML preview appears here.")
        self.editorSplitter.addWidget(self.textEdit)
        self.editorSplitter.addWidget(self.ssmlPreview)
        self.editorSplitter.setSizes([700, 500])
        content_row.addWidget(self.editorSplitter, 1)
        root_layout.addLayout(content_row, 1)

        self.historyGroup = QGroupBox(central_widget)
        self.historyGroup.setObjectName("historyGroup")
        history_layout = QVBoxLayout(self.historyGroup)
        history_layout.setContentsMargins(10, 6, 10, 10)
        history_layout.setSpacing(4)
        self.historyHeader = QWidget(self.historyGroup)
        self.historyHeader.setObjectName("historyHeader")
        history_header_layout = QHBoxLayout(self.historyHeader)
        history_header_layout.setContentsMargins(0, 0, 0, 0)
        self.historyTitleLabel = QLabel("Recent Audio", self.historyHeader)
        self.historyTitleLabel.setObjectName("historyTitleLabel")
        history_header_layout.addWidget(self.historyTitleLabel)
        history_header_layout.addStretch(1)
        self.historyToggleButton = QToolButton(self.historyGroup)
        self.historyToggleButton.setObjectName("historyToggleButton")
        self.historyToggleButton.setText("-")
        self.historyToggleButton.setToolTip("Collapse Recent Audio")
        self.historyToggleButton.setFixedSize(22, 22)
        history_header_layout.addWidget(self.historyToggleButton)
        history_layout.addWidget(self.historyHeader)
        self.historyList = QListWidget(self.historyGroup)
        self.historyList.setAlternatingRowColors(True)
        self.historyList.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection
        )
        self.historyList.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.historyList.setToolTip(
            "Double-click generated audio to play it, or right-click for history actions."
        )
        self.historyGroup.setMaximumHeight(170)
        self.historyGroup.setMinimumHeight(48)
        history_layout.addWidget(self.historyList)
        root_layout.addWidget(self.historyGroup)

        self.settingsSidebar = QGroupBox("Settings", central_widget)
        self.settingsSidebar.setObjectName("settingsSidebar")
        settings_sidebar_layout = QVBoxLayout(self.settingsSidebar)
        self.sidebarSettingsEditor = SettingsEditor(
            AppSettings(),
            self.settingsSidebar,
        )
        settings_sidebar_layout.addWidget(self.sidebarSettingsEditor, 1)
        sidebar_button_row = QHBoxLayout()
        self.applySidebarSettingsButton = QPushButton(
            "Apply",
            self.settingsSidebar,
        )
        self.collapseSettingsSidebarButton = QPushButton(
            "Collapse",
            self.settingsSidebar,
        )
        sidebar_button_row.addStretch(1)
        sidebar_button_row.addWidget(self.applySidebarSettingsButton)
        sidebar_button_row.addWidget(self.collapseSettingsSidebarButton)
        settings_sidebar_layout.addLayout(sidebar_button_row)
        self.settingsSidebar.setMinimumWidth(320)
        self.settingsSidebar.setMaximumWidth(420)
        self.settingsSidebar.hide()
        outer_layout.addWidget(self.settingsSidebar)

        main_window.setCentralWidget(central_widget)

        self.menubar = QMenuBar(main_window)
        self.menuFile = QMenu("File", self.menubar)
        self.menuTools = QMenu("Tools", self.menubar)
        self.menuHelp = QMenu("Help", self.menubar)
        self.actionOpenText = QAction("Open Document", main_window)
        self.actionOpenUrl = QAction("Open URL", main_window)
        self.actionOpenRawHtml = QAction("Import Raw HTML", main_window)
        self.actionExportEditorText = QAction("Export Editor Text", main_window)
        self.actionExportAudio = QAction("Export Audio", main_window)
        self.actionExit = QAction("Exit", main_window)
        self.actionSettings = QAction("Settings", main_window)
        self.actionOpenScraper = QAction("Import Document", main_window)
        self.actionSetupGuide = QAction("Setup Guide", main_window)
        self.actionAbout = QAction("About", main_window)

        self.menuFile.addAction(self.actionOpenText)
        self.menuFile.addAction(self.actionOpenUrl)
        self.menuFile.addAction(self.actionOpenRawHtml)
        self.menuFile.addAction(self.actionExportEditorText)
        self.menuFile.addAction(self.actionExportAudio)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuTools.addAction(self.actionSettings)
        self.menuTools.addAction(self.actionOpenScraper)
        self.menuHelp.addAction(self.actionSetupGuide)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionAbout)

        self.menubar.addMenu(self.menuFile)
        self.menubar.addMenu(self.menuTools)
        self.menubar.addMenu(self.menuHelp)
        main_window.setMenuBar(self.menubar)

        self.statusbar = QStatusBar(main_window)
        self.outputStatusLabel = QLabel(
            "Provider: Azure Speech | Voice: en-US-GuyNeural | Rate: medium | Speech Volume: medium | Output: data/dynamic/audio",
            self.statusbar,
        )
        self.outputStatusLabel.setObjectName("outputStatusLabel")
        self.outputStatusLabel.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.outputStatusLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.outputStatusLabel.setToolTip(
            "Current provider, voice, rate, speech volume, and output location."
        )
        self.statusbar.addPermanentWidget(self.outputStatusLabel, 1)
        main_window.setStatusBar(self.statusbar)

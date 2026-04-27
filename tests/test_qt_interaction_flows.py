from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow

from app.controller.main_controller import MainController
from app.controller.second_controller import SecondController
from app.gui.second_window import SecondApp
from app.gui.ui_main_window import Ui_MainWindow
from app.model.app_settings import AppSettings


def test_file_menu_exposes_source_and_export_actions(qtbot):
    window = QMainWindow()
    qtbot.addWidget(window)
    ui = Ui_MainWindow()
    ui.setupUi(window)

    file_actions = [
        action.text()
        for action in ui.menuFile.actions()
        if not action.isSeparator()
    ]

    assert file_actions == [
        "Open Document",
        "Open URL",
        "Import Raw HTML",
        "Export Editor Text",
        "Export Audio",
        "Exit",
    ]


def test_history_list_is_actionable_from_real_widget(qtbot):
    window = QMainWindow()
    qtbot.addWidget(window)
    ui = Ui_MainWindow()
    ui.setupUi(window)

    assert ui.historyList.selectionMode() == ui.historyList.SelectionMode.SingleSelection
    assert ui.historyList.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
    assert "Double-click" in ui.historyList.toolTip()
    assert "right-click" in ui.historyList.toolTip()
    assert ui.historyTitleLabel.text() == "Recent Audio"
    assert ui.historyToggleButton.text() == "-"


def test_recent_audio_toggle_collapses_and_expands_panel(qtbot):
    window = QMainWindow()
    qtbot.addWidget(window)
    ui = Ui_MainWindow()
    ui.setupUi(window)
    controller = MainController.__new__(MainController)
    controller.view = ui
    window.show()
    qtbot.waitExposed(window)

    controller.toggle_recent_audio()

    assert ui.historyList.isHidden()
    assert ui.historyToggleButton.text() == "+"
    assert "Expand" in ui.historyToggleButton.toolTip()
    assert ui.historyGroup.maximumHeight() == 48
    assert ui.historyGroup.minimumHeight() == 48
    assert ui.historyTitleLabel.isVisible()

    controller.toggle_recent_audio()

    assert not ui.historyList.isHidden()
    assert ui.historyToggleButton.text() == "-"
    assert "Collapse" in ui.historyToggleButton.toolTip()
    assert ui.historyGroup.maximumHeight() == 170


def test_output_summary_is_right_aligned_statusbar_text(qtbot):
    window = QMainWindow()
    qtbot.addWidget(window)
    ui = Ui_MainWindow()
    ui.setupUi(window)
    window.resize(1200, 620)
    window.show()
    qtbot.waitExposed(window)

    assert ui.settingsSidebar.isHidden()
    assert ui.outputStatusLabel.parent() == ui.statusbar
    assert ui.outputStatusLabel.alignment() & Qt.AlignmentFlag.AlignRight
    assert "Voice:" in ui.outputStatusLabel.text()
    assert ui.outputStatusLabel.width() > ui.statusbar.width() // 2


def test_settings_sidebar_toggle_and_apply_uses_main_window_editor(qtbot):
    window = QMainWindow()
    qtbot.addWidget(window)
    ui = Ui_MainWindow()
    ui.setupUi(window)
    controller = MainController.__new__(MainController)
    controller.view = ui
    controller.settings = AppSettings(
        voice="en-US-GuyNeural",
        output_dir="data/dynamic/audio",
    )
    applied_settings = []
    controller._apply_updated_settings = applied_settings.append

    controller.toggle_settings_sidebar()

    assert not ui.settingsSidebar.isHidden()
    assert ui.openSettingsButton.text() == "Hide Settings"

    ui.sidebarSettingsEditor.rate_combo.setCurrentText("slow")
    controller.apply_sidebar_settings()

    assert applied_settings
    assert applied_settings[-1].speaking_rate == "slow"

    controller.hide_settings_sidebar()

    assert ui.settingsSidebar.isHidden()
    assert ui.openSettingsButton.text() == "Settings"


def test_loading_state_toggles_real_import_dialog_buttons(qtbot):
    dialog = SecondApp()
    qtbot.addWidget(dialog)
    controller = SecondController(dialog)

    controller._set_loading_state(True)

    assert not dialog.browseButton.isEnabled()
    assert not dialog.loadButton.isEnabled()
    assert not dialog.importButton.isEnabled()
    assert dialog.cancelLoadButton.isEnabled()
    assert "Loading document" in dialog.infoLabel.text()

    controller._set_loading_state(False)

    assert dialog.browseButton.isEnabled()
    assert dialog.loadButton.isEnabled()
    assert dialog.importButton.isEnabled()
    assert not dialog.cancelLoadButton.isEnabled()


def test_loaded_rows_populate_table_apply_profile_and_select_rows(qtbot):
    dialog = SecondApp()
    qtbot.addWidget(dialog)
    controller = SecondController(dialog)
    rows = [
        {
            "item_number": 1,
            "title": "Page 1",
            "primary_text": "Unique page text.",
            "secondary_text": "Page context.",
            "source_type": "pdf",
            "metadata": {"kind": "page"},
        },
        {
            "item_number": 2,
            "title": "Page 2",
            "primary_text": "Second page text.",
            "secondary_text": "",
            "source_type": "pdf",
            "metadata": {"kind": "page"},
        },
    ]

    controller._handle_load_finished(rows)

    assert dialog.previewTable.rowCount() == 2
    assert dialog.previewTable.item(0, 0).text() == "Page 1"
    assert dialog.previewTable.item(0, 1).text() == "Unique page text."
    assert dialog.previewTable.horizontalHeaderItem(1).text() == "Page Text"
    assert dialog.previewTable.horizontalHeaderItem(2).text() == "Page Context"
    assert "Page Text Only" in controller.current_mode_map
    assert len(dialog.previewTable.selectionModel().selectedRows()) == 2
    assert "Loaded 2 document section" in dialog.infoLabel.text()


def test_import_selected_rows_emits_text_and_accepts_dialog(qtbot):
    dialog = SecondApp()
    qtbot.addWidget(dialog)
    controller = SecondController(dialog)
    imported_text = []
    dialog.textImported.connect(imported_text.append)
    rows = [
        {
            "item_number": 1,
            "title": "Text Block",
            "primary_text": "Main narration text.",
            "secondary_text": "Reusable context.",
            "source_type": "txt",
            "metadata": {},
        }
    ]
    controller._handle_load_finished(rows)
    dialog.contentModeComboBox.setCurrentText("Text Block Only")

    controller.import_text()

    assert imported_text == ["Main narration text."]
    assert dialog.result() == dialog.DialogCode.Accepted

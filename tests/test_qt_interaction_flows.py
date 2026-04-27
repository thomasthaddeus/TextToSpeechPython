import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow

from app.controller.second_controller import SecondController
from app.gui.second_window import SecondApp
from app.gui.ui_main_window import Ui_MainWindow


def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class MainWindowInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def setUp(self):
        self.window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_file_menu_exposes_source_and_export_actions(self):
        file_actions = [
            action.text()
            for action in self.ui.menuFile.actions()
            if not action.isSeparator()
        ]

        self.assertEqual(
            file_actions,
            [
                "Open Document",
                "Open URL",
                "Import Raw HTML",
                "Export Editor Text",
                "Export Audio",
                "Exit",
            ],
        )

    def test_history_list_is_actionable_from_real_widget(self):
        self.assertEqual(
            self.ui.historyList.selectionMode(),
            self.ui.historyList.SelectionMode.SingleSelection,
        )
        self.assertEqual(
            self.ui.historyList.contextMenuPolicy(),
            Qt.ContextMenuPolicy.CustomContextMenu,
        )
        self.assertIn("Double-click", self.ui.historyList.toolTip())
        self.assertIn("right-click", self.ui.historyList.toolTip())


class ImportDialogInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def setUp(self):
        self.dialog = SecondApp()
        self.controller = SecondController(self.dialog)

    def tearDown(self):
        self.dialog.close()
        self.dialog.deleteLater()
        self.app.processEvents()

    def test_loading_state_toggles_real_import_dialog_buttons(self):
        self.controller._set_loading_state(True)

        self.assertFalse(self.dialog.browseButton.isEnabled())
        self.assertFalse(self.dialog.loadButton.isEnabled())
        self.assertFalse(self.dialog.importButton.isEnabled())
        self.assertTrue(self.dialog.cancelLoadButton.isEnabled())
        self.assertIn("Loading document", self.dialog.infoLabel.text())

        self.controller._set_loading_state(False)

        self.assertTrue(self.dialog.browseButton.isEnabled())
        self.assertTrue(self.dialog.loadButton.isEnabled())
        self.assertTrue(self.dialog.importButton.isEnabled())
        self.assertFalse(self.dialog.cancelLoadButton.isEnabled())

    def test_loaded_rows_populate_table_apply_profile_and_select_rows(self):
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

        self.controller._handle_load_finished(rows)

        self.assertEqual(self.dialog.previewTable.rowCount(), 2)
        self.assertEqual(self.dialog.previewTable.item(0, 0).text(), "Page 1")
        self.assertEqual(self.dialog.previewTable.item(0, 1).text(), "Unique page text.")
        self.assertEqual(
            self.dialog.previewTable.horizontalHeaderItem(1).text(),
            "Page Text",
        )
        self.assertEqual(
            self.dialog.previewTable.horizontalHeaderItem(2).text(),
            "Page Context",
        )
        self.assertIn("Page Text Only", self.controller.current_mode_map)
        self.assertEqual(
            len(self.dialog.previewTable.selectionModel().selectedRows()),
            2,
        )
        self.assertIn("Loaded 2 document section", self.dialog.infoLabel.text())

    def test_import_selected_rows_emits_text_and_accepts_dialog(self):
        imported_text = []
        self.dialog.textImported.connect(imported_text.append)
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
        self.controller._handle_load_finished(rows)
        self.dialog.contentModeComboBox.setCurrentText("Text Block Only")

        self.controller.import_text()

        self.assertEqual(imported_text, ["Main narration text."])
        self.assertEqual(self.dialog.result(), self.dialog.DialogCode.Accepted)


if __name__ == "__main__":
    unittest.main()

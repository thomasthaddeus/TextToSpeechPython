import unittest

from app.controller.second_controller import SecondController


class ComboBoxStub:
    def __init__(self, text=""):
        self.items = []
        self._text = text

    def currentText(self):
        return self._text

    def clear(self):
        self.items.clear()

    def addItem(self, text):
        self.items.append(text)
        if not self._text:
            self._text = text

    def setCurrentText(self, text):
        self._text = text


class LabelStub:
    def __init__(self):
        self.text = ""

    def setText(self, text):
        self.text = text


class TableStub:
    def __init__(self):
        self.headers = []

    def setHorizontalHeaderLabels(self, labels):
        self.headers = labels


class ViewStub:
    def __init__(self, mode_text):
        self.contentModeComboBox = ComboBoxStub(mode_text)
        self.previewTable = TableStub()
        self.selectionHelpLabel = LabelStub()


class SecondControllerImportTests(unittest.TestCase):
    def _controller(self, mode_text="Prefer Context When Available"):
        controller = SecondController.__new__(SecondController)
        controller.view = ViewStub(mode_text)
        controller.current_mode_map = {
            "Prefer Context When Available": "prefer_secondary",
            "Context Only": "secondary_only",
            "Main Text Only": "primary_only",
            "Combine Main Text and Context": "combine",
            "Prefer Speaker Notes": "prefer_secondary",
            "Speaker Notes Only": "secondary_only",
            "Slide Text Only": "primary_only",
            "Combine Slide Text and Speaker Notes": "combine",
            "Row Text Only": "primary_only",
            "Include Sheet and Column Context": "combine",
        }
        return controller

    def test_build_import_payload_prefers_secondary_with_primary_fallback(self):
        controller = self._controller("Prefer Context When Available")
        selected_rows = [
            {
                "item_number": 1,
                "title": "Item 1",
                "primary_text": "Primary summary",
                "secondary_text": "Context notes",
            },
            {
                "item_number": 2,
                "title": "Item 2",
                "primary_text": "Only primary text",
                "secondary_text": "",
            },
        ]

        payload_rows, imported_text = controller._build_import_payload(selected_rows)

        self.assertEqual(len(payload_rows), 2)
        self.assertEqual(payload_rows[0]["resolved_text"], "Context notes")
        self.assertEqual(payload_rows[1]["resolved_text"], "Only primary text")
        self.assertEqual(imported_text, "Context notes\n\nOnly primary text")

    def test_build_import_payload_combines_main_text_and_context(self):
        controller = self._controller("Combine Main Text and Context")
        selected_rows = [
            {
                "item_number": 3,
                "title": "Chapter 3",
                "primary_text": "Agenda",
                "secondary_text": "Longer narration",
            }
        ]

        payload_rows, imported_text = controller._build_import_payload(selected_rows)

        self.assertEqual(payload_rows[0]["content_mode"], "combine")
        self.assertEqual(
            payload_rows[0]["resolved_text"],
            "Agenda\n\nLonger narration",
        )
        self.assertEqual(imported_text, "Agenda\n\nLonger narration")

    def test_apply_format_profile_uses_slide_specific_terms_for_pptx(self):
        controller = self._controller("")

        controller._apply_format_profile("pptx")

        self.assertEqual(
            controller.view.previewTable.headers,
            ["Item", "Slide Text", "Speaker Notes"],
        )
        self.assertIn("Speaker Notes Only", controller.view.contentModeComboBox.items)
        self.assertIn("slides", controller.view.selectionHelpLabel.text)

    def test_apply_format_profile_uses_page_terms_for_pdf(self):
        controller = self._controller("")

        controller._apply_format_profile("pdf")

        self.assertEqual(
            controller.view.previewTable.headers,
            ["Item", "Page Text", "Page Context"],
        )
        self.assertEqual(
            controller.current_mode_map["Page Text Only"],
            "primary_only",
        )

    def test_apply_format_profile_uses_spreadsheet_terms_for_xlsx(self):
        controller = self._controller("")

        controller._apply_format_profile("xlsx")

        self.assertEqual(
            controller.view.previewTable.headers,
            ["Item", "Row Text", "Sheet / Column Context"],
        )
        self.assertEqual(
            controller.current_mode_map["Include Sheet and Column Context"],
            "combine",
        )

    def test_unknown_format_uses_generic_document_terms(self):
        controller = self._controller("")

        controller._apply_format_profile("unknown")

        self.assertEqual(
            controller.view.previewTable.headers,
            ["Item", "Main Text", "Context"],
        )
        self.assertIn(
            "Prefer Context When Available",
            controller.view.contentModeComboBox.items,
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from app.controller.second_controller import SecondController


class ComboBoxStub:
    def __init__(self, text):
        self._text = text

    def currentText(self):
        return self._text


class ViewStub:
    def __init__(self, mode_text):
        self.contentModeComboBox = ComboBoxStub(mode_text)


class SecondControllerImportTests(unittest.TestCase):
    def _controller(self, mode_text="Prefer Secondary Text"):
        controller = SecondController.__new__(SecondController)
        controller.view = ViewStub(mode_text)
        return controller

    def test_build_import_payload_prefers_secondary_with_primary_fallback(self):
        controller = self._controller("Prefer Secondary Text")
        selected_rows = [
            {
                "item_number": 1,
                "title": "Item 1",
                "primary_text": "Primary summary",
                "secondary_text": "Secondary notes",
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
        self.assertEqual(payload_rows[0]["resolved_text"], "Secondary notes")
        self.assertEqual(payload_rows[1]["resolved_text"], "Only primary text")
        self.assertEqual(imported_text, "Secondary notes\n\nOnly primary text")

    def test_build_import_payload_combines_primary_and_secondary_text(self):
        controller = self._controller("Combine Primary and Secondary Text")
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


if __name__ == "__main__":
    unittest.main()

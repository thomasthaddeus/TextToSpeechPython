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
    def _controller(self, mode_text="Prefer Notes"):
        controller = SecondController.__new__(SecondController)
        controller.view = ViewStub(mode_text)
        return controller

    def test_build_import_payload_prefers_notes_with_slide_fallback(self):
        controller = self._controller("Prefer Notes")
        selected_rows = [
            {
                "slide_number": 1,
                "slide_text": "Slide summary",
                "notes_text": "Speaker notes",
            },
            {
                "slide_number": 2,
                "slide_text": "Only slide text",
                "notes_text": "",
            },
        ]

        payload_rows, imported_text = controller._build_import_payload(selected_rows)

        self.assertEqual(len(payload_rows), 2)
        self.assertEqual(payload_rows[0]["resolved_text"], "Speaker notes")
        self.assertEqual(payload_rows[1]["resolved_text"], "Only slide text")
        self.assertEqual(imported_text, "Speaker notes\n\nOnly slide text")

    def test_build_import_payload_combines_slide_text_and_notes(self):
        controller = self._controller("Combine Slide Text and Notes")
        selected_rows = [
            {
                "slide_number": 3,
                "slide_text": "Agenda",
                "notes_text": "Longer narration",
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

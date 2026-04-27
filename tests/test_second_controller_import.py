import pytest

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


@pytest.fixture
def controller_factory():
    def build_controller(mode_text="Prefer Context When Available"):
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

    return build_controller


def test_build_import_payload_prefers_secondary_with_primary_fallback(
    controller_factory,
):
    controller = controller_factory("Prefer Context When Available")
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

    assert len(payload_rows) == 2
    assert payload_rows[0]["resolved_text"] == "Context notes"
    assert payload_rows[1]["resolved_text"] == "Only primary text"
    assert imported_text == "Context notes\n\nOnly primary text"


def test_build_import_payload_combines_main_text_and_context(controller_factory):
    controller = controller_factory("Combine Main Text and Context")
    selected_rows = [
        {
            "item_number": 3,
            "title": "Chapter 3",
            "primary_text": "Agenda",
            "secondary_text": "Longer narration",
        }
    ]

    payload_rows, imported_text = controller._build_import_payload(selected_rows)

    assert payload_rows[0]["content_mode"] == "combine"
    assert payload_rows[0]["resolved_text"] == "Agenda\n\nLonger narration"
    assert imported_text == "Agenda\n\nLonger narration"


@pytest.mark.parametrize(
    ("source_type", "expected_headers", "expected_mode", "expected_mode_value"),
    [
        (
            "pptx",
            ["Item", "Slide Text", "Speaker Notes"],
            "Speaker Notes Only",
            "secondary_only",
        ),
        (
            "pdf",
            ["Item", "Page Text", "Page Context"],
            "Page Text Only",
            "primary_only",
        ),
        (
            "xlsx",
            ["Item", "Row Text", "Sheet / Column Context"],
            "Include Sheet and Column Context",
            "combine",
        ),
        (
            "unknown",
            ["Item", "Main Text", "Context"],
            "Prefer Context When Available",
            "prefer_secondary",
        ),
    ],
)
def test_apply_format_profile_uses_format_specific_terms(
    controller_factory,
    source_type,
    expected_headers,
    expected_mode,
    expected_mode_value,
):
    controller = controller_factory("")

    controller._apply_format_profile(source_type)

    assert controller.view.previewTable.headers == expected_headers
    assert expected_mode in controller.view.contentModeComboBox.items
    assert controller.current_mode_map[expected_mode] == expected_mode_value

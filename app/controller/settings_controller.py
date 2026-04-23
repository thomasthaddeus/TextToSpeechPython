"""Helpers for applying settings changes from the dialog."""

from app.gui.settings_dialog import SettingsDialog


class SettingsController:
    """
    Show the settings dialog and return updated settings when accepted.
    """

    def __init__(self, parent_view):
        self.parent_view = parent_view

    def edit_settings(self, settings):
        dialog = SettingsDialog(settings, self.parent_view)
        if dialog.exec():
            return dialog.get_settings()
        return None

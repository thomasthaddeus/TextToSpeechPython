"""In-app documentation viewer for setup and help guides."""

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QTextBrowser,
    QVBoxLayout,
)


class SetupGuideDialog(QDialog):
    """Render local markdown help content without leaving the application."""

    def __init__(self, guide_path, parent=None):
        super().__init__(parent)
        self.docs_root = Path(guide_path).resolve().parent
        self.current_path = None

        self.setWindowTitle("Setup Guide")
        self.resize(820, 620)

        layout = QVBoxLayout(self)
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(False)
        self.browser.anchorClicked.connect(self._handle_anchor_clicked)
        layout.addWidget(self.browser, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

        self.load_markdown(guide_path)

    def load_markdown(self, guide_path):
        resolved_path = Path(guide_path).resolve()
        if not resolved_path.exists():
            QMessageBox.warning(
                self,
                "Guide Missing",
                f"The guide could not be found at {resolved_path.name}.",
            )
            return

        self.current_path = resolved_path
        self.setWindowTitle(self._title_from_path(resolved_path))
        self.browser.setMarkdown(resolved_path.read_text(encoding="utf-8"))
        self.browser.moveCursor(self.browser.textCursor().MoveOperation.Start)

    def _handle_anchor_clicked(self, url):
        if url.isLocalFile():
            self.load_markdown(url.toLocalFile())
            return

        target = url.toString()
        if target.startswith(("http://", "https://", "mailto:")):
            QDesktopServices.openUrl(url)
            return

        if not self.current_path:
            return

        local_path = (self.current_path.parent / target).resolve()
        try:
            local_path.relative_to(self.docs_root)
        except ValueError:
            QDesktopServices.openUrl(QUrl(target))
            return

        self.load_markdown(local_path)

    def _title_from_path(self, guide_path):
        title = guide_path.stem.replace("_", " ").replace("-", " ").title()
        return f"{title} - Text To Speech Help"

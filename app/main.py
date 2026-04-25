import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from app.gui.main_window import MainApp
from app.model.app_settings import AppSettings
from app.utils.logging_config import configure_logging
from loguru import logger


SETTINGS_PATH = "data/dynamic/app_settings.json"
STYLESHEET_PATH = Path("app/assets/styles/styles.qss")
APP_ICON_PATH = "app/assets/icons/tts.ico"

def main():
    settings = AppSettings.load(SETTINGS_PATH)
    log_file = configure_logging(settings.logging_enabled)
    if log_file:
        logger.info("Application startup.")

    app = QApplication(sys.argv)
    if Path(APP_ICON_PATH).exists():
        app.setWindowIcon(QIcon(APP_ICON_PATH))
    if STYLESHEET_PATH.exists():
        app.setStyleSheet(STYLESHEET_PATH.read_text(encoding="utf-8"))
    main_win = MainApp()
    main_win.show()
    exit_code = app.exec()
    if log_file:
        logger.info("Application shutdown with exit code {}", exit_code)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()

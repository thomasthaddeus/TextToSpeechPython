import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from app.gui.main_window import MainApp
from app.model.app_settings import AppSettings
from app.utils.logging_config import configure_logging
from app.utils.resources import load_stylesheet, resource_path, resource_string
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
    if resource_path(APP_ICON_PATH).exists():
        app.setWindowIcon(QIcon(resource_string(APP_ICON_PATH)))
    stylesheet = load_stylesheet(STYLESHEET_PATH)
    if stylesheet:
        app.setStyleSheet(stylesheet)
    main_win = MainApp()
    main_win.show()
    exit_code = app.exec()
    if log_file:
        logger.info("Application shutdown with exit code {}", exit_code)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()

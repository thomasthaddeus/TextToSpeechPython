import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainApp  # Import the main window class

def main():
    app = QApplication(sys.argv)
    main_win = MainApp()
    main_win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

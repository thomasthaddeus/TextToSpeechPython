from app.controller.second_controller import SecondController
from app.gui.second_window import SecondApp


class MainController:
    def __init__(self, view):
        self.view = view
        self.view.openSecondWindowButton.clicked.connect(self.open_second_window)
        self.second_window = None
        self.second_controller = None

    def open_second_window(self):
        if not self.second_window or not self.second_window.isVisible():
            self.second_window = SecondApp(self.view)
            self.second_controller = SecondController(self.second_window)
            self.second_window.show()

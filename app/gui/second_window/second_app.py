

class SecondApp(QDialog, second_window.Ui_Dialog):
    def __init__(self, parent=None):
        super(SecondApp, self).__init__(parent)
        self.setupUi(self)
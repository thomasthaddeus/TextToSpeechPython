import mylib

class ComputeController:
    def __init__(self, view):
        self.view = view
        self.view.computeButton.clicked.connect(self.on_compute)

    def on_compute(self):
        try:
            x = float(self.view.inputField.text())
            result = mylib.compute(x)
            self.view.resultLabel.setText(str(result))
        except ValueError:
            self.view.resultLabel.setText("Invalid input")

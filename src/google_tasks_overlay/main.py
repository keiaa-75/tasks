import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google Tasks Overlay")
        self.setGeometry(100, 100, 400, 600)

        # Make the window frameless and transparent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # X11-specific flags for overlay behavior
        if os.environ.get('XDG_SESSION_TYPE') == 'x11':
            self.setWindowFlags(
                self.windowFlags() |
                Qt.WindowType.X11BypassWindowManagerHint
            )

        # Add a label to show something is working
        label = QLabel("Frameless Transparent Window", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QTimer

from . import auth
from . import tasks_api


class MainWindow(QMainWindow):
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
        self.setWindowTitle("Google Tasks Overlay")
        self.setGeometry(100, 100, 400, 400)  # Square window

        # Make the window frameless and stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.8);")

        # Add a label to show tasks
        self.tasks_label = QLabel("Loading tasks...", self)
        self.tasks_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.tasks_label.setStyleSheet("color: white; padding: 10px;")
        self.setCentralWidget(self.tasks_label)

        # Refresh tasks on a timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(300000)  # 5 minutes

        self.refresh_tasks()

    def refresh_tasks(self):
        try:
            tasks = tasks_api.fetch_tasks(self.credentials)
            if tasks:
                task_text = "\n".join([task["title"] for task in tasks])
                self.tasks_label.setText(task_text)
            else:
                self.tasks_label.setText("No tasks found.")
        except Exception as e:
            print(f"An error occurred while fetching tasks: {e}")
            self.tasks_label.setText("Error fetching tasks.")

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()


def main():
    try:
        credentials = auth.get_credentials()
        if credentials:
            print("Authentication successful!")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during authentication: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    main_window = MainWindow(credentials)

    # System tray icon
    tray_icon = QSystemTrayIcon(QIcon.fromTheme("application-x-executable"), app)
    tray_icon.setToolTip("Google Tasks Overlay")

    def handle_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            main_window.toggle_visibility()

    tray_icon.activated.connect(handle_tray_activated)

    # Tray menu
    menu = QMenu()
    toggle_action = QAction("Show/Hide", menu)
    toggle_action.triggered.connect(main_window.toggle_visibility)
    menu.addAction(toggle_action)

    quit_action = QAction("Quit", menu)
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    tray_icon.setContextMenu(menu)
    tray_icon.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

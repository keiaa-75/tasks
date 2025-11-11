import sys
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QLabel, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QScreen
from PyQt6.QtCore import Qt, QTimer

from . import auth
from . import tasks_api


class TaskItem(QWidget):
    def __init__(self, title, due_date):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 14px;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        if due_date and due_date != "No Due Date":
            try:
                dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%m/%d/%y")
            except:
                formatted_date = "Invalid date"
            
            due_label = QLabel(formatted_date)
            due_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 12px;")
            layout.addWidget(due_label)
        
        self.setStyleSheet("TaskItem { background-color: rgba(255, 255, 255, 0.1); margin: 2px; }")


class MainWindow(QMainWindow):
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
        
        self.setWindowTitle("Google Tasks")
        self.setFixedSize(300, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: rgba(30, 30, 30, 0.7);")
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(2)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_area.setWidget(self.content_widget)
        
        layout.addWidget(self.scroll_area)
        self.setCentralWidget(main_widget)
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(300000)
        
        self.refresh_tasks()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.position_bottom_right()
    
    def position_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 20)
    
    def refresh_tasks(self):
        try:
            tasks = tasks_api.fetch_tasks(self.credentials)
            self.update_tasks(tasks)
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            self.update_tasks([])
    
    def update_tasks(self, tasks):
        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().setParent(None)
        
        if not tasks:
            no_tasks = QLabel("No tasks")
            no_tasks.setStyleSheet("color: white; font-size: 14px; padding: 20px;")
            no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_tasks)
        else:
            for task in tasks:
                task_item = TaskItem(task["title"], task["due"])
                self.content_layout.addWidget(task_item)
        
        self.content_layout.addStretch()
    
    def toggle_visibility(self):
        self.hide() if self.isVisible() else self.show()


def main():
    try:
        credentials = auth.get_credentials()
    except Exception as e:
        print(f"Authentication error: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    main_window = MainWindow(credentials)

    tray_icon = QSystemTrayIcon(QIcon.fromTheme("application-x-executable"), app)
    tray_icon.activated.connect(lambda: main_window.toggle_visibility())

    menu = QMenu()
    menu.addAction("Toggle", main_window.toggle_visibility)
    menu.addAction("Quit", app.quit)
    tray_icon.setContextMenu(menu)
    tray_icon.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

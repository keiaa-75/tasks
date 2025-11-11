import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtGui import QIcon, QAction, QPainter, QPainterPath, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, QPoint

from . import auth
from . import tasks_api


class TaskItem(QWidget):
    def __init__(self, title, due_date):
        super().__init__()
        self.setFixedHeight(50)
        self.setStyleSheet("""
            TaskItem {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin: 2px;
            }
            TaskItem:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Task title (truncated if too long)
        title_label = QLabel(self._truncate_text(title, 30))
        title_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Due date badge
        if due_date and due_date != "No Due Date":
            badge = self._create_due_badge(due_date)
            layout.addWidget(badge)
    
    def _truncate_text(self, text, max_length):
        return text[:max_length] + "..." if len(text) > max_length else text
    
    def _create_due_badge(self, due_date):
        try:
            dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            formatted_date = dt.strftime("%y%m%d-00:00")
        except:
            formatted_date = "Invalid"
        
        badge = QLabel(formatted_date)
        badge.setStyleSheet("""
            background-color: rgba(100, 150, 255, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        """)
        return badge


class TasksList(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
        """)
        
        self.content_widget = QWidget()
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.setWidget(self.content_widget)
    
    def update_tasks(self, tasks):
        # Clear existing tasks
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)
        
        if not tasks:
            no_tasks = QLabel("No tasks found")
            no_tasks.setStyleSheet("color: white; font-size: 14px; padding: 20px;")
            no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(no_tasks)
        else:
            for task in tasks:
                task_item = TaskItem(task["title"], task["due"])
                self.layout.addWidget(task_item)
        
        self.layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
        self.drag_position = QPoint()
        
        self.setWindowTitle("Google Tasks Overlay")
        self.setGeometry(100, 100, 350, 500)
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main widget with rounded corners
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 0.95);
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header for dragging
        header = QWidget()
        header.setFixedHeight(40)
        header.setStyleSheet("""
            background-color: rgba(50, 50, 50, 0.8);
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        
        title_label = QLabel("Google Tasks")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        layout.addWidget(header)
        
        # Tasks list
        self.tasks_list = TasksList()
        layout.addWidget(self.tasks_list)
        
        self.setCentralWidget(main_widget)
        
        # Refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(300000)  # 5 minutes
        
        self.refresh_tasks()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() <= 40:
            self.drag_position = event.pos()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def refresh_tasks(self):
        try:
            tasks = tasks_api.fetch_tasks(self.credentials)
            self.tasks_list.update_tasks(tasks)
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            self.tasks_list.update_tasks([])

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

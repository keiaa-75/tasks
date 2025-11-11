import sys
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSystemTrayIcon, QMenu, QCheckBox
from PyQt6.QtGui import QIcon, QAction, QScreen
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from . import auth
from . import tasks_api


class AuthWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            credentials = auth.get_credentials()
            self.finished.emit(credentials)
        except Exception as e:
            self.error.emit(str(e))


class TaskFetchWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
    
    def run(self):
        try:
            tasks = tasks_api.fetch_tasks(self.credentials)
            self.finished.emit(tasks)
        except Exception as e:
            self.error.emit(str(e))


class TaskCompleteWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, credentials, tasklist_id, task_id, title):
        super().__init__()
        self.credentials = credentials
        self.tasklist_id = tasklist_id
        self.task_id = task_id
        self.title = title
    
    def run(self):
        try:
            tasks_api.complete_task(self.credentials, self.tasklist_id, self.task_id, self.title)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class TaskItem(QWidget):
    def __init__(self, task, credentials, refresh_callback):
        super().__init__()
        self.task = task
        self.credentials = credentials
        self.refresh_callback = refresh_callback
        self.complete_worker = None
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task["status"] == "completed")
        self.checkbox.setFixedSize(16, 16)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QCheckBox::indicator:checked {
                background-color: rgba(100, 150, 255, 0.8);
                border: 1px solid rgba(100, 150, 255, 1.0);
            }
        """)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        is_completed = task["status"] == "completed"
        title_style = "color: rgba(255, 255, 255, 0.5); text-decoration: line-through;" if is_completed else "color: white;"
        
        self.title_label = QLabel(task["title"])
        self.title_label.setStyleSheet(f"{title_style} font-size: 14px;")
        self.title_label.setWordWrap(True)
        content_layout.addWidget(self.title_label)
        
        if task["due"] and task["due"] != "No Due Date":
            try:
                dt = datetime.fromisoformat(task["due"].replace('Z', '+00:00'))
                formatted_date = dt.strftime("%m/%d/%y")
            except:
                formatted_date = "Invalid date"
            
            due_style = "color: rgba(255, 255, 255, 0.3);" if is_completed else "color: rgba(255, 255, 255, 0.6);"
            due_label = QLabel(formatted_date)
            due_label.setStyleSheet(f"{due_style} font-size: 12px;")
            content_layout.addWidget(due_label)
        
        layout.addLayout(content_layout, 1)
        
        self.setStyleSheet("TaskItem { background-color: rgba(255, 255, 255, 0.1); margin: 2px; }")
    
    def on_checkbox_changed(self, state):
        if state == Qt.CheckState.Checked.value and self.task["status"] != "completed":
            self.checkbox.setEnabled(False)
            self.title_label.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 14px;")
            
            self.complete_worker = TaskCompleteWorker(
                self.credentials, self.task["tasklist_id"], self.task["id"], self.task["title"]
            )
            self.complete_worker.finished.connect(self.on_complete_success)
            self.complete_worker.error.connect(self.on_complete_error)
            self.complete_worker.start()
    
    def on_complete_success(self):
        self.refresh_callback()
    
    def on_complete_error(self, error):
        print(f"Error completing task: {error}")
        self.checkbox.setChecked(False)
        self.checkbox.setEnabled(True)
        self.title_label.setStyleSheet("color: white; font-size: 14px;")


class MainWindow(QMainWindow):
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
        self.fetch_worker = None
        
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
        
        self.show_loading()
        self.refresh_tasks()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.position_bottom_right()
    
    def position_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 20)
    
    def show_loading(self):
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        loading = QLabel("Loading...")
        loading.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 14px; padding: 20px;")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(loading)
    
    def refresh_tasks(self):
        if self.fetch_worker and self.fetch_worker.isRunning():
            return
        
        self.fetch_worker = TaskFetchWorker(self.credentials)
        self.fetch_worker.finished.connect(self.update_tasks)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()
    
    def on_fetch_error(self, error):
        print(f"Error fetching tasks: {error}")
        self.update_tasks([])
    
    def update_tasks(self, tasks):
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not tasks:
            no_tasks = QLabel("No tasks")
            no_tasks.setStyleSheet("color: white; font-size: 14px; padding: 20px;")
            no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_tasks)
        else:
            # Sort tasks: incomplete first, then completed
            incomplete_tasks = [t for t in tasks if t["status"] != "completed"]
            completed_tasks = [t for t in tasks if t["status"] == "completed"]
            
            for task in incomplete_tasks + completed_tasks:
                task_item = TaskItem(task, self.credentials, self.refresh_tasks)
                self.content_layout.addWidget(task_item)
        
        self.content_layout.addStretch()
    
    def toggle_visibility(self):
        self.hide() if self.isVisible() else self.show()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Show loading window immediately
    loading_window = QMainWindow()
    loading_window.setWindowTitle("Google Tasks")
    loading_window.setFixedSize(300, 400)
    loading_window.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
    loading_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    loading_widget = QWidget()
    loading_widget.setStyleSheet("background-color: rgba(30, 30, 30, 0.7);")
    loading_layout = QVBoxLayout(loading_widget)
    loading_label = QLabel("Authenticating...")
    loading_label.setStyleSheet("color: white; font-size: 14px;")
    loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    loading_layout.addWidget(loading_label)
    loading_window.setCentralWidget(loading_widget)
    
    screen = QApplication.primaryScreen().availableGeometry()
    loading_window.move(screen.width() - loading_window.width() - 20, screen.height() - loading_window.height() - 20)
    loading_window.show()

    main_window = None
    tray_icon = QSystemTrayIcon(QIcon.fromTheme("application-x-executable"), app)
    
    def on_auth_success(credentials):
        nonlocal main_window
        loading_window.close()
        main_window = MainWindow(credentials)
        tray_icon.activated.connect(lambda: main_window.toggle_visibility())
        
        menu = QMenu()
        menu.addAction("Toggle", main_window.toggle_visibility)
        menu.addAction("Quit", app.quit)
        tray_icon.setContextMenu(menu)
        tray_icon.show()
    
    def on_auth_error(error):
        print(f"Authentication error: {error}")
        loading_window.close()
        sys.exit(1)
    
    auth_worker = AuthWorker()
    auth_worker.finished.connect(on_auth_success)
    auth_worker.error.connect(on_auth_error)
    auth_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

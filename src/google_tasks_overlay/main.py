import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSystemTrayIcon, QMenu, QPushButton, QDialog, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer

from .workers import AuthWorker, TaskFetchWorker, TaskCreateWorker, TaskUpdateWorker
from .widgets import TaskItem, TaskDialog


class MainWindow(QMainWindow):
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
        self.fetch_worker = None
        self.create_worker = None
        self.update_worker = None
        
        self.setWindowTitle("Google Tasks")
        self.setFixedSize(300, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: rgba(30, 30, 30, 0.7);")
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
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
        
        # Bottom bar
        bottom_bar = QWidget()
        bottom_bar.setStyleSheet("background-color: rgba(40, 40, 40, 0.8);")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(8, 8, 8, 8)
        
        add_button = QPushButton("+")
        add_button.setFixedSize(32, 32)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 150, 255, 0.8);
                color: white;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 150, 255, 1.0);
            }
        """)
        add_button.clicked.connect(self.show_create_dialog)
        bottom_layout.addWidget(add_button)
        bottom_layout.addStretch()
        
        layout.addWidget(bottom_bar)
        
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
    
    def show_create_dialog(self):
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, due_date = dialog.get_values()
            self.create_task(title, due_date)
    
    def show_edit_dialog(self, task):
        dialog = TaskDialog(self, title=task["title"], due_date=task["due"])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, due_date = dialog.get_values()
            self.update_task(task["tasklist_id"], task["id"], title, due_date)
    
    def create_task(self, title, due_date):
        if self.create_worker and self.create_worker.isRunning():
            return
        
        self.create_worker = TaskCreateWorker(self.credentials, title, due_date)
        self.create_worker.finished.connect(self.on_create_success)
        self.create_worker.error.connect(self.on_create_error)
        self.create_worker.start()
    
    def on_create_success(self):
        self.refresh_tasks()
    
    def on_create_error(self, error):
        print(f"Error creating task: {error}")
        QMessageBox.critical(self, "Error", f"Failed to create task: {error}")
    
    def update_task(self, tasklist_id, task_id, title, due_date):
        if self.update_worker and self.update_worker.isRunning():
            return
        
        self.update_worker = TaskUpdateWorker(self.credentials, tasklist_id, task_id, title, due_date)
        self.update_worker.finished.connect(self.on_update_success)
        self.update_worker.error.connect(self.on_update_error)
        self.update_worker.start()
    
    def on_update_success(self):
        self.refresh_tasks()
    
    def on_update_error(self, error):
        print(f"Error updating task: {error}")
        QMessageBox.critical(self, "Error", f"Failed to update task: {error}")
    
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
                task_item.clicked.connect(self.show_edit_dialog)
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

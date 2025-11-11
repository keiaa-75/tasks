import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSystemTrayIcon, QMenu, QPushButton, QDialog, QMessageBox, QComboBox, QFrame, QProgressBar, QTabWidget, QProgressBar
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer

from .workers import AuthWorker, TaskListFetchWorker, TaskFetchWorker, TaskCreateWorker, TaskUpdateWorker, TaskDeleteWorker, TaskUncompleteWorker
from .widgets import TaskItem, TaskDialog


class MainWindow(QMainWindow):
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
        self.fetch_worker = None
        self.create_worker = None
        self.update_worker = None
        self.delete_worker = None
        self.uncomplete_worker = None
        self.tasklist_fetch_worker = None
        self.selected_tasklist_id = None
        self.tasklists = []
        
        self.setWindowTitle("Google Tasks")
        self.setWindowIcon(QIcon.fromTheme("checkmark"))
        self.setFixedSize(300, 400)
        
        main_widget = QWidget()
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar (moved from bottom)
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 8, 8, 8)
        
        self.tasklist_combo = QComboBox()
        self.tasklist_combo.currentIndexChanged.connect(self.on_tasklist_changed)
        top_layout.addWidget(self.tasklist_combo)
        
        add_button = QPushButton("+")
        add_button.setFixedHeight(self.tasklist_combo.sizeHint().height())
        add_button.clicked.connect(self.show_create_dialog)
        top_layout.addWidget(add_button)
        
        layout.addWidget(top_bar)
        
        # Tab widget for incomplete/completed tasks
        self.tab_widget = QTabWidget()
        
        # Incomplete tasks tab
        self.incomplete_scroll = QScrollArea()
        self.incomplete_scroll.setWidgetResizable(True)
        self.incomplete_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.incomplete_widget = QWidget()
        self.incomplete_layout = QVBoxLayout(self.incomplete_widget)
        self.incomplete_layout.setSpacing(2)
        self.incomplete_layout.setContentsMargins(4, 4, 4, 4)
        self.incomplete_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.incomplete_scroll.setWidget(self.incomplete_widget)
        
        # Completed tasks tab
        self.completed_scroll = QScrollArea()
        self.completed_scroll.setWidgetResizable(True)
        self.completed_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.completed_widget = QWidget()
        self.completed_layout = QVBoxLayout(self.completed_widget)
        self.completed_layout.setSpacing(2)
        self.completed_layout.setContentsMargins(4, 4, 4, 4)
        self.completed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.completed_scroll.setWidget(self.completed_widget)
        
        self.tab_widget.addTab(self.incomplete_scroll, "Tasks")
        self.tab_widget.addTab(self.completed_scroll, "Completed")
        
        layout.addWidget(self.tab_widget)
        
        # Loading indicator at bottom (always visible)
        self.loading_bar = QProgressBar()
        self.loading_bar.setMaximumHeight(8)
        self.loading_bar.setRange(0, 100)  # Normal range when not loading
        self.loading_bar.setValue(0)  # Empty when not loading
        self.loading_bar.setTextVisible(False)  # Hide percentage text
        layout.addWidget(self.loading_bar)
        
        self.setCentralWidget(main_widget)
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(300000)
        
        self.show_loading()
        self.fetch_tasklists()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.position_bottom_right()
    
    def position_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 20)
    
    def show_loading_indicator(self):
        self.loading_bar.setStyleSheet("")  # Reset to default style
        self.loading_bar.setRange(0, 0)  # Indeterminate (animated)
    
    def hide_loading_indicator(self):
        self.loading_bar.setStyleSheet("")  # Reset to default style
        self.loading_bar.setRange(0, 100)  # Normal range
        self.loading_bar.setValue(0)  # Empty/gray appearance
    
    def show_error_indicator(self):
        self.loading_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setValue(100)  # Full red bar
    
    def show_loading(self):
        # Clear both tabs
        for i in reversed(range(self.incomplete_layout.count())):
            widget = self.incomplete_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        for i in reversed(range(self.completed_layout.count())):
            widget = self.completed_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        loading = QLabel("Loading...")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.incomplete_layout.addWidget(loading)
    
    def fetch_tasklists(self):
        if self.tasklist_fetch_worker and self.tasklist_fetch_worker.isRunning():
            return
        
        self.tasklist_fetch_worker = TaskListFetchWorker(self.credentials)
        self.tasklist_fetch_worker.finished.connect(self.on_tasklists_loaded)
        self.tasklist_fetch_worker.error.connect(self.on_tasklists_error)
        self.tasklist_fetch_worker.start()
    
    def on_tasklists_loaded(self, tasklists):
        self.tasklists = tasklists
        self.tasklist_combo.blockSignals(True)
        self.tasklist_combo.clear()
        
        for tasklist in tasklists:
            self.tasklist_combo.addItem(tasklist["title"], tasklist["id"])
        
        if tasklists:
            self.selected_tasklist_id = tasklists[0]["id"]
            self.tasklist_combo.setCurrentIndex(0)
        
        self.tasklist_combo.blockSignals(False)
        self.tasklist_fetch_worker.deleteLater()
        self.tasklist_fetch_worker = None
        self.refresh_tasks()
    
    def on_tasklists_error(self, error):
        print(f"Error fetching task lists: {error}")
        if self.tasklist_fetch_worker:
            self.tasklist_fetch_worker.deleteLater()
            self.tasklist_fetch_worker = None
        self.refresh_tasks()
    
    def on_tasklist_changed(self, index):
        if index >= 0:
            self.selected_tasklist_id = self.tasklist_combo.itemData(index)
            self.refresh_tasks()
    
    def show_create_dialog(self):
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, due_date = dialog.get_values()
            self.create_task(title, due_date)
    
    def show_edit_dialog(self, task):
        is_subtask = bool(task.get("parent"))
        dialog = TaskDialog(
            self, 
            title=task["title"], 
            due_date=task["due"],
            task_id=task["id"],
            tasklist_id=task["tasklist_id"],
            is_subtask=is_subtask
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.is_delete():
                self.delete_task(task["tasklist_id"], task["id"])
            elif dialog.is_create_subtask():
                self.show_subtask_dialog(task["id"])
            else:
                title, due_date = dialog.get_values()
                self.update_task(task["tasklist_id"], task["id"], title, due_date)
    
    def show_subtask_dialog(self, parent_id):
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, due_date = dialog.get_values()
            self.create_subtask(title, due_date, parent_id)
    
    def create_task(self, title, due_date):
        if self.create_worker and self.create_worker.isRunning():
            return
        
        if not self.selected_tasklist_id:
            QMessageBox.warning(self, "Error", "No task list selected")
            return
        
        self.show_loading_indicator()
        self.create_worker = TaskCreateWorker(self.credentials, self.selected_tasklist_id, title, due_date)
        self.create_worker.finished.connect(self.on_create_success)
        self.create_worker.error.connect(self.on_create_error)
        self.create_worker.start()
    
    def create_subtask(self, title, due_date, parent_id):
        if self.create_worker and self.create_worker.isRunning():
            return
        
        if not self.selected_tasklist_id:
            QMessageBox.warning(self, "Error", "No task list selected")
            return
        
        self.show_loading_indicator()
        self.create_worker = TaskCreateWorker(self.credentials, self.selected_tasklist_id, title, due_date, parent_id)
        self.create_worker.finished.connect(self.on_create_success)
        self.create_worker.error.connect(self.on_create_error)
        self.create_worker.start()
    
    def on_create_success(self):
        self.hide_loading_indicator()
        self.create_worker.deleteLater()
        self.create_worker = None
        self.refresh_tasks()
    
    def on_create_error(self, error):
        self.show_error_indicator()
        print(f"Error creating task: {error}")
        QMessageBox.critical(self, "Error", f"Failed to create task: {error}")
        if self.create_worker:
            self.create_worker.deleteLater()
            self.create_worker = None
    
    def update_task(self, tasklist_id, task_id, title, due_date):
        if self.update_worker and self.update_worker.isRunning():
            return
        
        self.update_worker = TaskUpdateWorker(self.credentials, tasklist_id, task_id, title, due_date)
        self.update_worker.finished.connect(self.on_update_success)
        self.update_worker.error.connect(self.on_update_error)
        self.update_worker.start()
    
    def on_update_success(self):
        self.update_worker.deleteLater()
        self.update_worker = None
    
    def on_update_error(self, error):
        print(f"Error updating task: {error}")
        QMessageBox.critical(self, "Error", f"Failed to update task: {error}")
        if self.update_worker:
            self.update_worker.deleteLater()
            self.update_worker = None
    
    def delete_task(self, tasklist_id, task_id):
        if self.delete_worker and self.delete_worker.isRunning():
            return
        
        self.delete_worker = TaskDeleteWorker(self.credentials, tasklist_id, task_id)
        self.delete_worker.finished.connect(self.on_delete_success)
        self.delete_worker.error.connect(self.on_delete_error)
        self.delete_worker.start()
    
    def on_delete_success(self):
        self.delete_worker.deleteLater()
        self.delete_worker = None
        self.refresh_tasks()
    
    def on_delete_error(self, error):
        print(f"Error deleting task: {error}")
        QMessageBox.critical(self, "Error", f"Failed to delete task: {error}")
        if self.delete_worker:
            self.delete_worker.deleteLater()
            self.delete_worker = None
    
    def refresh_tasks(self):
        if self.fetch_worker and self.fetch_worker.isRunning():
            return
        
        self.show_loading_indicator()
        self.fetch_worker = TaskFetchWorker(self.credentials, self.selected_tasklist_id)
        self.fetch_worker.finished.connect(self.update_tasks)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()
    
    def on_fetch_error(self, error):
        self.show_error_indicator()
        print(f"Error fetching tasks: {error}")
        if self.fetch_worker:
            self.fetch_worker.deleteLater()
            self.fetch_worker = None
        self.update_tasks([])
    
    def update_tasks(self, tasks):
        self.hide_loading_indicator()
        if self.fetch_worker:
            self.fetch_worker.deleteLater()
            self.fetch_worker = None
        
        # Clear both tabs
        for i in reversed(range(self.incomplete_layout.count())):
            widget = self.incomplete_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        for i in reversed(range(self.completed_layout.count())):
            widget = self.completed_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not tasks:
            no_tasks = QLabel("No tasks")
            no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.incomplete_layout.addWidget(no_tasks)
        else:
            # Separate incomplete and completed tasks
            incomplete_tasks = [t for t in tasks if t["status"] != "completed"]
            completed_tasks = [t for t in tasks if t["status"] == "completed"]
            
            # Add incomplete tasks to first tab
            if not incomplete_tasks:
                no_incomplete = QLabel("No active tasks")
                no_incomplete.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.incomplete_layout.addWidget(no_incomplete)
            else:
                self.add_tasks_hierarchically(incomplete_tasks, self.incomplete_layout)
            
            # Add completed tasks to second tab
            if not completed_tasks:
                no_completed = QLabel("No completed tasks")
                no_completed.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.completed_layout.addWidget(no_completed)
            else:
                self.add_tasks_hierarchically(completed_tasks, self.completed_layout)
            
            # Update tab titles with counts
            self.tab_widget.setTabText(0, f"Tasks ({len(incomplete_tasks)})")
            self.tab_widget.setTabText(1, f"Completed ({len(completed_tasks)})")
    
    def add_tasks_hierarchically(self, tasks, layout):
        # Separate parent tasks and subtasks
        parent_tasks = [t for t in tasks if not t.get("parent")]
        subtasks = [t for t in tasks if t.get("parent")]
        
        # Create a map of parent_id -> list of subtasks
        subtask_map = {}
        for subtask in subtasks:
            parent_id = subtask["parent"]
            if parent_id not in subtask_map:
                subtask_map[parent_id] = []
            subtask_map[parent_id].append(subtask)
        
        # Add parent tasks and their subtasks
        for parent_task in parent_tasks:
            # Add parent task
            task_item = TaskItem(parent_task, self.credentials, self.refresh_tasks, is_subtask=False)
            task_item.clicked.connect(self.show_edit_dialog)
            layout.addWidget(task_item)
            
            # Add subtasks if any
            if parent_task["id"] in subtask_map:
                for subtask in subtask_map[parent_task["id"]]:
                    subtask_item = TaskItem(subtask, self.credentials, self.refresh_tasks, is_subtask=True)
                    subtask_item.clicked.connect(self.show_edit_dialog)
                    layout.addWidget(subtask_item)
    
    def toggle_visibility(self):
        self.hide() if self.isVisible() else self.show()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Show loading window immediately
    loading_window = QMainWindow()
    loading_window.setWindowTitle("Google Tasks")
    loading_window.setFixedSize(300, 400)
    
    loading_widget = QWidget()
    loading_layout = QVBoxLayout(loading_widget)
    loading_label = QLabel("Authenticating...")
    loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    loading_layout.addWidget(loading_label)
    loading_window.setCentralWidget(loading_widget)
    
    screen = QApplication.primaryScreen().availableGeometry()
    loading_window.move(screen.width() - loading_window.width() - 20, screen.height() - loading_window.height() - 20)
    loading_window.show()

    main_window = None
    tray_icon = QSystemTrayIcon(QIcon.fromTheme("checkmark"), app)
    
    def on_auth_success(credentials):
        nonlocal main_window
        loading_window.close()
        main_window = MainWindow(credentials)
        main_window.show()
        tray_icon.activated.connect(lambda: main_window.toggle_visibility())
        
        menu = QMenu()
        menu.addAction("Toggle", main_window.toggle_visibility)
        menu.addAction("Quit", app.quit)
        tray_icon.setContextMenu(menu)
        tray_icon.show()
        auth_worker.deleteLater()
    
    def on_auth_error(error):
        print(f"Authentication error: {error}")
        loading_window.close()
        auth_worker.deleteLater()
        sys.exit(1)
    
    auth_worker = AuthWorker()
    auth_worker.finished.connect(on_auth_success)
    auth_worker.error.connect(on_auth_error)
    auth_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

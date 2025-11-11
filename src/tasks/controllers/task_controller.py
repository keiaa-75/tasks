from PyQt6.QtWidgets import QMessageBox, QLabel
from PyQt6.QtCore import Qt
from ..services.task_service import TaskService
from ..dialogs import TaskDialog
from ..widgets import TaskItem


class TaskController:
    def __init__(self, credentials, main_window):
        self.credentials = credentials
        self.main_window = main_window
        self.task_service = TaskService(credentials)
        self.create_worker = None
        self.update_worker = None
        self.delete_worker = None
        self.fetch_worker = None
    
    def refresh_tasks(self):
        if self.fetch_worker and self.fetch_worker.isRunning():
            return
        
        self.main_window.show_loading_indicator()
        self.fetch_worker = self.main_window.tasklist_service.fetch_tasks_worker(self.main_window.selected_tasklist_id)
        self.fetch_worker.finished.connect(self.update_tasks)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()
    
    def on_fetch_error(self, error):
        self.main_window.show_error_indicator()
        print(f"Error fetching tasks: {error}")
        if self.fetch_worker:
            self.fetch_worker.deleteLater()
            self.fetch_worker = None
        self.update_tasks([])
    
    def update_tasks(self, tasks):
        self.main_window.hide_loading_indicator()
        if self.fetch_worker:
            self.fetch_worker.deleteLater()
            self.fetch_worker = None
        
        # Clear both tabs
        self.clear_task_layouts()
        
        if not tasks:
            no_tasks = QLabel("No tasks")
            no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_window.incomplete_layout.addWidget(no_tasks)
        else:
            # Separate incomplete and completed tasks
            incomplete_tasks, completed_tasks = self.task_service.separate_by_status(tasks)
            
            # Add tasks to tabs
            self.populate_task_tab(incomplete_tasks, self.main_window.incomplete_layout, "No active tasks")
            self.populate_task_tab(completed_tasks, self.main_window.completed_layout, "No completed tasks")
            
            # Update tab titles with counts
            self.main_window.tab_widget.setTabText(0, f"Tasks ({len(incomplete_tasks)})")
            self.main_window.tab_widget.setTabText(1, f"Completed ({len(completed_tasks)})")
    
    def clear_task_layouts(self):
        for layout in [self.main_window.incomplete_layout, self.main_window.completed_layout]:
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
    
    def populate_task_tab(self, tasks, layout, empty_message):
        if not tasks:
            no_tasks = QLabel(empty_message)
            no_tasks.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_tasks)
        else:
            self.add_tasks_hierarchically(tasks, layout)
    
    def add_tasks_hierarchically(self, tasks, layout):
        parent_tasks, subtask_map = self.task_service.organize_tasks_hierarchically(tasks)
        
        for parent_task in parent_tasks:
            task_item = TaskItem(parent_task, self.credentials, self.refresh_tasks, is_subtask=False)
            task_item.clicked.connect(self.show_edit_dialog)
            layout.addWidget(task_item)
            
            if parent_task["id"] in subtask_map:
                for subtask in subtask_map[parent_task["id"]]:
                    subtask_item = TaskItem(subtask, self.credentials, self.refresh_tasks, is_subtask=True)
                    subtask_item.clicked.connect(self.show_edit_dialog)
                    layout.addWidget(subtask_item)
    
    def show_create_dialog(self):
        dialog = TaskDialog(self.main_window)
        if dialog.exec():
            title, due_date = dialog.get_values()
            self.create_task(title, due_date)
    
    def show_edit_dialog(self, task):
        is_subtask = bool(task.get("parent"))
        dialog = TaskDialog(
            self.main_window, 
            title=task["title"], 
            due_date=task["due"],
            task_id=task["id"],
            tasklist_id=task["tasklist_id"],
            is_subtask=is_subtask
        )
        if dialog.exec():
            if dialog.is_delete():
                self.delete_task(task["tasklist_id"], task["id"])
            elif dialog.is_create_subtask():
                self.show_subtask_dialog(task["id"])
            else:
                title, due_date = dialog.get_values()
                self.update_task(task["tasklist_id"], task["id"], title, due_date)
    
    def show_subtask_dialog(self, parent_id):
        dialog = TaskDialog(self.main_window)
        if dialog.exec():
            title, due_date = dialog.get_values()
            self.create_subtask(title, due_date, parent_id)
    
    def create_task(self, title, due_date):
        if self.create_worker and self.create_worker.isRunning():
            return
        
        if not self.main_window.selected_tasklist_id:
            QMessageBox.warning(self.main_window, "Error", "No task list selected")
            return
        
        try:
            self.main_window.show_loading_indicator()
            self.create_worker = self.task_service.create_task_worker(self.main_window.selected_tasklist_id, title, due_date)
            self.create_worker.finished.connect(self.on_create_success)
            self.create_worker.error.connect(self.on_create_error)
            self.create_worker.start()
        except ValueError as e:
            QMessageBox.warning(self.main_window, "Validation Error", str(e))
            self.main_window.hide_loading_indicator()
    
    def create_subtask(self, title, due_date, parent_id):
        if self.create_worker and self.create_worker.isRunning():
            return
        
        if not self.main_window.selected_tasklist_id:
            QMessageBox.warning(self.main_window, "Error", "No task list selected")
            return
        
        try:
            self.main_window.show_loading_indicator()
            self.create_worker = self.task_service.create_task_worker(self.main_window.selected_tasklist_id, title, due_date, parent_id)
            self.create_worker.finished.connect(self.on_create_success)
            self.create_worker.error.connect(self.on_create_error)
            self.create_worker.start()
        except ValueError as e:
            QMessageBox.warning(self.main_window, "Validation Error", str(e))
            self.main_window.hide_loading_indicator()
    
    def update_task(self, tasklist_id, task_id, title, due_date):
        if self.update_worker and self.update_worker.isRunning():
            return
        
        try:
            self.update_worker = self.task_service.update_task_worker(tasklist_id, task_id, title, due_date)
            self.update_worker.finished.connect(self.on_update_success)
            self.update_worker.error.connect(self.on_update_error)
            self.update_worker.start()
        except ValueError as e:
            QMessageBox.warning(self.main_window, "Validation Error", str(e))
    
    def delete_task(self, tasklist_id, task_id):
        if self.delete_worker and self.delete_worker.isRunning():
            return
        
        self.delete_worker = self.task_service.delete_task_worker(tasklist_id, task_id)
        self.delete_worker.finished.connect(self.on_delete_success)
        self.delete_worker.error.connect(self.on_delete_error)
        self.delete_worker.start()
    
    def on_create_success(self):
        self.main_window.hide_loading_indicator()
        self.create_worker.deleteLater()
        self.create_worker = None
        self.refresh_tasks()
    
    def on_create_error(self, error):
        self.main_window.show_error_indicator()
        print(f"Error creating task: {error}")
        QMessageBox.critical(self.main_window, "Error", f"Failed to create task: {error}")
        if self.create_worker:
            self.create_worker.deleteLater()
            self.create_worker = None
    
    def on_update_success(self):
        self.update_worker.deleteLater()
        self.update_worker = None
        self.refresh_tasks()  # Add refresh for updates
    
    def on_update_error(self, error):
        print(f"Error updating task: {error}")
        QMessageBox.critical(self.main_window, "Error", f"Failed to update task: {error}")
        if self.update_worker:
            self.update_worker.deleteLater()
            self.update_worker = None
    
    def on_delete_success(self):
        self.delete_worker.deleteLater()
        self.delete_worker = None
        self.refresh_tasks()
    
    def on_delete_error(self, error):
        print(f"Error deleting task: {error}")
        QMessageBox.critical(self.main_window, "Error", f"Failed to delete task: {error}")
        if self.delete_worker:
            self.delete_worker.deleteLater()
            self.delete_worker = None
    
    def show_loading(self):
        self.clear_task_layouts()
        loading = QLabel("Loading...")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_window.incomplete_layout.addWidget(loading)

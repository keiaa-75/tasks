from PyQt6.QtWidgets import QMessageBox
from ..services.task_service import TaskService
from ..dialogs import TaskDialog


class TaskController:
    def __init__(self, credentials, main_window):
        self.credentials = credentials
        self.main_window = main_window
        self.task_service = TaskService(credentials)
        self.create_worker = None
        self.update_worker = None
        self.delete_worker = None
    
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
        self.main_window.refresh_tasks()
    
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
    
    def on_update_error(self, error):
        print(f"Error updating task: {error}")
        QMessageBox.critical(self.main_window, "Error", f"Failed to update task: {error}")
        if self.update_worker:
            self.update_worker.deleteLater()
            self.update_worker = None
    
    def on_delete_success(self):
        self.delete_worker.deleteLater()
        self.delete_worker = None
        self.main_window.refresh_tasks()
    
    def on_delete_error(self, error):
        print(f"Error deleting task: {error}")
        QMessageBox.critical(self.main_window, "Error", f"Failed to delete task: {error}")
        if self.delete_worker:
            self.delete_worker.deleteLater()
            self.delete_worker = None

from PyQt6.QtWidgets import QInputDialog, QMessageBox
from ..services.tasklist_service import TaskListService


class TaskListController:
    def __init__(self, credentials, main_window):
        self.credentials = credentials
        self.main_window = main_window
        self.tasklist_service = TaskListService(credentials)
        self.tasklist_fetch_worker = None
        self.tasklist_create_worker = None
        self.tasklist_delete_worker = None
    
    def show_create_list_dialog(self):
        title, ok = QInputDialog.getText(self.main_window, "New List", "List name:")
        if ok and title.strip():
            self.create_tasklist(title.strip())
    
    def fetch_tasklists(self):
        if self.tasklist_fetch_worker and self.tasklist_fetch_worker.isRunning():
            return
        
        self.tasklist_fetch_worker = self.tasklist_service.fetch_tasklists_worker()
        self.tasklist_fetch_worker.finished.connect(self.on_tasklists_loaded)
        self.tasklist_fetch_worker.error.connect(self.on_tasklists_error)
        self.tasklist_fetch_worker.start()
    
    def create_tasklist(self, title):
        if self.tasklist_create_worker and self.tasklist_create_worker.isRunning():
            return
        
        try:
            self.main_window.show_loading_indicator()
            self.tasklist_create_worker = self.tasklist_service.create_tasklist_worker(title)
            self.tasklist_create_worker.finished.connect(self.on_tasklist_create_success)
            self.tasklist_create_worker.error.connect(self.on_tasklist_create_error)
            self.tasklist_create_worker.start()
        except ValueError as e:
            QMessageBox.warning(self.main_window, "Validation Error", str(e))
            self.main_window.hide_loading_indicator()
    
    def delete_current_list(self):
        if not self.main_window.selected_tasklist_id:
            QMessageBox.warning(self.main_window, "Error", "No task list selected")
            return
        
        if len(self.main_window.tasklists) <= 1:
            QMessageBox.warning(self.main_window, "Error", "Cannot delete the last task list")
            return
        
        current_list_name = self.main_window.tasklist_combo.currentText()
        reply = QMessageBox.question(
            self.main_window, "Confirm Delete", 
            f"Are you sure you want to delete the list '{current_list_name}'?\nAll tasks in this list will be permanently deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_tasklist(self.main_window.selected_tasklist_id)
    
    def delete_tasklist(self, tasklist_id):
        if self.tasklist_delete_worker and self.tasklist_delete_worker.isRunning():
            return
        
        self.main_window.show_loading_indicator()
        self.tasklist_delete_worker = self.tasklist_service.delete_tasklist_worker(tasklist_id)
        self.tasklist_delete_worker.finished.connect(self.on_tasklist_delete_success)
        self.tasklist_delete_worker.error.connect(self.on_tasklist_delete_error)
        self.tasklist_delete_worker.start()
    
    def on_tasklist_changed(self, index):
        if index >= 0:
            self.main_window.selected_tasklist_id = self.main_window.tasklist_combo.itemData(index)
            # Reset tab counts when switching lists
            self.main_window.tab_widget.setTabText(0, "Tasks")
            self.main_window.tab_widget.setTabText(1, "Completed")
            self.main_window.task_controller.refresh_tasks()
    
    def on_tasklists_loaded(self, tasklists):
        self.main_window.tasklists = tasklists
        self.main_window.tasklist_combo.blockSignals(True)
        self.main_window.tasklist_combo.clear()
        
        selected_index = 0
        for i, tasklist in enumerate(tasklists):
            self.main_window.tasklist_combo.addItem(tasklist["title"], tasklist["id"])
            # If we have a selected_tasklist_id, find its index
            if hasattr(self.main_window, 'selected_tasklist_id') and self.main_window.selected_tasklist_id == tasklist["id"]:
                selected_index = i
        
        if tasklists:
            if not hasattr(self.main_window, 'selected_tasklist_id') or not self.main_window.selected_tasklist_id:
                self.main_window.selected_tasklist_id = tasklists[0]["id"]
            self.main_window.tasklist_combo.setCurrentIndex(selected_index)
        
        self.main_window.tasklist_combo.blockSignals(False)
        self.tasklist_fetch_worker.deleteLater()
        self.tasklist_fetch_worker = None
        self.main_window.task_controller.refresh_tasks()
    
    def on_tasklists_error(self, error):
        print(f"Error fetching task lists: {error}")
        if self.tasklist_fetch_worker:
            self.tasklist_fetch_worker.deleteLater()
            self.tasklist_fetch_worker = None
        self.main_window.task_controller.refresh_tasks()
    
    def on_tasklist_create_success(self, new_tasklist_id):
        self.main_window.hide_loading_indicator()
        self.tasklist_create_worker.deleteLater()
        self.tasklist_create_worker = None
        # Clear tab counts immediately for new empty list
        self.main_window.tab_widget.setTabText(0, "Tasks (0)")
        self.main_window.tab_widget.setTabText(1, "Completed (0)")
        # Refresh the tasklist dropdown and select the new list
        self.main_window.selected_tasklist_id = new_tasklist_id
        self.fetch_tasklists()
    
    def on_tasklist_create_error(self, error):
        self.main_window.show_error_indicator()
        print(f"Error creating task list: {error}")
        QMessageBox.critical(self.main_window, "Error", f"Failed to create task list: {error}")
        if self.tasklist_create_worker:
            self.tasklist_create_worker.deleteLater()
            self.tasklist_create_worker = None
    
    def on_tasklist_delete_success(self):
        self.main_window.hide_loading_indicator()
        self.tasklist_delete_worker.deleteLater()
        self.tasklist_delete_worker = None
        # Refresh the tasklist dropdown
        self.fetch_tasklists()
    
    def on_tasklist_delete_error(self, error):
        self.main_window.show_error_indicator()
        print(f"Error deleting task list: {error}")
        QMessageBox.critical(self.main_window, "Error", f"Failed to delete task list: {error}")
        if self.tasklist_delete_worker:
            self.tasklist_delete_worker.deleteLater()
            self.tasklist_delete_worker = None

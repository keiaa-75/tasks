from datetime import datetime
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox
from PyQt6.QtCore import Qt


class TaskDialog(QDialog):
    def __init__(self, parent=None, title="", due_date="", task_id=None, tasklist_id=None, is_subtask=False):
        super().__init__(parent)
        self.is_edit_mode = task_id is not None
        self.task_id = task_id
        self.tasklist_id = tasklist_id
        self.is_subtask = is_subtask
        self.delete_requested = False
        self.create_subtask_requested = False
        
        self.setWindowTitle("Edit Task" if self.is_edit_mode else "New Task")
        self.setModal(True)
        self.setFixedWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        title_label = QLabel("Title:")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task title")
        self.title_input.setText(title)
        layout.addWidget(self.title_input)
        
        date_label = QLabel("Due Date (YYYY-MM-DD):")
        layout.addWidget(date_label)
        
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Optional (clear to remove)")
        if due_date and due_date != "No Due Date":
            try:
                dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                self.date_input.setText(dt.strftime("%Y-%m-%d"))
            except:
                pass
        layout.addWidget(self.date_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        
        # Remove icon from OK button
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setIcon(ok_button.style().standardIcon(ok_button.style().StandardPixmap.SP_CustomBase))
        
        if self.is_edit_mode:
            delete_button = buttons.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_button.clicked.connect(self.confirm_delete)
            
            # Add subtask button only for parent tasks (not subtasks)
            if not self.is_subtask:
                subtask_button = buttons.addButton("Subtask", QDialogButtonBox.ButtonRole.ActionRole)
                subtask_button.clicked.connect(self.create_subtask)
        
        layout.addWidget(buttons)
    
    def create_subtask(self):
        self.create_subtask_requested = True
        self.accept()
    
    def confirm_delete(self):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this task?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested = True
            self.accept()
    
    def validate_and_accept(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Title is required")
            return
        
        due_date = self.date_input.text().strip()
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Invalid date format. Use YYYY-MM-DD")
                return
        
        self.accept()
    
    def get_values(self):
        title = self.title_input.text().strip()
        due_date = self.date_input.text().strip() or None
        return title, due_date
    
    def is_delete(self):
        return self.delete_requested
    
    def is_create_subtask(self):
        return self.create_subtask_requested

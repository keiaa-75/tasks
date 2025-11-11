from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QDialog, QLineEdit, QDialogButtonBox, QMessageBox
from PyQt6.QtCore import Qt
from .workers import TaskCompleteWorker


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


class CreateTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Task")
        self.setModal(True)
        self.setFixedWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        title_label = QLabel("Title:")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task title")
        layout.addWidget(self.title_input)
        
        date_label = QLabel("Due Date (YYYY-MM-DD):")
        layout.addWidget(date_label)
        
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Optional")
        layout.addWidget(self.date_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
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

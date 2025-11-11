from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QDialog, QLineEdit, QDialogButtonBox, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from .workers import TaskCompleteWorker


class TaskItem(QWidget):
    clicked = pyqtSignal(dict)
    
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
                background-color: rgb(50, 50, 50);
                border: 1px solid rgb(150, 150, 150);
            }
            QCheckBox::indicator:checked {
                background-color: rgb(100, 150, 255);
                border: 1px solid rgb(100, 150, 255);
            }
        """)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        is_completed = task["status"] == "completed"
        title_style = "color: rgb(150, 150, 150); text-decoration: line-through;" if is_completed else "color: white;"
        
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
            
            due_style = "color: rgb(100, 100, 100);" if is_completed else "color: rgb(180, 180, 180);"
            due_label = QLabel(formatted_date)
            due_label.setStyleSheet(f"{due_style} font-size: 12px;")
            content_layout.addWidget(due_label)
        
        layout.addLayout(content_layout, 1)
        
        self.setStyleSheet("TaskItem { background-color: rgb(40, 40, 40); margin: 2px; }")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is not on checkbox
            if not self.checkbox.geometry().contains(event.pos()):
                self.clicked.emit(self.task)
        super().mousePressEvent(event)
    
    def on_checkbox_changed(self, state):
        if state == Qt.CheckState.Checked.value and self.task["status"] != "completed":
            self.checkbox.setEnabled(False)
            self.title_label.setStyleSheet("color: rgb(120, 120, 120); font-size: 14px;")
            
            self.complete_worker = TaskCompleteWorker(
                self.credentials, self.task["tasklist_id"], self.task["id"], self.task["title"]
            )
            self.complete_worker.finished.connect(self.on_complete_success)
            self.complete_worker.error.connect(self.on_complete_error)
            self.complete_worker.start()
    
    def on_complete_success(self):
        self.refresh_callback()
        if self.complete_worker:
            self.complete_worker.deleteLater()
    
    def on_complete_error(self, error):
        print(f"Error completing task: {error}")
        self.checkbox.setChecked(False)
        self.checkbox.setEnabled(True)
        self.title_label.setStyleSheet("color: white; font-size: 14px;")
        if self.complete_worker:
            self.complete_worker.deleteLater()


class TaskDialog(QDialog):
    def __init__(self, parent=None, title="", due_date="", task_id=None, tasklist_id=None):
        super().__init__(parent)
        self.is_edit_mode = task_id is not None
        self.task_id = task_id
        self.tasklist_id = tasklist_id
        self.delete_requested = False
        
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
        
        if self.is_edit_mode:
            delete_button = buttons.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_button.clicked.connect(self.confirm_delete)
        
        layout.addWidget(buttons)
    
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

from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QDialog, QLineEdit, QDialogButtonBox, QMessageBox, QFrame, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from .workers import TaskCompleteWorker, TaskUncompleteWorker


class CollapsibleSection(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header = QPushButton(title)
        self.header.setCheckable(True)
        self.header.setChecked(False)
        self.header.clicked.connect(self.toggle_content)
        layout.addWidget(self.header)
        
        # Content area
        self.content_area = QFrame()
        self.content_area.setVisible(False)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(2)
        layout.addWidget(self.content_area)
    
    def toggle_content(self):
        self.content_area.setVisible(self.header.isChecked())
    
    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
    
    def set_title(self, title):
        self.header.setText(title)


class TaskItem(QWidget):
    clicked = pyqtSignal(dict)
    
    def __init__(self, task, credentials, refresh_callback, is_subtask=False):
        super().__init__()
        self.task = task
        self.credentials = credentials
        self.refresh_callback = refresh_callback
        self.complete_worker = None
        self.uncomplete_worker = None
        
        layout = QHBoxLayout(self)
        
        # Add indentation for subtasks
        if is_subtask:
            layout.setContentsMargins(24, 8, 8, 8)  # Extra left margin for subtasks
        else:
            layout.setContentsMargins(8, 8, 8, 8)
            
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task["status"] == "completed")
        self.checkbox.setFixedSize(16, 16)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        is_completed = task["status"] == "completed"
        
        self.title_label = QLabel(task["title"])
        if is_completed:
            font = self.title_label.font()
            font.setStrikeOut(True)
            self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        content_layout.addWidget(self.title_label)
        
        if task["due"] and task["due"] != "No Due Date":
            try:
                dt = datetime.fromisoformat(task["due"].replace('Z', '+00:00'))
                formatted_date = dt.strftime("%Y-%m-%d")
            except:
                formatted_date = "Invalid date"
            
            due_label = QLabel(formatted_date)
            content_layout.addWidget(due_label)
        
        layout.addLayout(content_layout, 1)
        
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
            # Optimistic update
            self.task["status"] = "completed"
            self.update_appearance()
            
            self.complete_worker = TaskCompleteWorker(
                self.credentials, self.task["tasklist_id"], self.task["id"], self.task["title"], self.task.get("due")
            )
            self.complete_worker.finished.connect(self.on_complete_success)
            self.complete_worker.error.connect(self.on_complete_error)
            self.complete_worker.start()
        elif state == Qt.CheckState.Unchecked.value and self.task["status"] == "completed":
            self.checkbox.setEnabled(False)
            # Optimistic update
            self.task["status"] = "needsAction"
            self.update_appearance()
            
            self.uncomplete_worker = TaskUncompleteWorker(
                self.credentials, self.task["tasklist_id"], self.task["id"], self.task["title"], self.task.get("due")
            )
            self.uncomplete_worker.finished.connect(self.on_uncomplete_success)
            self.uncomplete_worker.error.connect(self.on_uncomplete_error)
            self.uncomplete_worker.start()
    
    def update_appearance(self):
        is_completed = self.task["status"] == "completed"
        font = self.title_label.font()
        font.setStrikeOut(is_completed)
        self.title_label.setFont(font)
    
    def on_complete_success(self):
        self.checkbox.setEnabled(True)
        if self.complete_worker:
            self.complete_worker.deleteLater()
    
    def on_complete_error(self, error):
        print(f"Error completing task: {error}")
        # Revert optimistic update
        self.task["status"] = "needsAction"
        self.checkbox.setChecked(False)
        self.checkbox.setEnabled(True)
        self.update_appearance()
        if self.complete_worker:
            self.complete_worker.deleteLater()
    
    def on_uncomplete_success(self):
        self.checkbox.setEnabled(True)
        if self.uncomplete_worker:
            self.uncomplete_worker.deleteLater()
    
    def on_uncomplete_error(self, error):
        print(f"Error uncompleting task: {error}")
        # Revert optimistic update
        self.task["status"] = "completed"
        self.checkbox.setChecked(True)
        self.checkbox.setEnabled(True)
        self.update_appearance()
        if self.uncomplete_worker:
            self.uncomplete_worker.deleteLater()


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
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.validate_and_accept)
        
        # Remove icon from OK button
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setIcon(ok_button.style().standardIcon(ok_button.style().StandardPixmap.SP_CustomBase))
        
        if self.is_edit_mode:
            # Add subtask button first (will appear between OK and Delete)
            if not self.is_subtask:
                subtask_button = buttons.addButton("Subtask", QDialogButtonBox.ButtonRole.ActionRole)
                subtask_button.clicked.connect(self.create_subtask)
            
            delete_button = buttons.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_button.clicked.connect(self.confirm_delete)
        
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

from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFrame, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from .services.task_service import TaskService


class CollapsibleSection(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header = QPushButton(title)
        self.header.setCheckable(True)
        self.header.setChecked(False)
        self.header.clicked.connect(self.toggle_content)
        layout.addWidget(self.header)
        
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
        self.task_service = TaskService(credentials)
        self.complete_worker = None
        self.uncomplete_worker = None
        
        layout = QHBoxLayout(self)
        
        if is_subtask:
            layout.setContentsMargins(24, 8, 8, 8)
        else:
            layout.setContentsMargins(8, 8, 8, 8)
            
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task["status"] == "completed")
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
            if not self.checkbox.geometry().contains(event.pos()):
                self.clicked.emit(self.task)
        super().mousePressEvent(event)
    
    def on_checkbox_changed(self, state):
        if state == Qt.CheckState.Checked.value and self.task["status"] != "completed":
            self.checkbox.setEnabled(False)
            self.task["status"] = "completed"
            self.update_appearance()
            
            self.complete_worker = self.task_service.complete_task_worker(self.task)
            self.complete_worker.finished.connect(self.on_complete_success)
            self.complete_worker.error.connect(self.on_complete_error)
            self.complete_worker.start()
        elif state == Qt.CheckState.Unchecked.value and self.task["status"] == "completed":
            self.checkbox.setEnabled(False)
            self.task["status"] = "needsAction"
            self.update_appearance()
            
            self.uncomplete_worker = self.task_service.uncomplete_task_worker(self.task)
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

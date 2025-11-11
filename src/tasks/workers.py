from PyQt6.QtCore import QThread, pyqtSignal
from . import auth, tasks_api


class AuthWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            credentials = auth.get_credentials()
            self.finished.emit(credentials)
        except Exception as e:
            self.error.emit(str(e))


class TaskListFetchWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
    
    def run(self):
        try:
            tasklists = tasks_api.fetch_tasklists(self.credentials)
            self.finished.emit(tasklists)
        except Exception as e:
            self.error.emit(str(e))


class TaskFetchWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, credentials, tasklist_id=None):
        super().__init__()
        self.credentials = credentials
        self.tasklist_id = tasklist_id
    
    def run(self):
        try:
            tasks = tasks_api.fetch_tasks(self.credentials, self.tasklist_id)
            self.finished.emit(tasks)
        except Exception as e:
            self.error.emit(str(e))


class TaskCompleteWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, credentials, tasklist_id, task_id, title, due_date=None):
        super().__init__()
        self.credentials = credentials
        self.tasklist_id = tasklist_id
        self.task_id = task_id
        self.title = title
        self.due_date = due_date
    
    def run(self):
        try:
            tasks_api.complete_task(self.credentials, self.tasklist_id, self.task_id, self.title, self.due_date)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class TaskUncompleteWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, credentials, tasklist_id, task_id, title, due_date=None):
        super().__init__()
        self.credentials = credentials
        self.tasklist_id = tasklist_id
        self.task_id = task_id
        self.title = title
        self.due_date = due_date
    
    def run(self):
        try:
            tasks_api.uncomplete_task(self.credentials, self.tasklist_id, self.task_id, self.title, self.due_date)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class TaskCreateWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, credentials, tasklist_id, title, due_date):
        super().__init__()
        self.credentials = credentials
        self.tasklist_id = tasklist_id
        self.title = title
        self.due_date = due_date
    
    def run(self):
        try:
            tasks_api.create_task(self.credentials, self.tasklist_id, self.title, self.due_date)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class TaskUpdateWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, credentials, tasklist_id, task_id, title, due_date):
        super().__init__()
        self.credentials = credentials
        self.tasklist_id = tasklist_id
        self.task_id = task_id
        self.title = title
        self.due_date = due_date
    
    def run(self):
        try:
            tasks_api.update_task(self.credentials, self.tasklist_id, self.task_id, self.title, self.due_date)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class TaskDeleteWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, credentials, tasklist_id, task_id):
        super().__init__()
        self.credentials = credentials
        self.tasklist_id = tasklist_id
        self.task_id = task_id
    
    def run(self):
        try:
            tasks_api.delete_task(self.credentials, self.tasklist_id, self.task_id)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

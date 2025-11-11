from .. import tasks_api
from ..workers import TaskCreateWorker, TaskUpdateWorker, TaskDeleteWorker, TaskCompleteWorker, TaskUncompleteWorker

class TaskService:
    def __init__(self, credentials):
        self.credentials = credentials
    
    def create_task_worker(self, tasklist_id, title, due_date, parent_id=None):
        if not title.strip():
            raise ValueError("Task title is required")
        return TaskCreateWorker(self.credentials, tasklist_id, title.strip(), due_date, parent_id)
    
    def update_task_worker(self, tasklist_id, task_id, title, due_date):
        if not title.strip():
            raise ValueError("Task title is required")
        return TaskUpdateWorker(self.credentials, tasklist_id, task_id, title.strip(), due_date)
    
    def delete_task_worker(self, tasklist_id, task_id):
        """Create a worker for task deletion"""
        return TaskDeleteWorker(self.credentials, tasklist_id, task_id)
    
    def complete_task_worker(self, task):
        return TaskCompleteWorker(
            self.credentials, 
            task["tasklist_id"], 
            task["id"], 
            task["title"], 
            task.get("due")
        )
    
    def uncomplete_task_worker(self, task):
        return TaskUncompleteWorker(
            self.credentials, 
            task["tasklist_id"], 
            task["id"], 
            task["title"], 
            task.get("due")
        )
    
    def organize_tasks_hierarchically(self, tasks):
        parent_tasks = [t for t in tasks if not t.get("parent")]
        subtasks = [t for t in tasks if t.get("parent")]
        
        # Create a map of parent_id -> list of subtasks
        subtask_map = {}
        for subtask in subtasks:
            parent_id = subtask["parent"]
            if parent_id not in subtask_map:
                subtask_map[parent_id] = []
            subtask_map[parent_id].append(subtask)
        
        return parent_tasks, subtask_map
    
    def separate_by_status(self, tasks):
        incomplete = [t for t in tasks if t["status"] != "completed"]
        completed = [t for t in tasks if t["status"] == "completed"]
        return incomplete, completed

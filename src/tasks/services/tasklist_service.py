from ..workers import TaskListFetchWorker, TaskListCreateWorker, TaskFetchWorker


class TaskListService:
    def __init__(self, credentials):
        self.credentials = credentials
    
    def fetch_tasklists_worker(self):
        return TaskListFetchWorker(self.credentials)
    
    def create_tasklist_worker(self, title):
        if not title.strip():
            raise ValueError("List name is required")
        return TaskListCreateWorker(self.credentials, title.strip())
    
    def fetch_tasks_worker(self, tasklist_id):
        return TaskFetchWorker(self.credentials, tasklist_id)
    
    def find_tasklist_index(self, tasklists, target_id):
        for i, tasklist in enumerate(tasklists):
            if tasklist["id"] == target_id:
                return i
        return 0

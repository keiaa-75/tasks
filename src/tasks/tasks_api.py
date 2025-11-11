from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_tasklists(credentials):
    """Fetches task lists from the Google Tasks API."""
    service = build("tasks", "v1", credentials=credentials)
    tasklists_result = service.tasklists().list().execute()
    return tasklists_result.get("items", [])

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_tasks(credentials, tasklist_id=None):
    """Fetches tasks from the Google Tasks API with exponential backoff."""
    service = build("tasks", "v1", credentials=credentials)

    # Fetch the user's task lists
    tasklists_result = service.tasklists().list().execute()
    tasklists = tasklists_result.get("items", [])

    all_tasks = []
    if tasklists:
        # Filter by specific list if provided
        lists_to_fetch = [tl for tl in tasklists if tl["id"] == tasklist_id] if tasklist_id else tasklists
        
        for tasklist in lists_to_fetch:
            # Fetch tasks from each task list
            tasks_result = service.tasks().list(tasklist=tasklist["id"], showCompleted=True).execute()
            tasks = tasks_result.get("items", [])
            for task in tasks:
                all_tasks.append(
                    {
                        "id": task.get("id"),
                        "tasklist_id": tasklist["id"],
                        "title": task.get("title", "No Title"),
                        "due": task.get("due", "No Due Date"),
                        "status": task.get("status", "needsAction"),
                    }
                )
    return all_tasks

def complete_task(credentials, tasklist_id, task_id, title):
    service = build("tasks", "v1", credentials=credentials)
    task_body = {"id": task_id, "title": title, "status": "completed"}
    service.tasks().update(tasklist=tasklist_id, task=task_id, body=task_body).execute()

def uncomplete_task(credentials, tasklist_id, task_id, title):
    service = build("tasks", "v1", credentials=credentials)
    task_body = {"id": task_id, "title": title, "status": "needsAction"}
    service.tasks().update(tasklist=tasklist_id, task=task_id, body=task_body).execute()

def create_task(credentials, tasklist_id, title, due_date=None):
    service = build("tasks", "v1", credentials=credentials)
    
    task_body = {"title": title}
    if due_date:
        task_body["due"] = f"{due_date}T00:00:00.000Z"
    
    service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()

def update_task(credentials, tasklist_id, task_id, title, due_date=None):
    service = build("tasks", "v1", credentials=credentials)
    
    task_body = {"id": task_id, "title": title}
    if due_date:
        task_body["due"] = f"{due_date}T00:00:00.000Z"
    else:
        task_body["due"] = None
    
    service.tasks().update(tasklist=tasklist_id, task=task_id, body=task_body).execute()

def delete_task(credentials, tasklist_id, task_id):
    service = build("tasks", "v1", credentials=credentials)
    service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()

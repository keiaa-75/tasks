from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_tasks(credentials):
    """Fetches tasks from the Google Tasks API with exponential backoff."""
    service = build("tasks", "v1", credentials=credentials)

    # Fetch the user's task lists
    tasklists_result = service.tasklists().list().execute()
    tasklists = tasklists_result.get("items", [])

    all_tasks = []
    if tasklists:
        for tasklist in tasklists:
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
    """Marks a task as completed."""
    service = build("tasks", "v1", credentials=credentials)
    task_body = {"id": task_id, "title": title, "status": "completed"}
    service.tasks().update(tasklist=tasklist_id, task=task_id, body=task_body).execute()

def create_task(credentials, title, due_date=None):
    """Creates a new task in the default task list."""
    service = build("tasks", "v1", credentials=credentials)
    
    # Get default task list
    tasklists_result = service.tasklists().list().execute()
    tasklists = tasklists_result.get("items", [])
    if not tasklists:
        raise Exception("No task lists found")
    
    tasklist_id = tasklists[0]["id"]
    
    task_body = {"title": title}
    if due_date:
        task_body["due"] = f"{due_date}T00:00:00.000Z"
    
    service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()

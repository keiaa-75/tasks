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
            tasks_result = service.tasks().list(tasklist=tasklist["id"]).execute()
            tasks = tasks_result.get("items", [])
            for task in tasks:
                all_tasks.append(
                    {
                        "title": task.get("title", "No Title"),
                        "due": task.get("due", "No Due Date"),
                    }
                )
    return all_tasks

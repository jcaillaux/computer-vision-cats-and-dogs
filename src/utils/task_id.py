import uuid

def generate_task_id() -> str:
    """Generate a unique task ID using UUID4."""
    return str(uuid.uuid4())
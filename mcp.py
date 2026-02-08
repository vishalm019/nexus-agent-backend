import psycopg2
from db_config import DB_CONFIG

def execute_query(query, params = None, fetch=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        print(query,params)
        cur.execute(query, params)
        conn.commit()
        if fetch:
            result = cur.fetchall()
        else:
            result = None
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def update_task(user_id, task_title, status=None, priority=None, description=None):
    updates = []
    values = []

    if status:
        updates.append("status = %s")
        values.append(status)
    if priority:
        updates.append("priority = %s")
        values.append(priority)
    if description:
        updates.append("description = %s")
        values.append(description)

    values.extend([task_title, user_id])

    query = f"""UPDATE tasks SET {", ".join(updates)} WHERE title ILIKE %s AND userid = %s"""
    execute_query(query, tuple(values))

def create_tasks(user_id, title, description=None, priority=2, due_date=None):
    print('hooo')
    query = """INSERT INTO tasks (title, description, priority, due_date, status, userid) VALUES (%s, %s, %s, %s, %s, %s)"""
    values = (title,description,priority,due_date,"Pending",user_id)
    execute_query(query, values)

def delete_task(user_id, task_title):
    query = """DELETE FROM tasks WHERE title ILIKE %s AND userid = %s"""
    values = (task_title, user_id)
    execute_query(query, values)


mcp_tools = [
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update an existing task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_title": {"type": "string"},
                    "status": {"type": "string"},
                    "priority": {"type": "integer"},
                    "description": {"type": "string"}
                },
                "required": ["task_title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_tasks",
            "description": "Create a new task",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "integer"},
                    "due_date": {"type": "string"}
                },
                "required": ["title", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete an existing task by title",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_title": {"type": "string"},
                },
                "required": ["task_title"]
            }
        }
    }
]


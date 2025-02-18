import sqlite3
from config import DATABASE_NAME

def create_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_text TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tasks (
            user_id INTEGER PRIMARY KEY,
            task_id INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            completed_tasks INTEGER DEFAULT 0
        )
    """)

    conn.commit()

def get_all_user_ids(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_stats")
    return [row[0] for row in cursor.fetchall()]

def add_user_to_stats(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_active_task(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT task_id FROM user_tasks WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result

def get_random_task(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_text FROM tasks ORDER BY RANDOM() LIMIT 1")
    task = cursor.fetchone()
    return task

def add_task_to_user(conn, user_id, task_id):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_tasks (user_id, task_id) VALUES (?, ?)", (user_id, task_id))
    conn.commit()

def update_user_stats(conn, user_id, increment):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_stats
        SET completed_tasks = MAX(0, completed_tasks + ?)
        WHERE user_id = ?
    """, (increment, user_id))
    conn.commit()

def delete_task_from_user(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_tasks WHERE user_id = ?", (user_id,))
    conn.commit()

def get_user_stats(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT completed_tasks FROM user_stats WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def add_task(conn, task_text: str):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task_text) VALUES (?)", (task_text,))
    conn.commit()

def delete_task(conn, task_id: int):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()

def get_task_by_id(conn, task_id: int):
    cursor = conn.cursor()
    cursor.execute("SELECT task_text FROM tasks WHERE id = ?", (task_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_all_tasks(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_text FROM tasks")
    return cursor.fetchall()

def get_user_stats(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT completed_tasks FROM user_stats WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_stats WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_top_users(conn, limit=10):
    """
    Возвращает топ пользователей по количеству выполненных заданий.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, completed_tasks FROM user_stats ORDER BY completed_tasks DESC LIMIT ?", (limit,))
    top_users = cursor.fetchall()
    return top_users
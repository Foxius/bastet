import sqlite3
from config import DATABASE_NAME

def create_connection():
    """
    Создает и возвращает соединение с базой данных.

    :return: Объект соединения с базой данных SQLite.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

def create_tables(conn):
    """
    Создает необходимые таблицы в базе данных, если они еще не существуют.

    :param conn: Объект соединения с базой данных.
    """
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
    """
    Получает список всех пользователей из таблицы статистики.

    :param conn: Объект соединения с базой данных.
    :return: Список идентификаторов пользователей.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_stats")
    return [row[0] for row in cursor.fetchall()]

def add_user_to_stats(conn, user_id):
    """
    Добавляет пользователя в таблицу статистики, если он еще не существует.

    :param conn: Объект соединения с базой данных.
    :param user_id: Идентификатор пользователя.
    """
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_active_task(conn, user_id):
    """
    Получает активное задание для указанного пользователя.

    :param conn: Объект соединения с базой данных.
    :param user_id: Идентификатор пользователя.
    :return: Идентификатор задания, если оно есть; иначе None.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT task_id FROM user_tasks WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result

def get_random_task(conn):
    """
    Получает случайное задание из таблицы заданий.

    :param conn: Объект соединения с базой данных.
    :return: Кортеж (id, текст задания) или None, если заданий нет.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_text FROM tasks ORDER BY RANDOM() LIMIT 1")
    task = cursor.fetchone()
    return task

def add_task_to_user(conn, user_id, task_id):
    """
    Присваивает задание пользователю.

    :param conn: Объект соединения с базой данных.
    :param user_id: Идентификатор пользователя.
    :param task_id: Идентификатор задания.
    """
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_tasks (user_id, task_id) VALUES (?, ?)", (user_id, task_id))
    conn.commit()

def update_user_stats(conn, user_id, increment):
    """
    Обновляет статистику пользователя по количеству выполненных заданий.

    :param conn: Объект соединения с базой данных.
    :param user_id: Идентификатор пользователя.
    :param increment: Количество выполненных заданий для добавления или вычитания.
    """
    cursor = conn.cursor()
    cursor.execute("""
       UPDATE user_stats
       SET completed_tasks = MAX(0, completed_tasks + ?)
       WHERE user_id = ?
    """, (increment, user_id))
    conn.commit()

def delete_task_from_user(conn, user_id):
   """
   Удаляет все задания у указанного пользователя.

   :param conn: Объект соединения с базой данных.
   :param user_id: Идентификатор пользователя.
   """
   cursor = conn.cursor()
   cursor.execute("DELETE FROM user_tasks WHERE user_id = ?", (user_id,))
   conn.commit()

def get_user_stats(conn, user_id):
   """
   Получает статистику пользователя по количеству выполненных заданий.

   :param conn: Объект соединения с базой данных.
   :param user_id: Идентификатор пользователя.
   :return: Количество выполненных заданий или 0, если пользователь не найден.
   """
   cursor = conn.cursor()
   cursor.execute("SELECT completed_tasks FROM user_stats WHERE user_id = ?", (user_id,))
   result = cursor.fetchone()
   return result[0] if result else 0

def add_task(conn, task_text: str):
   """
   Добавляет новое задание в таблицу заданий.

   :param conn: Объект соединения с базой данных.
   :param task_text: Текст задания для добавления в базу данных.
   """
   cursor = conn.cursor()
   cursor.execute("INSERT INTO tasks (task_text) VALUES (?)", (task_text,))
   conn.commit()

def delete_task(conn, task_id: int):
   """
   Удаляет задание из таблицы заданий по его идентификатору.

   :param conn: Объект соединения с базой данных.
   :param task_id: Идентификатор задания для удаления.
   """
   cursor = conn.cursor()
   cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
   conn.commit()

def get_task_by_id(conn, task_id: int):
   """
   Получает текст задания по его идентификатору.

   :param conn: Объект соединения с базой данных.
   :param task_id: Идентификатор задания.
   :return: Текст задания или None, если задание не найдено.
   """
   cursor = conn.cursor()
   cursor.execute("SELECT task_text FROM tasks WHERE id = ?", (task_id,))
   result = cursor.fetchone()
   return result[0] if result else None

def get_all_tasks(conn):
   """
   Получает все задания из таблицы заданий.

   :param conn: Объект соединения с базой данных.
   :return: Список кортежей (id, текст задания).
   """
   cursor = conn.cursor()
   cursor.execute("SELECT id, task_text FROM tasks")
   return cursor.fetchall()

def get_top_users(conn, limit=10):
     """
     Возвращает топ пользователей по количеству выполненных заданий.

     :param conn: Объект соединения с базой данных.
     :param limit: Максимальное количество пользователей для возврата (по умолчанию 10).
     :return: Список кортежей (user_id, completed_tasks).
     """
     cursor = conn.cursor()
     cursor.execute("SELECT user_id, completed_tasks FROM user_stats ORDER BY completed_tasks DESC LIMIT ?", (limit,))
     top_users = cursor.fetchall()
     return top_users

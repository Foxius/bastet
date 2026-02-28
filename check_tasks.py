#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import create_connection, get_all_tasks

def main():
    """Показывает все задания из базы данных"""
    try:
        # Подключаемся к базе данных
        conn = create_connection()
        
        # Получаем все задания
        tasks = get_all_tasks(conn)
        
        print(f"Всего заданий в базе данных: {len(tasks)}")
        print("-" * 50)
        
        for task_id, task_text in tasks:
            print(f"ID {task_id}: {task_text}")
            print("-" * 50)
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при получении заданий: {e}")

if __name__ == "__main__":
    main()

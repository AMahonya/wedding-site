#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль инициализации базы данных для свадебного сайта.
Создаёт таблицу для хранения ответов гостей (RSVP).
"""

import sqlite3
import os
import sys
from datetime import datetime

# Конфигурация базы данных
DATABASE_FILE = 'wedding.db'
DATABASE_SCHEMA_VERSION = 1


def get_db_connection(db_file):
    """
    Устанавливает соединение с базой данных.

    Args:
        db_file (str): Путь к файлу базы данных

    Returns:
        sqlite3.Connection: Объект соединения с БД
    """
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        sys.exit(1)


def check_existing_database(db_file):
    """
    Проверяет, существует ли уже база данных.

    Args:
        db_file (str): Путь к файлу базы данных

    Returns:
        bool: True если БД существует, иначе False
    """
    return os.path.exists(db_file)


def backup_database(db_file):
    """
    Создаёт резервную копию существующей базы данных.

    Args:
        db_file (str): Путь к файлу базы данных
    """
    if not check_existing_database(db_file):
        return

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{db_file}.backup_{timestamp}"

    try:
        import shutil
        shutil.copy2(db_file, backup_file)
        print(f"📦 Создана резервная копия: {backup_file}")
    except Exception as e:
        print(f"⚠️ Не удалось создать резервную копию: {e}")


def table_exists(cursor, table_name):
    """
    Проверяет существование таблицы в базе данных.

    Args:
        cursor: Курсор SQLite
        table_name (str): Имя таблицы

    Returns:
        bool: True если таблица существует, иначе False
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def create_rsvp_table(cursor):
    """
    Создаёт таблицу для ответов гостей.

    Args:
        cursor: Курсор SQLite
    """
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS rsvp_responses
                   (
                       id                INTEGER PRIMARY KEY AUTOINCREMENT,
                       guest_name        TEXT NOT NULL,
                       attending         TEXT NOT NULL CHECK (attending IN ('yes', 'no')),
                       guests_count      INTEGER   DEFAULT 1 CHECK (guests_count BETWEEN 1 AND 10),
                       gift_type         TEXT      DEFAULT 'money',
                       message           TEXT,
                       food_no_meat      BOOLEAN   DEFAULT 0,
                       food_no_fish      BOOLEAN   DEFAULT 0,
                       food_vegan        BOOLEAN   DEFAULT 0,
                       alcohol_red       BOOLEAN   DEFAULT 0,
                       alcohol_white     BOOLEAN   DEFAULT 0,
                       alcohol_champagne BOOLEAN   DEFAULT 0,
                       alcohol_whiskey   BOOLEAN   DEFAULT 0,
                       alcohol_vodka     BOOLEAN   DEFAULT 0,
                       alcohol_none      BOOLEAN   DEFAULT 0,
                       created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')


def create_indexes(cursor):
    """
    Создаёт индексы для ускорения запросов.

    Args:
        cursor: Курсор SQLite
    """
    # Индекс для быстрого поиска по дате
    cursor.execute('''
                   CREATE INDEX IF NOT EXISTS idx_created_at
                       ON rsvp_responses (created_at DESC)
                   ''')

    # Индекс для фильтрации по присутствию
    cursor.execute('''
                   CREATE INDEX IF NOT EXISTS idx_attending
                       ON rsvp_responses (attending)
                   ''')

    # Индекс для поиска по имени
    cursor.execute('''
                   CREATE INDEX IF NOT EXISTS idx_guest_name
                       ON rsvp_responses (guest_name)
                   ''')

    print("✅ Индексы созданы")


def get_table_info(cursor):
    """
    Получает информацию о таблице.

    Args:
        cursor: Курсор SQLite

    Returns:
        dict: Информация о таблице
    """
    cursor.execute("PRAGMA table_info(rsvp_responses)")
    columns = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM rsvp_responses")
    row_count = cursor.fetchone()[0]

    return {
        'columns': len(columns),
        'rows': row_count,
        'exists': True
    }


def show_statistics(cursor):
    """
    Показывает статистику базы данных.

    Args:
        cursor: Курсор SQLite
    """
    cursor.execute("SELECT COUNT(*) FROM rsvp_responses")
    total = cursor.fetchone()[0]

    if total > 0:
        cursor.execute(
            "SELECT COUNT(*) FROM rsvp_responses WHERE attending = 'yes'"
        )
        attending = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM rsvp_responses WHERE attending = 'no'"
        )
        not_attending = cursor.fetchone()[0]

        print(f"\n📊 Статистика базы данных:")
        print(f"   • Всего ответов: {total}")
        print(f"   • Придут: {attending}")
        print(f"   • Не придут: {not_attending}")


def init_db(force=False, backup=True):
    """
    Инициализирует базу данных.

    Args:
        force (bool): Принудительное пересоздание таблицы
        backup (bool): Создавать резервную копию
    """
    print("🚀 Начало инициализации базы данных...")

    # Проверяем существование БД
    if check_existing_database(DATABASE_FILE):
        print(f"📁 База данных '{DATABASE_FILE}' уже существует")

        if backup:
            backup_database(DATABASE_FILE)

        if force:
            print("⚠️ Принудительное пересоздание таблицы...")
            # Удаляем старую таблицу
            conn = get_db_connection(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS rsvp_responses")
            conn.commit()
            conn.close()
        else:
            print("ℹ️ Использую существующую базу данных")
            # Проверяем структуру существующей таблицы
            conn = get_db_connection(DATABASE_FILE)
            cursor = conn.cursor()
            if table_exists(cursor, 'rsvp_responses'):
                info = get_table_info(cursor)
                print(f"   • Колонок: {info['columns']}")
                print(f"   • Записей: {info['rows']}")
                show_statistics(cursor)
            conn.close()
            return

    # Создаём новую таблицу
    conn = get_db_connection(DATABASE_FILE)
    cursor = conn.cursor()

    try:
        # Создаём таблицу
        create_rsvp_table(cursor)
        print("✅ Таблица 'rsvp_responses' создана")

        # Создаём индексы
        create_indexes(cursor)

        # Сохраняем изменения
        conn.commit()

        # Показываем информацию о созданной таблице
        info = get_table_info(cursor)
        print(f"\n📋 Информация о таблице:")
        print(f"   • Название: rsvp_responses")
        print(f"   • Колонок: {info['columns']}")
        print(f"   • Пустая таблица")

        print(f"\n💾 База данных сохранена: {DATABASE_FILE}")
        print(f"📊 Размер файла: {os.path.getsize(DATABASE_FILE)} байт")

    except sqlite3.Error as e:
        print(f"❌ Ошибка при создании таблицы: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

    print("\n✨ Инициализация завершена успешно!")


def upgrade_database():
    """
    Обновление структуры базы данных до последней версии.
    """
    if not check_existing_database(DATABASE_FILE):
        print("База данных не существует. Запустите init_db() сначала")
        return

    print("🔄 Проверка необходимости обновления...")

    conn = get_db_connection(DATABASE_FILE)
    cursor = conn.cursor()

    # Проверяем наличие колонки ceremony_attend (если нужно добавить)
    cursor.execute("PRAGMA table_info(rsvp_responses)")
    columns = [col[1] for col in cursor.fetchall()]

    upgrades = []

    # Пример: добавление новой колонки для регистрации
    if 'ceremony_attend' not in columns:
        upgrades.append("ALTER TABLE rsvp_responses ADD COLUMN ceremony_attend TEXT DEFAULT 'not_specified'")

    if upgrades:
        print(f"Найдено {len(upgrades)} обновлений")
        for upgrade in upgrades:
            try:
                cursor.execute(upgrade)
                print(f"✅ Выполнено: {upgrade}")
            except sqlite3.Error as e:
                print(f"⚠️ Ошибка: {e}")
        conn.commit()
    else:
        print("✅ База данных уже актуальна")

    conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Инициализация базы данных для свадебного сайта')
    parser.add_argument('--force', action='store_true', help='Принудительно пересоздать таблицу')
    parser.add_argument('--no-backup', action='store_true', help='Не создавать резервную копию')
    parser.add_argument('--upgrade', action='store_true', help='Обновить структуру базы данных')
    parser.add_argument('--show', action='store_true', help='Показать статистику без изменений')

    args = parser.parse_args()

    if args.show:
        if check_existing_database(DATABASE_FILE):
            conn = get_db_connection(DATABASE_FILE)
            cursor = conn.cursor()
            show_statistics(cursor)
            conn.close()
        else:
            print("База данных не найдена")
        sys.exit(0)

    if args.upgrade:
        upgrade_database()
        sys.exit(0)

    # Обычная инициализация
    init_db(force=args.force, backup=not args.no_backup)
"""
db.py - работа с локальной SQLite-базой данных.

Используется "чистый" модуль sqlite3 из стандартной библиотеки Python
(без ORM), т.к. для объёма и сложности данной дипломной работы это
достаточно, прозрачно и не требует дополнительных зависимостей.
Подключение к БД создаётся один раз на HTTP-запрос (Flask `g`) и
закрывается по окончании запроса.
"""

import sqlite3

from flask import current_app, g


def get_db():
    """
    @effects: при первом вызове в рамках текущего запроса открывает
        соединение с БД (flask.g.db) и настраивает row_factory для
        доступа к столбцам по имени; при повторных вызовах в том же
        запросе возвращает уже открытое соединение.
    @returns: sqlite3.Connection.
    """
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    """Закрывает соединение с БД в конце запроса (регистрируется в app.py)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """
    Создаёт таблицы БД по schema.sql, если они ещё не существуют.
    Безопасно вызывать при каждом запуске приложения (CREATE TABLE IF NOT EXISTS).
    """
    with app.app_context():
        db = get_db()
        with open(app.config["SCHEMA_PATH"], "r", encoding="utf-8") as f:
            db.executescript(f.read())
        db.commit()


def register_db(app):
    """Регистрирует закрытие соединения с БД по окончании запроса."""
    app.teardown_appcontext(close_db)

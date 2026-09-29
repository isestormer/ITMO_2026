"""
config.py - конфигурация приложения "Система создания и управления
мероприятиями".

Значения по умолчанию рассчитаны на локальный запуск/защиту диплома
без настройки внешних сервисов: локальная SQLite-БД, email-уведомления
пишутся в лог/файл ("console"-бэкенд) вместо реальной отправки.
Для боевого использования достаточно сменить EMAIL_BACKEND на "smtp"
и заполнить SMTP_* параметры - код email_service.py уже это поддерживает.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("EVENTAPP_SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_PATH = os.environ.get(
        "EVENTAPP_DB_PATH", os.path.join(BASE_DIR, "eventapp.sqlite3")
    )
    SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

    # "console" -- письма пишутся в лог-файл EMAIL_LOG_PATH (по умолчанию,
    #   не требует настройки, удобно для демонстрации на защите);
    # "smtp" -- реальная отправка через SMTP-сервер.
    EMAIL_BACKEND = os.environ.get("EVENTAPP_EMAIL_BACKEND", "console")
    EMAIL_LOG_PATH = os.path.join(BASE_DIR, "outgoing_emails.log")

    SMTP_HOST = os.environ.get("EVENTAPP_SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("EVENTAPP_SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("EVENTAPP_SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("EVENTAPP_SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("EVENTAPP_SMTP_FROM", "noreply@eventapp.local")

    # Мок-платёжный шлюз: PAYMENT_ALWAYS_SUCCEED=True -- все оплаты успешны
    # (удобно для демонстрации). См. services/payment_service.py.
    PAYMENT_ALWAYS_SUCCEED = True


class TestConfig(Config):
    TESTING = True
    DATABASE_PATH = ":memory:"
    EMAIL_BACKEND = "console"

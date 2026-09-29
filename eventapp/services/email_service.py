"""
services/email_service.py - отправка email-уведомлений.

Поддерживает два бэкенда (переключается настройкой Config.EMAIL_BACKEND):
  - "console" (по умолчанию): письмо не отправляется по сети, а дописывается
    в лог-файл EMAIL_LOG_PATH -- удобно для локальной демонстрации на
    защите без настройки реального почтового сервера;
  - "smtp": реальная отправка через smtplib.SMTP с STARTTLS.

С точки зрения остального приложения способ отправки не важен - вызывающий
код всегда работает с send_email(to, subject, body).
"""

import smtplib
from datetime import datetime
from email.mime.text import MIMEText


def send_email(config, to_address, subject, body):
    """
    Отправляет письмо согласно config.EMAIL_BACKEND.

    @requires: config - объект конфигурации приложения (Config);
        to_address - строка с email-адресом получателя;
        subject, body - строки.
    @effects: письмо либо дописывается в лог-файл (backend "console"),
        либо отправляется через SMTP (backend "smtp").
    @returns: True, если письмо успешно "отправлено"/залогировано,
        False при ошибке отправки (для smtp-бэкенда).
    """
    if config["EMAIL_BACKEND"] == "smtp":
        return _send_via_smtp(config, to_address, subject, body)
    return _send_via_console(config, to_address, subject, body)


def _send_via_console(config, to_address, subject, body):
    entry = (
        f"\n{'=' * 60}\n"
        f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Кому: {to_address}\n"
        f"Тема: {subject}\n"
        f"{'-' * 60}\n"
        f"{body}\n"
    )
    with open(config["EMAIL_LOG_PATH"], "a", encoding="utf-8") as f:
        f.write(entry)
    return True


def _send_via_smtp(config, to_address, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = config["SMTP_FROM"]
    msg["To"] = to_address
    try:
        with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"], timeout=10) as server:
            server.starttls()
            if config["SMTP_USER"]:
                server.login(config["SMTP_USER"], config["SMTP_PASSWORD"])
            server.sendmail(config["SMTP_FROM"], [to_address], msg.as_string())
        return True
    except (smtplib.SMTPException, OSError):
        return False

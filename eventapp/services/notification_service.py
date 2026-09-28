"""
services/notification_service.py - формирование и рассылка уведомлений.

Каждое уведомление сначала записывается в таблицу notifications
(статус "queued"), затем немедленно предпринимается попытка отправки
через email_service; итоговый статус ("sent"/"failed") и время отправки
обновляются в той же записи. Такой журнал уведомлений позволяет
организатору видеть историю рассылок и то, что письмо было отправлено,
даже если реальный email не настроен (в режиме backend="console").
"""

from datetime import datetime

from services.email_service import send_email

TEMPLATES = {
    "registration_confirmation": (
        "Подтверждение регистрации: {event_title}",
        "Здравствуйте, {name}!\n\n"
        "Вы успешно зарегистрированы на мероприятие «{event_title}».\n"
        "Дата и время: {start}\n"
        "Место проведения: {location}\n\n"
        "До встречи на мероприятии!",
    ),
    "payment_confirmation": (
        "Оплата подтверждена: {event_title}",
        "Здравствуйте, {name}!\n\n"
        "Ваша оплата за участие в мероприятии «{event_title}» на сумму "
        "{amount} руб. успешно проведена.\n"
        "Номер транзакции: {transaction_ref}\n\n"
        "Спасибо за оплату!",
    ),
    "event_reminder": (
        "Напоминание: «{event_title}» уже скоро",
        "Здравствуйте, {name}!\n\n"
        "Напоминаем, что мероприятие «{event_title}» состоится:\n"
        "{start}, {location}\n\n"
        "Ждём вас!",
    ),
    "event_cancelled": (
        "Мероприятие «{event_title}» отменено",
        "Здравствуйте, {name}!\n\n"
        "К сожалению, мероприятие «{event_title}» ({start}) отменено "
        "организатором. Приносим извинения за неудобства.",
    ),
}


def notify(db, config, user_row, notif_type, event_row=None, **extra):
    """
    Формирует и отправляет уведомление пользователю по шаблону notif_type.

    @requires: user_row - строка таблицы users (со столбцами id, full_name, email);
        notif_type - один из ключей TEMPLATES;
        event_row - строка таблицы events (нужна для большинства шаблонов);
        extra - дополнительные поля для подстановки в шаблон (amount, transaction_ref, ...).
    @effects: создаёт запись в notifications и пытается отправить письмо;
        обновляет статус записи (sent/failed) и sent_at.
    @returns: id созданной записи notifications.
    """
    subject_tpl, body_tpl = TEMPLATES[notif_type]
    context = {"name": user_row["full_name"]}
    if event_row is not None:
        context.update(
            event_title=event_row["title"],
            start=event_row["start_datetime"],
            location=event_row["location"],
        )
    context.update(extra)

    subject = subject_tpl.format(**context)
    body = body_tpl.format(**context)

    event_id = event_row["id"] if event_row is not None else None
    cur = db.execute(
        "INSERT INTO notifications (user_id, event_id, type, subject, body, status) "
        "VALUES (?, ?, ?, ?, ?, 'queued')",
        (user_row["id"], event_id, notif_type, subject, body),
    )
    notification_id = cur.lastrowid
    db.commit()

    ok = send_email(config, user_row["email"], subject, body)
    status = "sent" if ok else "failed"
    db.execute(
        "UPDATE notifications SET status = ?, sent_at = ? WHERE id = ?",
        (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notification_id),
    )
    db.commit()
    return notification_id

-- =============================================================
--  Схема базы данных "Система создания и управления мероприятиями"
--  СУБД: SQLite (файловая, локальная)
-- =============================================================

PRAGMA foreign_keys = ON;

-- Пользователи системы: и организаторы, и участники хранятся в одной
-- таблице с полем role -- это единая сущность "Пользователь" с ролью,
-- что соответствует диаграмме классов (наследование User -> Organizer/Participant
-- на уровне логики приложения, единая таблица на уровне хранения).
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    phone         TEXT,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('organizer', 'participant')),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Мероприятия
CREATE TABLE IF NOT EXISTS events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    organizer_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title          TEXT    NOT NULL,
    description    TEXT,
    category       TEXT    NOT NULL DEFAULT 'Другое',
    location       TEXT    NOT NULL,
    start_datetime TEXT    NOT NULL,   -- ISO 8601, 'YYYY-MM-DD HH:MM'
    end_datetime   TEXT,
    capacity       INTEGER NOT NULL CHECK (capacity > 0),
    price          REAL    NOT NULL DEFAULT 0 CHECK (price >= 0),
    status         TEXT    NOT NULL DEFAULT 'published'
                     CHECK (status IN ('draft', 'published', 'cancelled', 'completed')),
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Регистрации участников на мероприятия (билеты)
CREATE TABLE IF NOT EXISTS registrations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id       INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status         TEXT    NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'confirmed', 'cancelled')),
    registered_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (event_id, participant_id)   -- нельзя зарегистрироваться на одно
                                          -- мероприятие дважды
);

-- Оплаты по регистрациям (одна регистрация -- максимум одна актуальная оплата)
CREATE TABLE IF NOT EXISTS payments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_id  INTEGER NOT NULL REFERENCES registrations(id) ON DELETE CASCADE,
    amount           REAL    NOT NULL CHECK (amount >= 0),
    method            TEXT    NOT NULL DEFAULT 'mock_card',
    status           TEXT    NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    transaction_ref  TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    paid_at          TEXT
);

-- Журнал уведомлений (email), отправляемых системой
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id    INTEGER REFERENCES events(id) ON DELETE SET NULL,
    type        TEXT    NOT NULL CHECK (type IN (
                    'registration_confirmation',
                    'payment_confirmation',
                    'event_reminder',
                    'event_cancelled'
                )),
    subject     TEXT    NOT NULL,
    body        TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'queued'
                  CHECK (status IN ('queued', 'sent', 'failed')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    sent_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_organizer ON events(organizer_id);
CREATE INDEX IF NOT EXISTS idx_events_status_date ON events(status, start_datetime);
CREATE INDEX IF NOT EXISTS idx_registrations_event ON registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_registrations_participant ON registrations(participant_id);
CREATE INDEX IF NOT EXISTS idx_payments_registration ON payments(registration_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);

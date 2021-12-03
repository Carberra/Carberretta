-- CREATE TABLE IF NOT EXISTS example (
--     user_id INTEGER PRIMARY KEY,
--     some_string TEXT,
--     time_or_date NUMERIC,
--     now NUMERIC DEFAULT CURRENT_TIMESTAMP
-- );

CREATE TABLE IF NOT EXISTS errors (
    err_id TEXT PRIMARY KEY,
    err_time NUMERIC DEFAULT CURRENT_TIMESTAMP,
    err_cmd TEXT,
    err_text TEXT
);

CREATE TABLE IF NOT EXISTS support_cases (
    case_id TEXT PRIMARY KEY,
    client_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS support_instances (
    case_id TEXT,
    instance_id TEXT,
    channel_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    opened_at NUMERIC DEFAULT CURRENT_TIMESTAMP,
    closed_at NUMERIC,
    PRIMARY KEY (case_id, instance_id),
    FOREIGN KEY (case_id) REFERENCES support_cases(case_id)
);

CREATE TABLE IF NOT EXISTS support_history (
    case_id TEXT PRIMARY KEY,
    author_id INTEGER NOT NULL,
    is_helper INTEGER NOT NULL,
    FOREIGN KEY (case_id) REFERENCES support_cases(case_id)
);

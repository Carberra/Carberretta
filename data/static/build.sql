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

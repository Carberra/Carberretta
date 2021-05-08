CREATE TABLE IF NOT EXISTS videos (
    ID int NOT NULL PRIMARY KEY,
    Vid text DEFAULT "",
    Vod text DEFAULT ""
);

INSERT OR IGNORE INTO videos (ID)
VALUES (1);

CREATE TABLE IF NOT EXISTS premieres (
    VideoID text NOT NULL PRIMARY KEY,
    Upcoming int,
    Announced int
);

CREATE TABLE IF NOT EXISTS streams (
    ID int NOT NULL PRIMARY KEY,
    StreamStart text DEFAULT "",
    StreamEnd text DEFAULT "",
    StreamLive int DEFAULT 0,
    StreamMessage int DEFAULT 0
);

INSERT OR IGNORE INTO streams (ID)
VALUES (1);

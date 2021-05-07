CREATE TABLE IF NOT EXISTS feeds (
    ContentType text NOT NULL PRIMARY KEY,
    ContentValue text DEFAULT ""
);

INSERT OR IGNORE INTO feeds (ContentType, ContentValue)
VALUES
    ("video", ""),
    ("vod", ""),
    ("stream_start", ""),
    ("stream_end", ""),
    ("stream_live", "0"),
    ("stream_message", "");

CREATE TABLE IF NOT EXISTS premieres (
    VideoID text NOT NULL PRIMARY KEY,
    Upcoming int,
    Announced int
);

CREATE TABLE IF NOT EXISTS hugs (
    UserID INTEGER NOT NULL PRIMARY KEY,
    received INTEGER DEFAULT 0,
    given INTEGER DEFAULT 0
);

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

CREATE TABLE IF NOT EXISTS videos (
    ContentType text NOT NULL PRIMARY KEY,
    ContentValue text DEFAULT ""
);

INSERT OR IGNORE INTO videos (ContentType)
VALUES ("video"), ("vod");

CREATE TABLE IF NOT EXISTS premieres (
    VideoID text NOT NULL PRIMARY KEY,
    Upcoming integer,
    Announced integer
);

CREATE TABLE IF NOT EXISTS streams (
    ID integer NOT NULL PRIMARY KEY,
    StreamStart numeric DEFAULT 0,
    StreamEnd numeric DEFAULT 0,
    StreamLive integer DEFAULT 0,
    StreamMessage integer DEFAULT 0
);

INSERT OR IGNORE INTO streams (ID)
VALUES (1);

CREATE TABLE IF NOT EXISTS members (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS books (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL,
    author    TEXT NOT NULL,
    isbn      TEXT NOT NULL UNIQUE,
    category  TEXT NOT NULL,
    available INTEGER NOT NULL DEFAULT 1 CHECK (available IN (0,1))
);
CREATE TABLE IF NOT EXISTS issues (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id     INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    member_id   INTEGER NOT NULL REFERENCES members(id),
    issue_date  TEXT NOT NULL DEFAULT (date('now')),
    return_date TEXT
);

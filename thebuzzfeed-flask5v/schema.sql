
CREATE TABLE IF NOT EXISTS users (
  username TEXT PRIMARY KEY,
  password TEXT
);
CREATE TABLE IF NOT EXISTS videos (
  id TEXT PRIMARY KEY,
  title TEXT,
  filename TEXT,
  uploader TEXT,
  created_at TEXT,
  comments_enabled INTEGER DEFAULT 1,
  likes INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id TEXT,
  username TEXT,
  text TEXT,
  created_at TEXT,
  visible INTEGER DEFAULT 1,
  likes INTEGER DEFAULT 0
);

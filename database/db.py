"""
Database layer using aiosqlite.
"""

import aiosqlite
from config import DB_PATH


INIT_SQL = """
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assistant_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    api_id TEXT,
    api_hash TEXT,
    session_string TEXT
);

CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    requested_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    chat_id INTEGER PRIMARY KEY,
    loop INTEGER DEFAULT 0,
    volume INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS active_chats (
    chat_id INTEGER PRIMARY KEY,
    current_title TEXT,
    current_file_path TEXT,
    requested_by TEXT,
    started_at INTEGER DEFAULT (strftime('%s','now'))
);

INSERT OR IGNORE INTO assistant_config (id, api_id, api_hash, session_string)
VALUES (1, '', '', '');
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(INIT_SQL)
        await db.commit()


# ── Admins ──────────────────────────────────────────

async def add_admin(username: str, password_hash: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admins (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        await db.commit()


async def get_admin(username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM admins WHERE username = ?", (username,))
        return await cur.fetchone()


# ── Assistant Config ────────────────────────────────

async def get_assistant_config():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM assistant_config WHERE id = 1")
        return await cur.fetchone()


async def set_assistant_config(api_id: str, api_hash: str, session_string: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE assistant_config SET api_id = ?, api_hash = ?, session_string = ? WHERE id = 1",
            (api_id, api_hash, session_string),
        )
        await db.commit()


# ── Queue ───────────────────────────────────────────

async def add_queue(chat_id: int, title: str, file_path: str, requested_by: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO queue (chat_id, title, file_path, requested_by) VALUES (?, ?, ?, ?)",
            (chat_id, title, file_path, requested_by),
        )
        await db.commit()


async def get_queue(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM queue WHERE chat_id = ? ORDER BY id", (chat_id,)
        )
        return await cur.fetchall()


async def pop_queue(chat_id: int):
    """Return and delete first queue item for chat."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM queue WHERE chat_id = ? ORDER BY id LIMIT 1", (chat_id,)
        )
        row = await cur.fetchone()
        if row:
            await db.execute("DELETE FROM queue WHERE id = ?", (row["id"],))
            await db.commit()
        return row


async def remove_queue_item(chat_id: int, index: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM queue WHERE chat_id = ? ORDER BY id LIMIT 1 OFFSET ?",
            (chat_id, index),
        )
        row = await cur.fetchone()
        if row:
            await db.execute("DELETE FROM queue WHERE id = ?", (row[0],))
            await db.commit()
            return True
        return False


async def clear_queue(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM queue WHERE chat_id = ?", (chat_id,))
        await db.commit()


# ── Settings ────────────────────────────────────────

async def get_settings(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM settings WHERE chat_id = ?", (chat_id,))
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO settings (chat_id, loop, volume) VALUES (?, 0, 100)",
                (chat_id,),
            )
            await db.commit()
            return {"chat_id": chat_id, "loop": 0, "volume": 100}
        return dict(row)


async def set_loop(chat_id: int, loop: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (chat_id, loop, volume) VALUES (?, ?, COALESCE((SELECT volume FROM settings WHERE chat_id = ?), 100))",
            (chat_id, loop, chat_id),
        )
        await db.commit()


async def set_volume(chat_id: int, volume: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (chat_id, loop, volume) VALUES (?, COALESCE((SELECT loop FROM settings WHERE chat_id = ?), 0), ?)",
            (chat_id, chat_id, volume),
        )
        await db.commit()


# ── Active Chats ─────────────────────────────────────

async def set_active_chat(chat_id: int, title: str, file_path: str, requested_by: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO active_chats
               (chat_id, current_title, current_file_path, requested_by)
               VALUES (?, ?, ?, ?)""",
            (chat_id, title, file_path, requested_by),
        )
        await db.commit()


async def clear_active_chat(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM active_chats WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def get_active_chat(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM active_chats WHERE chat_id = ?", (chat_id,))
        return await cur.fetchone()


async def get_all_active_chats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM active_chats")
        return await cur.fetchall()

from __future__ import annotations

import asyncio
from pathlib import Path

import aiosqlite


class SubscriberStore:
    def __init__(self, database_path: str) -> None:
        self._path = database_path
        self._connection: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def open(self) -> None:
        Path(self._path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self._path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")
        await self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id INTEGER PRIMARY KEY,
                active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                last_notified_rotation_key TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await self._connection.commit()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    def _db(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("SubscriberStore is not open")
        return self._connection

    async def subscribe(self, chat_id: int, rotation_key: str | None) -> None:
        async with self._lock:
            await self._db().execute(
                """
                INSERT INTO subscribers (chat_id, active, last_notified_rotation_key)
                VALUES (?, 1, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    active = 1,
                    last_notified_rotation_key = excluded.last_notified_rotation_key,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (chat_id, rotation_key),
            )
            await self._db().commit()

    async def unsubscribe(self, chat_id: int) -> bool:
        async with self._lock:
            cursor = await self._db().execute(
                """
                UPDATE subscribers
                SET active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ? AND active = 1
                """,
                (chat_id,),
            )
            await self._db().commit()
            return cursor.rowcount > 0

    async def deactivate(self, chat_id: int) -> None:
        async with self._lock:
            await self._db().execute(
                "UPDATE subscribers SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                (chat_id,),
            )
            await self._db().commit()

    async def pending_subscribers(self, rotation_key: str) -> list[int]:
        async with self._lock:
            cursor = await self._db().execute(
                """
                SELECT chat_id FROM subscribers
                WHERE active = 1
                  AND (last_notified_rotation_key IS NULL OR last_notified_rotation_key != ?)
                ORDER BY chat_id
                """,
                (rotation_key,),
            )
            rows = await cursor.fetchall()
            return [int(row["chat_id"]) for row in rows]

    async def mark_notified(self, chat_id: int, rotation_key: str) -> None:
        async with self._lock:
            await self._db().execute(
                """
                UPDATE subscribers
                SET last_notified_rotation_key = ?, updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ? AND active = 1
                """,
                (rotation_key, chat_id),
            )
            await self._db().commit()

    async def get(self, chat_id: int) -> dict[str, object] | None:
        """Return one subscriber. Primarily useful for diagnostics and tests."""
        async with self._lock:
            cursor = await self._db().execute(
                "SELECT chat_id, active, last_notified_rotation_key FROM subscribers WHERE chat_id = ?",
                (chat_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row is not None else None


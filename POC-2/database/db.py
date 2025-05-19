# database/db.py
import aiosqlite
from models.ticket import Ticket

DB_PATH = "support.sqlite3"

async def create_ticket(message: str) -> Ticket:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                status TEXT
            )
        """)
        cursor = await db.execute(
            "INSERT INTO tickets (message, status) VALUES (?, ?)", (message, "open")
        )
        await db.commit()
        ticket_id = cursor.lastrowid
        return Ticket(id=ticket_id, message=message, status="open")

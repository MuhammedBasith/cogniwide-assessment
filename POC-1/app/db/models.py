import sqlite3
import os

def init_db():
    # Check if database file exists
    db_exists = os.path.exists("calls.db")
    
    # If database exists, remove it to start fresh
    if db_exists:
        try:
            os.remove("calls.db")
            if os.path.exists("calls.db-journal"):
                os.remove("calls.db-journal")
        except Exception:
            pass
    
    conn = sqlite3.connect("calls.db")
    c = conn.cursor()
    
    # Create the table with the complete schema for call data
    c.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE,
            timestamp TEXT,                -- When the record was created
            phone_number TEXT,             -- Caller's phone number
            transcript TEXT,               -- Complete conversation transcript
            summary TEXT,                  -- AI-generated summary of the call
            intent TEXT,                   -- Extracted intent (e.g., "schedule_callback")
            intent_json TEXT,              -- Full intent data as JSON
            direction TEXT,                -- inbound or outbound
            start_time TEXT,               -- When the call started
            end_time TEXT,                 -- When the call ended
            duration_seconds REAL,         -- Call duration in seconds
            recording_url TEXT,            -- URL to the call recording
            stereo_recording_url TEXT,     -- URL to the stereo recording
            is_complete INTEGER DEFAULT 0, -- Whether this is a complete record
            last_updated TEXT              -- When the record was last updated
        )
    ''')
    
    conn.commit()
    conn.close()


import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()

class CallData(BaseModel):
    id: int
    call_id: str
    timestamp: str
    transcript: Optional[str] = None
    summary: Optional[str] = None
    intent: Optional[str] = None
    intent_json: Optional[str] = None
    direction: Optional[str] = None
    phone_number: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None  # Changed from int to float
    recording_url: Optional[str] = None
    stereo_recording_url: Optional[str] = None
    is_complete: bool
    last_updated: str

class WebhookEvent(BaseModel):
    id: int
    event_type: str
    timestamp: str
    payload: Dict[str, Any]
    processed: bool

@router.get("/calls", response_model=List[CallData])
async def get_all_calls():
    """
    Retrieve all call records from the database
    """
    try:
        conn = sqlite3.connect("calls.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM calls ORDER BY timestamp DESC")
        calls = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return calls
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve calls: {str(e)}")

@router.get("/calls/{call_id}", response_model=CallData)
async def get_call_by_id(call_id: str):
    """
    Retrieve a specific call record by its call_id
    """
    try:
        conn = sqlite3.connect("calls.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM calls WHERE call_id = ?", (call_id,))
        call = cursor.fetchone()
        
        conn.close()
        
        if not call:
            raise HTTPException(status_code=404, detail=f"Call with ID {call_id} not found")
        
        return dict(call)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to retrieve call: {str(e)}")

@router.get("/webhooks", response_model=List[WebhookEvent])
async def get_webhook_events():
    """
    Retrieve webhook events from the database
    """
    try:
        # Check if webhooks table exists
        conn = sqlite3.connect("calls.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if the webhooks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='webhooks'")
        if not cursor.fetchone():
            # Create webhooks table if it doesn't exist
            cursor.execute("""
                CREATE TABLE webhooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    timestamp TEXT,
                    payload TEXT,
                    processed BOOLEAN
                )
            """)
            conn.commit()
            conn.close()
            return []
        
        cursor.execute("SELECT * FROM webhooks ORDER BY timestamp DESC LIMIT 100")
        webhooks = []
        
        for row in cursor.fetchall():
            webhook_dict = dict(row)
            # Convert payload from string to dict if needed
            if isinstance(webhook_dict['payload'], str):
                import json
                try:
                    webhook_dict['payload'] = json.loads(webhook_dict['payload'])
                except:
                    webhook_dict['payload'] = {"raw": webhook_dict['payload']}
            
            webhooks.append(webhook_dict)
        
        conn.close()
        return webhooks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve webhook events: {str(e)}")

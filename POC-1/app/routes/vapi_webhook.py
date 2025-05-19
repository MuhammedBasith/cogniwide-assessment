import json
import sqlite3
from datetime import datetime
from fastapi import APIRouter, Request, Response
from app.services.call_handler import process_call_data

router = APIRouter()

# Ensure webhook table exists
def ensure_webhook_table():
    conn = sqlite3.connect("calls.db")
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

# Store webhook event in database
async def store_webhook_event(event_type, payload, processed=False):
    try:
        # Ensure the webhook table exists
        ensure_webhook_table()
        
        # Store the webhook event
        conn = sqlite3.connect("calls.db")
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO webhooks (event_type, timestamp, payload, processed) VALUES (?, ?, ?, ?)",
            (event_type, datetime.now().isoformat(), json.dumps(payload), processed)
        )
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error storing webhook event: {e}")
        return False

@router.post("/webhook/vapi")
async def handle_vapi_webhook(request: Request):
    try:
        body = await request.json()
        
        # Extract message type and data
        message = body.get("message", {})
        message_type = message.get("type")
        
        # Store the webhook event in the database
        await store_webhook_event(message_type, body)
        
        # Handle end-of-call-report event (final summary with complete data)
        if message_type == "end-of-call-report":
            # Extract call ID from the call object
            call_data = message.get("call", {})
            call_id = call_data.get("id")
            
            if not call_id:
                return Response(status_code=400, content="Missing call_id in report")
            
            # Process the complete call data
            result = await process_call_data(message, is_final=True)
            
            # Update webhook as processed
            await store_webhook_event(message_type, body, processed=True)
            
            return {"status": "success", "call_id": call_id}
        
        # For other event types, just acknowledge receipt
        return {"status": "acknowledged"}
    
    except Exception as e:
        return Response(status_code=500, content=f"Error: {str(e)}")

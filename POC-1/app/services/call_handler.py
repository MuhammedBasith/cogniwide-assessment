import sqlite3
import json
from datetime import datetime
from app.utils.intent_extractor import extract_intent

async def process_call_data(data, is_final=False):
    """
    Process call data from Vapi webhook and store it in the database.
    Optimized to handle end-of-call-report events with complete transcript data.
    """
    try:
        # Extract data from end-of-call-report
        call_id = data.get("call", {}).get("id")
        transcript = data.get("transcript", "")
        summary = data.get("summary", "")
        
        # Extract timestamps
        started_at = data.get("startedAt")
        ended_at = data.get("endedAt")
        duration_seconds = data.get("durationSeconds", 0)
        
        # Extract recording URLs
        recording_url = data.get("recordingUrl", "")
        stereo_recording_url = data.get("stereoRecordingUrl", "")
        
        # Extract call direction (default to inbound for now)
        direction = "inbound"  # Default
        
        # Extract phone number (may need to be adjusted based on Vapi's data structure)
        phone_number = ""  # This might need to be extracted differently
        
        # Extract or generate intent
        intent_str = "unknown"
        intent_data = {"intent": "unknown", "confidence": 0.0}
        
        # If we have a transcript, extract intent using our intent extractor
        if transcript and len(transcript.strip()) > 0:
            try:
                # Extract intent from transcript
                intent_data = extract_intent(transcript)
                intent_str = intent_data.get("intent", "unknown")
                
                # If intent is still unknown but we have a summary, try extracting from summary
                if intent_str == "unknown" and summary:
                    summary_intent = extract_intent(summary)
                    if summary_intent.get("intent") != "unknown":
                        intent_data = summary_intent
                        intent_str = summary_intent.get("intent")
            except Exception:
                pass
        
        # Convert intent data to JSON string
        intent_json = json.dumps(intent_data)
        
        # Current timestamp for database record
        current_time = datetime.now().isoformat()
        
        # Connect to database
        conn = sqlite3.connect("calls.db")
        c = conn.cursor()
        
        # Check if this call already exists in the database
        c.execute("SELECT id FROM calls WHERE call_id = ?", (call_id,))
        existing_call = c.fetchone()
        
        if existing_call:
            # Update existing record with final data
            c.execute(
                """UPDATE calls SET 
                    transcript = ?,
                    summary = ?,
                    intent = ?,
                    intent_json = ?,
                    direction = ?,
                    phone_number = ?,
                    start_time = ?,
                    end_time = ?,
                    duration_seconds = ?,
                    recording_url = ?,
                    stereo_recording_url = ?,
                    is_complete = 1,
                    last_updated = ?
                WHERE call_id = ?""",
                (transcript, summary, intent_str, intent_json, direction, phone_number,
                 started_at, ended_at, duration_seconds, recording_url, stereo_recording_url,
                 current_time, call_id)
            )
        else:
            # Insert new record
            c.execute(
                """INSERT INTO calls 
                    (call_id, timestamp, transcript, summary, intent, intent_json, direction, 
                     phone_number, start_time, end_time, duration_seconds, recording_url, 
                     stereo_recording_url, is_complete, last_updated) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (call_id, current_time, transcript, summary, intent_str, intent_json, direction,
                 phone_number, started_at, ended_at, duration_seconds, recording_url,
                 stereo_recording_url, 1, current_time)
            )
        
        conn.commit()
        conn.close()
        
        return {"success": True, "call_id": call_id, "intent": intent_str}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

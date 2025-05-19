import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import httpx
from typing import Optional

# Load environment variables
load_dotenv()

# Get Vapi API key from environment variables
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
DEFAULT_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
DEFAULT_CALLER_ID = os.getenv("VAPI_DEFAULT_CALLER_ID")

router = APIRouter()

class PhoneDestination(BaseModel):
    type: str = "number"
    number: str
    callerId: Optional[str] = None

class OutboundCallRequest(BaseModel):
    assistantId: Optional[str] = None
    destination: PhoneDestination

class OutboundCallResponse(BaseModel):
    call_id: str
    status: str
    message: str

@router.post("/outbound-call", response_model=OutboundCallResponse)
async def initiate_outbound_call(call_request: OutboundCallRequest):
    """
    Initiates an outbound call using the Vapi API.
    
    Requires:
    - A valid phone number in E.164 format (e.g., +1234567890)
    - A valid Vapi API key set in environment variables
    """
    if not VAPI_API_KEY:
        raise HTTPException(status_code=500, detail="VAPI_API_KEY not configured in environment variables")
    
    # Use the provided assistantId or fall back to the default one
    assistant_id = call_request.assistantId or DEFAULT_ASSISTANT_ID
    
    if not assistant_id:
        raise HTTPException(
            status_code=400, 
            detail="No assistantId provided and no default assistant configured"
        )
    
    # Create the payload exactly matching the curl example
    payload = {
        "assistantId": assistant_id,
        "customers": [{
            "number": call_request.destination.number
        }]
    }
    
    # Add caller ID if provided
    if call_request.destination.callerId:
        payload["destination"]["callerId"] = call_request.destination.callerId
    
    # Print the request payload for debugging
    print(f"\nVapi API Request Payload:\n{payload}\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.vapi.ai/call",
                json=payload,
                headers={
                    "Authorization": f"Bearer {VAPI_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            return {
                "call_id": response_data.get("id", "unknown"),
                "status": "initiated",
                "message": "Outbound call successfully initiated"
            }
            
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors from the Vapi API
        error_detail = f"Vapi API error: {e.response.status_code}"
        try:
            error_json = e.response.json()
            if "message" in error_json:
                error_detail = f"Vapi API error: {error_json['message']} The failed to call is because of an International number"
        except:
            pass
        
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
        
    except Exception as e:
        # Handle other errors
        raise HTTPException(status_code=500, detail=f"Failed to initiate outbound call: {str(e)}")

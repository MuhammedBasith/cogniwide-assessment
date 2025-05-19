import os
import re
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
from typing import List, Dict, Any

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Gemini client
client = genai.Client(api_key=GOOGLE_API_KEY)

class Intent(BaseModel):
    intent: str
    confidence: float

# Define common intents for customer support calls with descriptions
INTENT_DEFINITIONS = {
    "schedule_callback": {
        "description": "Customer wants to schedule a callback or appointment",
        "keywords": ["call back", "callback", "schedule", "appointment", "later", "tomorrow", "next week", "available", "reach me"]
    },
    "technical_support": {
        "description": "Customer needs help with a technical issue",
        "keywords": ["not working", "broken", "error", "help", "fix", "issue", "problem", "technical"]
    },
    "billing_inquiry": {
        "description": "Customer has questions about billing or payments",
        "keywords": ["bill", "payment", "charge", "invoice", "cost", "price", "subscription", "pay"]
    },
    "product_information": {
        "description": "Customer wants information about products or services",
        "keywords": ["information", "details", "tell me about", "features", "how does", "what is", "product"]
    },
    "complaint": {
        "description": "Customer is making a complaint",
        "keywords": ["unhappy", "disappointed", "complaint", "not satisfied", "poor", "terrible", "bad experience"]
    },
    "cancel_service": {
        "description": "Customer wants to cancel a service",
        "keywords": ["cancel", "stop", "end", "terminate", "no longer", "don't want"]
    },
    "change_plan": {
        "description": "Customer wants to modify their current plan",
        "keywords": ["change", "upgrade", "downgrade", "switch", "different plan", "modify"]
    },
    "general_inquiry": {
        "description": "Customer has a general question",
        "keywords": ["question", "wondering", "curious", "inquiry", "information"]
    },
    "request_refund": {
        "description": "Customer wants a refund",
        "keywords": ["refund", "money back", "reimburse", "return", "credit"]
    },
    "report_issue": {
        "description": "Customer is reporting a problem",
        "keywords": ["report", "problem", "issue", "not right", "wrong"]
    }
}

# List of common intents for easy access
COMMON_INTENTS = list(INTENT_DEFINITIONS.keys())

def preprocess_transcript(text: str) -> str:
    """Preprocess the transcript to clean and format it for better analysis.
    
    Args:
        text: The raw conversation transcript
        
    Returns:
        Cleaned and formatted transcript
    """
    if not text:
        return ""
        
    # Remove excessive whitespace
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    
    # Ensure proper sentence breaks
    cleaned_text = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\2', cleaned_text)
    
    return cleaned_text


def extract_conversation_structure(text: str) -> Dict[str, Any]:
    """Extract structured information from the conversation.
    
    Args:
        text: The conversation transcript
        
    Returns:
        Dictionary with structured conversation data
    """
    # Basic structure to return
    structure = {
        "customer_statements": [],
        "agent_statements": [],
        "key_phrases": [],
        "potential_intents": []
    }
    
    if not text:
        return structure
    
    # Simple pattern to identify speaker turns
    # This is a basic implementation - could be improved with more sophisticated parsing
    lines = text.split('\n')
    current_speaker = "agent"  # Default assumption
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Very basic speaker detection - this would need to be customized based on actual transcript format
        if line.lower().startswith("customer:") or line.lower().startswith("caller:"):
            current_speaker = "customer"
            content = line.split(':', 1)[1].strip() if ':' in line else line
            structure["customer_statements"].append(content)
        elif line.lower().startswith("agent:") or line.lower().startswith("representative:"):
            current_speaker = "agent"
            content = line.split(':', 1)[1].strip() if ':' in line else line
            structure["agent_statements"].append(content)
        else:
            # If no speaker is explicitly marked, attribute to the current speaker
            if current_speaker == "customer":
                structure["customer_statements"].append(line)
            else:
                structure["agent_statements"].append(line)
    
    # Check for keywords associated with each intent
    for intent, info in INTENT_DEFINITIONS.items():
        for keyword in info["keywords"]:
            if keyword.lower() in text.lower():
                if intent not in structure["potential_intents"]:
                    structure["potential_intents"].append(intent)
                    structure["key_phrases"].append(keyword)
    
    return structure


def generate_intent_prompt(text: str, structure: Dict[str, Any]) -> str:
    """Generate a detailed prompt for the Gemini model based on conversation structure.
    
    Args:
        text: The original conversation transcript
        structure: The extracted conversation structure
        
    Returns:
        A formatted prompt for the Gemini model
    """
    # Build a detailed prompt with conversation analysis
    prompt = """
You are an expert in analyzing customer service conversations. Your task is to determine the customer's primary intent.

Analyze the following customer support conversation carefully. Pay special attention to:
1. What the customer explicitly asks for or mentions needing
2. The overall context and flow of the conversation
3. Any specific requests or issues mentioned multiple times
4. Statements that indicate what the customer wants to happen after the call

Choose the most appropriate intent category from this list:
"""
    
    # Add intent definitions with descriptions
    for intent, info in INTENT_DEFINITIONS.items():
        prompt += f"- {intent}: {info['description']}\n"
    
    prompt += "- unknown: Intent cannot be determined\n\n"
    
    # Add potential intents based on keyword matching
    if structure["potential_intents"]:
        prompt += "Based on keyword analysis, these intents may be relevant:\n"
        for intent in structure["potential_intents"]:
            prompt += f"- {intent}: {INTENT_DEFINITIONS[intent]['description']}\n"
        prompt += "\n"
    
    # Add key customer statements
    if structure["customer_statements"]:
        prompt += "Key customer statements:\n"
        for i, statement in enumerate(structure["customer_statements"], 1):
            if len(statement) > 10:  # Only include substantial statements
                prompt += f"{i}. {statement}\n"
        prompt += "\n"
    
    # Add the full conversation
    prompt += "Full conversation transcript:\n" + text + "\n\n"
    
    # Add response format instructions
    prompt += """
Respond with the intent category only, in the format {"intent": "category_name", "confidence": confidence_score}
where confidence_score is between 0.0 and 1.0 based on your certainty.

If the customer explicitly mentions wanting a callback or to be contacted later, this should strongly indicate a "schedule_callback" intent.
"""
    
    return prompt


def extract_intent(text: str) -> dict:
    """Extract intent from conversation text using Gemini AI with enhanced context analysis.
    
    Args:
        text: The conversation transcript or message text
        
    Returns:
        Dictionary with intent and confidence score
    """
    if not text or len(text.strip()) < 3:  # Require at least a few characters
        return {"intent": "unknown", "confidence": 0.0}
    
    # Preprocess the transcript
    cleaned_text = preprocess_transcript(text)
    
    # Extract conversation structure
    conversation_structure = extract_conversation_structure(cleaned_text)
    
    # Print the input text for debugging
    print(f"\n\nText input for intent extraction:\n{cleaned_text}\n")
    
    try:
        # Generate a detailed prompt based on conversation analysis
        prompt = generate_intent_prompt(cleaned_text, conversation_structure)
        
        # Print the prompt for debugging
        print(f"\nPrompt sent to Gemini:\n{prompt}\n")
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": Intent,
                "temperature": 0.1,  # Lower temperature for more deterministic results
                "max_output_tokens": 100,  # Limit token usage
            },
        )
        
        # Print the Gemini response for debugging
        print(f"Gemini response: {response.text}\n")
        
        # Get the parsed response
        intent_data = response.parsed.dict()
        
        # Ensure the intent is one of our predefined intents or 'unknown'
        if intent_data["intent"] not in COMMON_INTENTS and intent_data["intent"] != "unknown":
            # Try to map to the closest predefined intent using our keyword matching
            for intent, info in INTENT_DEFINITIONS.items():
                for keyword in info["keywords"]:
                    if keyword.lower() in intent_data["intent"].lower():
                        intent_data["intent"] = intent
                        break
                if intent_data["intent"] in COMMON_INTENTS:
                    break
            
            # If still not matched, use fallback logic
            if intent_data["intent"] not in COMMON_INTENTS:
                # Special handling for callback intent since it's important
                if any(kw in text.lower() for kw in ["call back", "callback", "call me", "reach me", "contact me"]):
                    intent_data["intent"] = "schedule_callback"
                else:
                    intent_data["intent"] = "general_inquiry"
        
        # Boost confidence for schedule_callback if there are strong indicators
        if intent_data["intent"] == "schedule_callback":
            callback_indicators = [
                "call me back", "call back", "callback", "contact me", "reach me", 
                "call tomorrow", "call next", "schedule", "appointment"
            ]
            
            if any(indicator in text.lower() for indicator in callback_indicators):
                intent_data["confidence"] = max(0.85, intent_data["confidence"])
        
        return intent_data
    except Exception as e:
        print(f"Error in intent extraction: {e}")
        return {"intent": "unknown", "confidence": 0.0}

import os
from google import genai
from pydantic import BaseModel
from typing import List

class IntentResult(BaseModel):
    intent: str
    confidence: float

class IntentClassifierAgent:
    @staticmethod
    async def classify(message: str) -> str:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable not set.")
        client = genai.Client(api_key=api_key)
        prompt = f"Classify the intent of this customer message as one of: faq, complaint, account_inquiry. Respond in JSON with fields: intent, confidence. Message: '{message}'"
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": IntentResult,
            },
        )
        # Use the response as a JSON string.
        # print(response.text)
        # Use instantiated objects.
        intent_result: IntentResult = response.parsed
        return intent_result.intent

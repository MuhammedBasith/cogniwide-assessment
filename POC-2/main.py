from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from agents.intent_classifier import IntentClassifierAgent
from agents.routing_agent import RoutingAgent
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

@app.post("/chat")
async def chat_handler(request: Request):
    body = await request.json()
    user_message = body.get("message")

    intent = await IntentClassifierAgent.classify(user_message)
    response = await RoutingAgent.route(intent, user_message)

    return {"response": response}

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routes import vapi_webhook, outbound_call, call_data
from app.db.models import init_db

# Create FastAPI app
app = FastAPI(title="Voice POC API", description="API for handling Vapi voice calls")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Check if database exists and remove it to start fresh
    if os.path.exists("calls.db"):
        os.remove("calls.db")
    
    # Initialize the database with the new schema
    init_db()

# Include routers
app.include_router(vapi_webhook.router)
app.include_router(outbound_call.router)
app.include_router(call_data.router, prefix="/api")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    # Redirect to the dashboard
    return RedirectResponse(url="/static/dashboard.html")

@app.get("/make-call")
async def make_call():
    # Redirect to the simple call form
    return RedirectResponse(url="/static/index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

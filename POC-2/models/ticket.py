# models/ticket.py
from pydantic import BaseModel
from typing import Optional

class Ticket(BaseModel):
    id: Optional[int] = None
    message: str
    status: str = "open"

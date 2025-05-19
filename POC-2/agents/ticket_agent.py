# agents/ticket_agent.py
from models.ticket import Ticket
from database.db import create_ticket

class TicketAgent:
    @staticmethod
    async def handle(message: str) -> str:
        # Mock ticket creation logic
        ticket = await create_ticket(message)
        return f"Ticket created with ID: {ticket.id}"

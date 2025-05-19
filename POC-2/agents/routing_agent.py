# agents/routing_agent.py
from agents.faq_agent import FAQAgent
from agents.ticket_agent import TicketAgent
from agents.account_agent import AccountAgent

class RoutingAgent:
    @staticmethod
    async def route(intent: str, message: str) -> str:
        if intent == "faq":
            return await FAQAgent.handle(message)
        elif intent == "complaint":
            return await TicketAgent.handle(message)
        elif intent == "account_inquiry":
            return await AccountAgent.handle(message)
        else:
            return "Sorry, I couldn't understand your request."

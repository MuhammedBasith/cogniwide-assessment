# agents/notify_agent.py
# Placeholder for NotifyAgent (Email/WhatsApp)
class NotifyAgent:
    @staticmethod
    async def notify(recipient: str, message: str, channel: str = "email") -> bool:
        # TODO: Integrate SendGrid/Twilio
        print(f"Notify {recipient} via {channel}: {message}")
        return True

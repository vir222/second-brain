import anthropic

from app.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

def generate(system: str, user_message: str, max_tokens: int = 1024) -> str:
    response = client.messages.create(
        model = settings.chat_model,
        max_tokens = max_tokens,
        system = system,
        messages = [{"role" : "user", "content": user_message}],
    )

    return "".join(block.text for block in response.content if block.type == "text")
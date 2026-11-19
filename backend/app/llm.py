import anthropic
from collections.abc import Iterator
from app.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

def generate(system: str, messages: list[dict], max_tokens: int = 1024) -> str:
    response = client.messages.create(
        model = settings.chat_model,
        max_tokens = max_tokens,
        system = system,
        messages = messages,
    )

    return "".join(block.text for block in response.content if block.type == "text")

def generate_stream(system : str, messages: list[dict], max_tokens: int = 1024) -> Iterator[str]:
    with client.messages.stream(
        model = settings.chat_model,
        max_tokens= max_tokens,
        system = system,
        messages = messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
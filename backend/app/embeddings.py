from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.openai_api_key)
BATCH_SIZE = 100

def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start+BATCH_SIZE]
        response = client.embeddings.create(model=settings.embedding_model, input=batch)
        ordered = sorted(response.data, key=lambda item: item.index)
        embeddings.extend(item.embedding for item in ordered)

    return embeddings

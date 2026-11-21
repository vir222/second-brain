from unittest.mock import MagicMock
from app.db import SessionLocal
from app.models import EMBEDDING_DIMENSIONS, Chunk, Document

def unit_vector(position: int) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    vector[position] = 1.0
    return vector

def add_ready_document(notebook_id: int, content: str, vector: list[float]) -> None:
    with SessionLocal() as db:
        document = Document(
            notebook_id = notebook_id,
            filename="notes.txt",
            storage_key=f"test-{notebook_id}-{abs(hash(content))}",
            content_type = "text/plain",
            size_bytes = len(content),
            status="ready",
        )
        db.add(document)
        db.flush()
        db.add(Chunk(document_id=document.id, chunk_index=0, content=content, embedding=vector))
        db.commit()

def test_upload_saves_document_and_queues_processing(client, make_user, monkeypatch):
    fake_task = MagicMock()
    monkeypatch.setattr("app.routers.documents.process_document_task", fake_task)
    headers = make_user()
    notebook = client.post("/notebooks", json={"title": "Bio"}, headers=headers).json()

    res = client.post(f"/notebooks/{notebook['id']}/documents", files={"file": ("notes.txt", b"Mitosis is cell division.", "text/plain")}, headers=headers,)
    assert res.status_code == 201
    document = res.json()
    assert document["status"] == "pending"
    assert document["filename"] == "notes.txt"
    fake_task.delay.assert_called_once_with(document['id'])

def test_fake_pdf_is_rejected(client, make_user, monkeypatch):
    monkeypatch.setattr("app.routers.documents.process_document_task", MagicMock())
    headers = make_user()
    notebook = client.post("/notebooks", json={"title" : "Bio"}, headers=headers).json()
    res = client.post(f"/notebooks/{notebook['id']}/documents", files= {"file": ("fake.pdf", b"This is just text.", "application/pdf")}, headers=headers)
    assert res.status_code == 400

def test_search_only_returns_chunks_from_your_own_notebook(client, make_user, monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.embed_texts", lambda texts: [unit_vector(0) for _ in texts]
    )
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    alice_notebook = client.post("/notebooks", json={"title": "A"}, headers=alice).json()
    bob_notebook = client.post("/notebooks", json={"title": "B"}, headers=bob).json()
    add_ready_document(alice_notebook["id"], "Alice's private notes", unit_vector(0))
    add_ready_document(bob_notebook["id"], "Bob's notes", unit_vector(0))

    res = client.post(
        f"/notebook/{bob_notebook['id']}/search", json={"query": "notes"}, headers=bob
    )
    #print(res.json())

    assert res.status_code == 200
    assert [result["content"] for result in res.json()] == ["Bob's notes"]
def test_create_and_list_notebooks(client, make_user):
    headers = make_user()

    res = client.post("/notebooks", json={"title": "Biology"}, headers=headers)

    assert res.status_code == 201
    assert res.json()["title"] == "Biology"
    assert [nb["title"] for nb in client.get("/notebooks", headers=headers).json()] == ["Biology"]

def test_users_cannot_access_each_others_notebooks(client, make_user):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    notebook = client.post("/notebooks", json = {"title" : "Alice's notes"}, headers=alice).json()
    path = f"/notebooks/{notebook['id']}"

    assert client.get(path, headers=bob).status_code == 404
    assert client.patch(path, json={"title": "Hacked"}, headers=bob).status_code == 404
    assert client.delete(path, headers=bob).status_code == 404
    assert client.get("/notebooks", headers=bob).json() == []

    assert client.get(path, headers=alice).json()["title"] == "Alice's notes" #Alices notes are untouched

def test_patch_only_changes_the_fields_sent(client, make_user):
    headers = make_user()
    notebook = client.post(
        "/notebooks", json={"title": "Bio", "description": "Chapter notes"}, headers=headers
    ).json()

    res = client.patch(f"/notebooks/{notebook['id']}", json={"title": "Biology"}, headers=headers)

    assert res.json()["title"] == "Biology"
    assert res.json()["description"] == "Chapter notes"

def test_patch_rejets_a_null_title(client, make_user):
    headers = make_user()
    notebook = client.post("/notebooks", json={"title": "Bio"}, headers=headers).json()

    res = client.patch(f"/notebooks/{notebook['id']}", json={"title": None}, headers=headers)

    assert res.status_code == 422
    
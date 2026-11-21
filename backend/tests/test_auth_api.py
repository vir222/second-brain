def test_signup_returns_user_without_password(client):
    res = client.post("/auth/signup", json={"email": "a@example.com", "password" : "password123"})

    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "a@example.com"
    assert "password" not in body
    assert "hashed_password" not in body

def test_duplicate_signup_is_rejected(client):
    payload = {"email" : "a@example.com", "password" : "password123"}
    client.post("/auth/signup", json=payload)

    res = client.post("/auth/signup", json=payload)

    assert res.status_code == 409

def test_email_is_case_insensitive(client):
    client.post("/auth/signup", json={"email" : "Storm@Example.com", "password" : "password123"})
    res = client.post("/auth/login", json={"email" : "storm@example.com", "password" : "password123"})

    assert res.status_code == 200

def test_login_with_wrong_password_fails(client):
    client.post("/auth/signup", json={"email" : "a@example.com", "password" : "password123"})

    res = client.post("/auth/login", json= {"email" : "a@example.com", "password" : "wrong password"})

    assert res.status_code == 401

def test_me_requires_a_token(client):
    assert client.get("/users/me").status_code == 401

def test_me_rejects_a_tampered_token(client, make_user):
    headers = make_user()
    token = headers["Authorization"].removeprefix("Bearer ")
    tampered = token[:-5] + ("aaaaa" if not token.endswith("aaaaa") else "bbbbb")

    res = client.get("/users/me", headers={"Authorization": f"Bearer {tampered}"})

    assert res.status_code == 401

def test_me_returns_the_current_user(client, make_user):
    headers = make_user("me@example.com")
    res = client.get("/users/me", headers=headers)

    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"

def test_password_too_short_for_signup(client):
    res = client.post("/auth/signup", json={"email" : "a@example.com", "password" : "pass"})

    assert res.status_code == 422
    assert client.post("/auth/login", json={"email": "a@example.com", "password": "pass"}).status_code == 401

import re

from conftest import register, token


def headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


def test_auth_and_private_crud(client):
    assert client.get("/agenda").status_code == 401
    created = register(client, "ana", "ana@example.com")
    assert created.status_code == 201
    assert created.json() == {"id": 1, "username": "ana", "email": "ana@example.com"}
    assert register(client, "ana", "otra@example.com").status_code == 409
    assert register(client, "bob", "bob@example.com").status_code == 201
    assert client.post("/auth/token", data={"username": "ana", "password": "mal"}).status_code == 401
    ana, bob = token(client, "ana"), token(client, "bob")

    payload = {"nombre": "María López", "telefono": "8123456789", "mail": "maria@example.com"}
    contact = client.post("/agenda", json=payload, headers=headers(ana))
    assert contact.status_code == 201
    contact_id = contact.json()["id"]
    assert "user_id" not in contact.json()
    assert client.get("/agenda", headers=headers(ana)).json() == [contact.json()]
    assert client.get("/agenda", headers=headers(bob)).json() == []
    assert client.get(f"/agenda/{contact_id}", headers=headers(bob)).status_code == 404
    assert client.put(f"/agenda/{contact_id}", json={"nombre": "Intruso"}, headers=headers(bob)).status_code == 404
    assert client.delete(f"/agenda/{contact_id}", headers=headers(bob)).status_code == 404
    assert client.put(f"/agenda/{contact_id}", json={"nombre": "María Actualizada"}, headers=headers(ana)).json()["nombre"] == "María Actualizada"
    assert client.put(f"/agenda/{contact_id}", json={"mail": None}, headers=headers(ana)).status_code == 422
    assert client.put(f"/agenda/{contact_id}", json={"telefono": "abc"}, headers=headers(ana)).status_code == 422
    assert client.post("/agenda", json={**payload, "telefono": "abc"}, headers=headers(ana)).status_code == 422
    assert client.delete(f"/agenda/{contact_id}", headers=headers(ana)).status_code == 200
    assert client.get(f"/agenda/{contact_id}", headers=headers(ana)).status_code == 404


def test_web_form_login_csrf_and_ownership(client):
    register(client, "ana", "ana@example.com")
    register(client, "bob", "bob@example.com")
    assert client.get("/views/agenda", follow_redirects=False).headers["location"] == "/views/login"
    assert client.post("/views/login", data={"username": "ana", "password": "mal"}).status_code == 401
    login = client.post(
        "/views/login", data={"username": "ana", "password": "ClaveSegura123"}, follow_redirects=False
    )
    assert login.status_code == 303
    assert "httponly" in login.headers["set-cookie"].lower()
    page = client.get("/views/agenda")
    assert page.status_code == 200
    assert "Todavía no tienes contactos" in page.text
    csrf = re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)
    data = {"nombre": "María López", "telefono": "8123456789", "mail": "maria@example.com", "csrf": csrf}
    assert client.post("/views/agenda", data={**data, "csrf": "incorrecto"}).status_code == 403
    assert client.post("/views/agenda", data=data, follow_redirects=False).status_code == 303
    assert "María López" in client.get("/views/agenda").text
    assert client.post("/views/logout", data={"csrf": csrf}, follow_redirects=False).status_code == 303
    assert client.post("/views/login", data={"username": "bob", "password": "ClaveSegura123"}).status_code == 200
    assert "María López" not in client.get("/views/agenda").text


def test_docs_and_middleware(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    assert client.get("/docs").status_code == 200

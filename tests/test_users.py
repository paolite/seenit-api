"""
Tests de integración para las rutas de /users.

Cubre registro, login, perfil, actualización y el sistema de follows,
centrándose en los casos límite (validaciones, duplicados, auth, 404/409...).
"""


# ---------------------------------------------------------------------------
# POST /users/registro
# ---------------------------------------------------------------------------


def test_registro_ok_devuelve_userpublic_sin_password(client):
    r = client.post(
        "/users/registro",
        json={"name": "Alice", "email": "alice@example.com", "password": "secret123"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "alice@example.com"
    assert data["name"] == "Alice"
    assert "id" in data and data["id"] is not None
    assert "fecha_alta" in data
    # El password (ni en claro ni hasheado) NUNCA debe salir en la respuesta.
    assert "password" not in data
    assert "hashed_password" not in data


def test_registro_email_duplicado_da_400(client):
    payload = {"name": "Alice", "email": "dup@example.com", "password": "secret123"}
    assert client.post("/users/registro", json=payload).status_code == 201
    # Segundo registro con el mismo email.
    r = client.post("/users/registro", json=payload)
    assert r.status_code == 400
    assert "correo" in r.json()["detail"].lower()


def test_registro_email_sin_arroba_da_422(client):
    r = client.post(
        "/users/registro",
        json={"name": "Alice", "email": "sin-arroba", "password": "secret123"},
    )
    assert r.status_code == 422


def test_registro_password_demasiado_corta_da_422(client):
    r = client.post(
        "/users/registro",
        json={"name": "Alice", "email": "a@example.com", "password": "123"},
    )
    assert r.status_code == 422


def test_registro_nombre_demasiado_corto_da_422(client):
    r = client.post(
        "/users/registro",
        json={"name": "A", "email": "a@example.com", "password": "secret123"},
    )
    assert r.status_code == 422


def test_registro_nombre_demasiado_largo_da_422(client):
    r = client.post(
        "/users/registro",
        json={"name": "A" * 21, "email": "a@example.com", "password": "secret123"},
    )
    assert r.status_code == 422


def test_registro_falta_campo_obligatorio_da_422(client):
    # Sin password.
    r = client.post(
        "/users/registro",
        json={"name": "Alice", "email": "a@example.com"},
    )
    assert r.status_code == 422


def test_registro_body_vacio_da_422(client):
    r = client.post("/users/registro", json={})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /users/login
# ---------------------------------------------------------------------------


def test_login_ok_devuelve_token_bearer(client, make_user):
    make_user(email="login@example.com", password="secret123")
    r = client.post(
        "/users/login",
        data={"username": "login@example.com", "password": "secret123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_email_inexistente_da_401(client):
    r = client.post(
        "/users/login",
        data={"username": "noexiste@example.com", "password": "secret123"},
    )
    assert r.status_code == 401


def test_login_password_incorrecta_da_401(client, make_user):
    make_user(email="login@example.com", password="secret123")
    r = client.post(
        "/users/login",
        data={"username": "login@example.com", "password": "OTRA-MAL"},
    )
    assert r.status_code == 401
    assert "incorrecta" in r.json()["detail"].lower()


def test_login_sin_datos_da_422(client):
    # OAuth2PasswordRequestForm exige username y password.
    r = client.post("/users/login", data={})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/  (listar usuarios, requiere auth)
# ---------------------------------------------------------------------------


def test_listar_usuarios_requiere_auth(client):
    r = client.get("/users/")
    assert r.status_code == 401


def test_listar_usuarios_con_token_invalido_da_401(client):
    r = client.get("/users/", headers={"Authorization": "Bearer token-basura"})
    assert r.status_code == 401


def test_listar_usuarios_ok(client, make_user):
    a = make_user(name="Ana")
    make_user(name="Bob")
    r = client.get("/users/", headers=a["headers"])
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert all("hashed_password" not in u for u in data)


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------


def test_me_ok(client, user):
    r = client.get("/users/me", headers=user["headers"])
    assert r.status_code == 200
    assert r.json()["email"] == user["email"]


def test_me_sin_auth_da_401(client):
    assert client.get("/users/me").status_code == 401


def test_me_con_esquema_no_bearer_da_401(client, user):
    # Authorization mal formado (sin "Bearer ").
    r = client.get("/users/me", headers={"Authorization": user["token"]})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /users/me
# ---------------------------------------------------------------------------


def test_patch_me_actualiza_nombre_y_bio(client, user):
    r = client.patch(
        "/users/me",
        json={"name": "NuevoNombre", "bio": "mi bio"},
        headers=user["headers"],
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "NuevoNombre"
    assert data["bio"] == "mi bio"


def test_patch_me_parcial_solo_bio(client, user):
    r = client.patch("/users/me", json={"bio": "solo bio"}, headers=user["headers"])
    assert r.status_code == 200
    assert r.json()["bio"] == "solo bio"
    # El nombre no se tocó.
    assert r.json()["name"] == user["name"]


def test_patch_me_body_vacio_no_rompe(client, user):
    # exclude_unset=True => no cambia nada, debe seguir devolviendo 200.
    r = client.patch("/users/me", json={}, headers=user["headers"])
    assert r.status_code == 200
    assert r.json()["email"] == user["email"]


def test_patch_me_sin_auth_da_401(client):
    assert client.patch("/users/me", json={"bio": "x"}).status_code == 401


# ---------------------------------------------------------------------------
# POST /users/{account_id}/follow
# ---------------------------------------------------------------------------


def test_follow_ok(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    r = client.post(f"/users/{b['id']}/follow", headers=a["headers"])
    assert r.status_code == 200
    data = r.json()
    assert data["follower_id"] == a["id"]
    assert data["followed_id"] == b["id"]


def test_follow_a_si_mismo_da_400(client, user):
    r = client.post(f"/users/{user['id']}/follow", headers=user["headers"])
    assert r.status_code == 400
    assert "ti mismo" in r.json()["detail"].lower()


def test_follow_duplicado_da_409(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    assert (
        client.post(f"/users/{b['id']}/follow", headers=a["headers"]).status_code == 200
    )
    r = client.post(f"/users/{b['id']}/follow", headers=a["headers"])
    assert r.status_code == 409


def test_follow_sin_auth_da_401(client, user):
    assert client.post(f"/users/{user['id']}/follow").status_code == 401


# ---------------------------------------------------------------------------
# DELETE /users/{account_id}/follow  (unfollow)
# ---------------------------------------------------------------------------


def test_unfollow_ok(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    client.post(f"/users/{b['id']}/follow", headers=a["headers"])
    r = client.request("DELETE", f"/users/{b['id']}/follow", headers=a["headers"])
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_unfollow_sin_seguir_da_404(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    r = client.request("DELETE", f"/users/{b['id']}/follow", headers=a["headers"])
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /users/me/followers/{follower_id}
# ---------------------------------------------------------------------------


def test_eliminar_seguidor_ok(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    # b sigue a a.
    client.post(f"/users/{a['id']}/follow", headers=b["headers"])
    # a elimina a b de sus seguidores.
    r = client.request("DELETE", f"/users/me/followers/{b['id']}", headers=a["headers"])
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_eliminar_seguidor_que_no_te_sigue_da_404(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    r = client.request("DELETE", f"/users/me/followers/{b['id']}", headers=a["headers"])
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /users/me/followers  y  GET /users/me/followed
# ---------------------------------------------------------------------------


def test_listar_seguidores(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    c = make_user(name="Cris")
    # b y c siguen a a.
    client.post(f"/users/{a['id']}/follow", headers=b["headers"])
    client.post(f"/users/{a['id']}/follow", headers=c["headers"])
    r = client.get("/users/me/followers", headers=a["headers"])
    assert r.status_code == 200
    ids = {u["id"] for u in r.json()}
    assert ids == {b["id"], c["id"]}


def test_listar_seguidos(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    c = make_user(name="Cris")
    # a sigue a b y c.
    client.post(f"/users/{b['id']}/follow", headers=a["headers"])
    client.post(f"/users/{c['id']}/follow", headers=a["headers"])
    r = client.get("/users/me/followed", headers=a["headers"])
    assert r.status_code == 200
    ids = {u["id"] for u in r.json()}
    assert ids == {b["id"], c["id"]}


def test_seguidores_vacio_al_inicio(client, user):
    r = client.get("/users/me/followers", headers=user["headers"])
    assert r.status_code == 200
    assert r.json() == []


def test_followers_y_followed_requieren_auth(client):
    assert client.get("/users/me/followers").status_code == 401
    assert client.get("/users/me/followed").status_code == 401

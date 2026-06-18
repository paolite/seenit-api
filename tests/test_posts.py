"""
Tests de integración para las rutas de /posts.

Cubre creación, listado, actualización/borrado, 404 y likes/dislikes.

OJO: a diferencia de /reviews y /comments, las rutas PATCH y DELETE de /posts
NO comprueban que el post sea del usuario. Eso se documenta abajo con tests
que reflejan el comportamiento ACTUAL (cualquier usuario autenticado puede
editar/borrar el post de otro). Si en el futuro se añade la comprobación de
propietario, esos tests habrá que cambiarlos a esperar 403.
"""


# ---------------------------------------------------------------------------
# POST /posts/
# ---------------------------------------------------------------------------


def test_crear_post_ok(client, auth_headers):
    r = client.post("/posts/", json={"text": "Hola"}, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == "Hola"
    assert data["user_id"] is not None


def test_crear_post_vacio_permitido(client, auth_headers):
    # text e image_url son ambos opcionales -> un post vacío se acepta.
    r = client.post("/posts/", json={}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["text"] is None
    assert r.json()["image_url"] is None


def test_crear_post_sin_auth_da_401(client):
    assert client.post("/posts/", json={"text": "Hola"}).status_code == 401


# ---------------------------------------------------------------------------
# GET /posts/
# ---------------------------------------------------------------------------


def test_listar_posts_requiere_auth(client):
    assert client.get("/posts/").status_code == 401


def test_listar_posts_ok(client, auth_headers, make_post):
    make_post(auth_headers, text="uno")
    make_post(auth_headers, text="dos")
    r = client.get("/posts/", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 2


# ---------------------------------------------------------------------------
# PATCH /posts/{id}
# ---------------------------------------------------------------------------


def test_actualizar_post_ok(client, auth_headers, make_post):
    post = make_post(auth_headers, text="viejo")
    r = client.patch(
        f"/posts/{post['id']}", json={"text": "nuevo"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["text"] == "nuevo"


def test_actualizar_post_inexistente_da_404(client, auth_headers):
    r = client.patch("/posts/99999", json={"text": "x"}, headers=auth_headers)
    assert r.status_code == 404


def test_actualizar_post_sin_auth_da_401(client, auth_headers, make_post):
    post = make_post(auth_headers)
    assert client.patch(f"/posts/{post['id']}", json={"text": "x"}).status_code == 401


def test_actualizar_post_ajeno_no_se_bloquea(client, make_user, make_post):
    # Comportamiento ACTUAL: no hay check de propietario -> 200.
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    post = make_post(a["headers"], text="de A")
    r = client.patch(
        f"/posts/{post['id']}", json={"text": "editado por B"}, headers=b["headers"]
    )
    assert r.status_code == 200
    assert r.json()["text"] == "editado por B"


# ---------------------------------------------------------------------------
# DELETE /posts/{id}
# ---------------------------------------------------------------------------


def test_borrar_post_ok(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.delete(f"/posts/{post['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_borrar_post_inexistente_da_404(client, auth_headers):
    r = client.delete("/posts/99999", headers=auth_headers)
    assert r.status_code == 404


def test_borrar_post_ajeno_no_se_bloquea(client, make_user, make_post):
    # Comportamiento ACTUAL: cualquiera autenticado puede borrar -> 200.
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    post = make_post(a["headers"], text="de A")
    r = client.delete(f"/posts/{post['id']}", headers=b["headers"])
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Likes  /posts/{id}/like
# ---------------------------------------------------------------------------


def test_like_post_ok(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.post(f"/posts/{post['id']}/like", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["post_id"] == post["id"]


def test_like_post_duplicado_da_409(client, auth_headers, make_post):
    post = make_post(auth_headers)
    client.post(f"/posts/{post['id']}/like", headers=auth_headers)
    r = client.post(f"/posts/{post['id']}/like", headers=auth_headers)
    assert r.status_code == 409


def test_listar_likes_post(client, make_user, make_post):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    post = make_post(a["headers"])
    client.post(f"/posts/{post['id']}/like", headers=a["headers"])
    client.post(f"/posts/{post['id']}/like", headers=b["headers"])
    r = client.get(f"/posts/{post['id']}/like", headers=a["headers"])
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_quitar_like_post_ok(client, auth_headers, make_post):
    post = make_post(auth_headers)
    client.post(f"/posts/{post['id']}/like", headers=auth_headers)
    r = client.delete(f"/posts/{post['id']}/like", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_quitar_like_post_sin_haberlo_dado_da_404(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.delete(f"/posts/{post['id']}/like", headers=auth_headers)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Dislikes  /posts/{id}/dislike  /dislikes
# ---------------------------------------------------------------------------


def test_dislike_post_ok(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.post(f"/posts/{post['id']}/dislike", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["post_id"] == post["id"]


def test_dislike_post_duplicado_da_409(client, auth_headers, make_post):
    post = make_post(auth_headers)
    client.post(f"/posts/{post['id']}/dislike", headers=auth_headers)
    r = client.post(f"/posts/{post['id']}/dislike", headers=auth_headers)
    assert r.status_code == 409


def test_listar_dislikes_post(client, auth_headers, make_post):
    post = make_post(auth_headers)
    client.post(f"/posts/{post['id']}/dislike", headers=auth_headers)
    r = client.get(f"/posts/{post['id']}/dislikes", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_quitar_dislike_post_sin_haberlo_dado_da_404(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.delete(f"/posts/{post['id']}/dislike", headers=auth_headers)
    assert r.status_code == 404


def test_like_post_sin_auth_da_401(client, auth_headers, make_post):
    post = make_post(auth_headers)
    assert client.post(f"/posts/{post['id']}/like").status_code == 401

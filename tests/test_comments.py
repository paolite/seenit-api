"""
Tests de integración para las rutas de comentarios.

Rutas (sin prefijo de router):
    POST   /posts/{post_id}/comments
    POST   /reviews/{review_id}/comments
    PATCH  /posts/{post_id}/comments/{comment_id}
    PATCH  /reviews/{review_id}/comments/{comment_id}
    DELETE /posts/{post_id}/comments/{comment_id}
    DELETE /reviews/{review_id}/comments/{comment_id}

Cubre validación de texto, permisos de propietario (403), 404 y auth.
"""


# ---------------------------------------------------------------------------
# POST /posts/{post_id}/comments
# ---------------------------------------------------------------------------


def test_comentar_post_ok(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.post(
        f"/posts/{post['id']}/comments",
        json={"text": "Buen post"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == "Buen post"
    assert data["post_id"] == post["id"]
    assert data["review_id"] is None
    assert data["user_id"] is not None


def test_comentar_post_texto_vacio_da_422(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.post(
        f"/posts/{post['id']}/comments",
        json={"text": ""},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_comentar_post_texto_demasiado_largo_da_422(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.post(
        f"/posts/{post['id']}/comments",
        json={"text": "x" * 1001},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_comentar_post_sin_auth_da_401(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.post(f"/posts/{post['id']}/comments", json={"text": "hola"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# POST /reviews/{review_id}/comments
# ---------------------------------------------------------------------------


def test_comentar_review_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.post(
        f"/reviews/{review['id']}/comments",
        json={"text": "De acuerdo"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["review_id"] == review["id"]
    assert data["post_id"] is None


# ---------------------------------------------------------------------------
# PATCH /posts/{post_id}/comments/{comment_id}
# ---------------------------------------------------------------------------


def _crear_comentario_post(client, headers, post_id, text="original"):
    r = client.post(f"/posts/{post_id}/comments", json={"text": text}, headers=headers)
    assert r.status_code == 200
    return r.json()


def test_editar_comentario_post_propio_ok(client, auth_headers, make_post):
    post = make_post(auth_headers)
    comment = _crear_comentario_post(client, auth_headers, post["id"])
    r = client.patch(
        f"/posts/{post['id']}/comments/{comment['id']}",
        json={"text": "editado"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["text"] == "editado"


def test_editar_comentario_post_inexistente_da_404(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.patch(
        f"/posts/{post['id']}/comments/99999",
        json={"text": "x"},
        headers=auth_headers,
    )
    assert r.status_code == 404


def test_editar_comentario_post_ajeno_da_403(client, make_user, make_post):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    post = make_post(a["headers"])
    comment = _crear_comentario_post(client, a["headers"], post["id"])
    r = client.patch(
        f"/posts/{post['id']}/comments/{comment['id']}",
        json={"text": "intruso"},
        headers=b["headers"],
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /reviews/{review_id}/comments/{comment_id}
# ---------------------------------------------------------------------------


def test_editar_comentario_review_inexistente_da_404(
    client, auth_headers, make_movie, make_review
):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.patch(
        f"/reviews/{review['id']}/comments/99999",
        json={"text": "x"},
        headers=auth_headers,
    )
    assert r.status_code == 404


def test_editar_comentario_review_propio_ok(
    client, auth_headers, make_movie, make_review
):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    comment = client.post(
        f"/reviews/{review['id']}/comments",
        json={"text": "original"},
        headers=auth_headers,
    ).json()
    r = client.patch(
        f"/reviews/{review['id']}/comments/{comment['id']}",
        json={"text": "editado"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["text"] == "editado"


# ---------------------------------------------------------------------------
# DELETE /posts/{post_id}/comments/{comment_id}
# ---------------------------------------------------------------------------


def test_borrar_comentario_post_propio_ok(client, auth_headers, make_post):
    post = make_post(auth_headers)
    comment = _crear_comentario_post(client, auth_headers, post["id"])
    r = client.delete(
        f"/posts/{post['id']}/comments/{comment['id']}", headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_borrar_comentario_post_inexistente_da_404(client, auth_headers, make_post):
    post = make_post(auth_headers)
    r = client.delete(f"/posts/{post['id']}/comments/99999", headers=auth_headers)
    assert r.status_code == 404


def test_borrar_comentario_post_ajeno_da_403(client, make_user, make_post):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    post = make_post(a["headers"])
    comment = _crear_comentario_post(client, a["headers"], post["id"])
    r = client.delete(
        f"/posts/{post['id']}/comments/{comment['id']}", headers=b["headers"]
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /reviews/{review_id}/comments/{comment_id}
# ---------------------------------------------------------------------------


def test_borrar_comentario_review_inexistente_da_404(
    client, auth_headers, make_movie, make_review
):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.delete(f"/reviews/{review['id']}/comments/99999", headers=auth_headers)
    assert r.status_code == 404


def test_comentario_de_post_se_puede_borrar_via_ruta_de_review(
    client, auth_headers, make_post
):
    # Comportamiento ACTUAL: el endpoint de borrado solo mira comment_id y
    # propietario, NO valida que el comentario pertenezca de verdad a la review
    # de la URL. Por eso un comentario de un post se puede borrar usando la
    # ruta de reviews. Se documenta como caso límite de acoplamiento débil.
    post = make_post(auth_headers)
    comment = _crear_comentario_post(client, auth_headers, post["id"])
    r = client.delete(f"/reviews/123/comments/{comment['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"ok": True}

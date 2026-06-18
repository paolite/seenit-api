"""
Tests de integración para las rutas de /reviews.

Cubre creación (con duplicado 409 y rating fuera de rango), permisos de
propietario (403), 404, y el sistema de likes/dislikes.
"""


# ---------------------------------------------------------------------------
# POST /reviews/
# ---------------------------------------------------------------------------


def test_crear_review_ok(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    r = client.post(
        "/reviews/",
        json={"movie_id": movie["id"], "rating": 8, "text": "Genial"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["rating"] == 8
    assert data["movie_id"] == movie["id"]
    # El user_id se infiere del token, no del body.
    assert data["user_id"] is not None


def test_crear_review_duplicada_misma_pelicula_da_409(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    client.post(
        "/reviews/",
        json={"movie_id": movie["id"], "rating": 8},
        headers=auth_headers,
    )
    r = client.post(
        "/reviews/",
        json={"movie_id": movie["id"], "rating": 5},
        headers=auth_headers,
    )
    assert r.status_code == 409


def test_dos_usuarios_pueden_valorar_la_misma_pelicula(client, make_user, make_movie):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    movie = make_movie(a["headers"])
    assert (
        client.post(
            "/reviews/",
            json={"movie_id": movie["id"], "rating": 8},
            headers=a["headers"],
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/reviews/",
            json={"movie_id": movie["id"], "rating": 3},
            headers=b["headers"],
        ).status_code
        == 200
    )


def test_crear_review_rating_mayor_que_10_da_422(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    r = client.post(
        "/reviews/",
        json={"movie_id": movie["id"], "rating": 11},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_crear_review_rating_negativo_da_422(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    r = client.post(
        "/reviews/",
        json={"movie_id": movie["id"], "rating": -1},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_crear_review_sin_movie_id_da_422(client, auth_headers):
    r = client.post("/reviews/", json={"rating": 8}, headers=auth_headers)
    assert r.status_code == 422


def test_crear_review_sin_auth_da_401(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    r = client.post("/reviews/", json={"movie_id": movie["id"], "rating": 8})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /reviews/  y  GET /reviews/{id}   (NO requieren auth)
# ---------------------------------------------------------------------------


def test_listar_reviews_sin_auth_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    make_review(auth_headers, movie_id=movie["id"])
    r = client.get("/reviews/")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_review_por_id_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.get(f"/reviews/{review['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == review["id"]


def test_get_review_inexistente_da_404(client):
    r = client.get("/reviews/99999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /reviews/{id}
# ---------------------------------------------------------------------------


def test_actualizar_review_propia_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"], rating=5)
    r = client.patch(
        f"/reviews/{review['id']}",
        json={"rating": 9, "text": "Mejoró"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["rating"] == 9
    assert r.json()["text"] == "Mejoró"


def test_actualizar_review_inexistente_da_404(client, auth_headers):
    r = client.patch("/reviews/99999", json={"rating": 9}, headers=auth_headers)
    assert r.status_code == 404


def test_actualizar_review_ajena_da_403(client, make_user, make_movie, make_review):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    movie = make_movie(a["headers"])
    review = make_review(a["headers"], movie_id=movie["id"])
    # b intenta editar la review de a.
    r = client.patch(
        f"/reviews/{review['id']}",
        json={"rating": 1},
        headers=b["headers"],
    )
    assert r.status_code == 403


def test_actualizar_review_rating_invalido_da_422(
    client, auth_headers, make_movie, make_review
):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.patch(
        f"/reviews/{review['id']}",
        json={"rating": 99},
        headers=auth_headers,
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /reviews/{id}
# ---------------------------------------------------------------------------


def test_borrar_review_propia_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.delete(f"/reviews/{review['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_borrar_review_inexistente_da_404(client, auth_headers):
    r = client.delete("/reviews/99999", headers=auth_headers)
    assert r.status_code == 404


def test_borrar_review_ajena_da_403(client, make_user, make_movie, make_review):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    movie = make_movie(a["headers"])
    review = make_review(a["headers"], movie_id=movie["id"])
    r = client.delete(f"/reviews/{review['id']}", headers=b["headers"])
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Likes  /reviews/{id}/like  /likes
# ---------------------------------------------------------------------------


def test_like_review_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.post(f"/reviews/{review['id']}/like", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["review_id"] == review["id"]


def test_like_review_duplicado_da_409(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    client.post(f"/reviews/{review['id']}/like", headers=auth_headers)
    r = client.post(f"/reviews/{review['id']}/like", headers=auth_headers)
    assert r.status_code == 409


def test_listar_likes_review(client, make_user, make_movie, make_review):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    movie = make_movie(a["headers"])
    review = make_review(a["headers"], movie_id=movie["id"])
    client.post(f"/reviews/{review['id']}/like", headers=a["headers"])
    client.post(f"/reviews/{review['id']}/like", headers=b["headers"])
    r = client.get(f"/reviews/{review['id']}/likes", headers=a["headers"])
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_quitar_like_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    client.post(f"/reviews/{review['id']}/like", headers=auth_headers)
    r = client.delete(f"/reviews/{review['id']}/like", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_quitar_like_sin_haberlo_dado_da_404(
    client, auth_headers, make_movie, make_review
):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.delete(f"/reviews/{review['id']}/like", headers=auth_headers)
    assert r.status_code == 404


def test_like_review_sin_auth_da_401(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    assert client.post(f"/reviews/{review['id']}/like").status_code == 401


# ---------------------------------------------------------------------------
# Dislikes  /reviews/{id}/dislike  /dislikes
# ---------------------------------------------------------------------------


def test_dislike_review_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.post(f"/reviews/{review['id']}/dislike", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["review_id"] == review["id"]


def test_dislike_review_duplicado_da_409(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    client.post(f"/reviews/{review['id']}/dislike", headers=auth_headers)
    r = client.post(f"/reviews/{review['id']}/dislike", headers=auth_headers)
    assert r.status_code == 409


def test_quitar_dislike_sin_haberlo_dado_da_404(
    client, auth_headers, make_movie, make_review
):
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    r = client.delete(f"/reviews/{review['id']}/dislike", headers=auth_headers)
    assert r.status_code == 404


def test_like_y_dislike_a_la_vez_estan_permitidos(
    client, auth_headers, make_movie, make_review
):
    # No hay exclusión mutua: el mismo usuario puede dar like Y dislike.
    movie = make_movie(auth_headers)
    review = make_review(auth_headers, movie_id=movie["id"])
    assert (
        client.post(f"/reviews/{review['id']}/like", headers=auth_headers).status_code
        == 200
    )
    assert (
        client.post(
            f"/reviews/{review['id']}/dislike", headers=auth_headers
        ).status_code
        == 200
    )

"""
Tests de integración para las rutas de /movies.

Incluye los casos límite de validación (año fuera de rango, campos
obligatorios), duplicados (409), 404 al actualizar/borrar inexistentes y auth.
"""


# ---------------------------------------------------------------------------
# POST /movies/
# ---------------------------------------------------------------------------


def test_crear_pelicula_ok(client, auth_headers):
    r = client.post(
        "/movies/",
        json={"title": "Inception", "year": 2010, "director": "Nolan"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Inception"
    assert data["id"] is not None


def test_crear_pelicula_sin_auth_da_401(client):
    r = client.post(
        "/movies/",
        json={"title": "Inception", "year": 2010, "director": "Nolan"},
    )
    assert r.status_code == 401


def test_crear_pelicula_duplicada_da_409(client, auth_headers, make_movie):
    make_movie(auth_headers, title="Inception", director="Nolan")
    # Mismo título y mismo director -> duplicado.
    r = client.post(
        "/movies/",
        json={"title": "Inception", "year": 2010, "director": "Nolan"},
        headers=auth_headers,
    )
    assert r.status_code == 409


def test_mismo_titulo_distinto_director_no_es_duplicado(
    client, auth_headers, make_movie
):
    make_movie(auth_headers, title="Inception", director="Nolan")
    r = client.post(
        "/movies/",
        json={"title": "Inception", "year": 1999, "director": "Otro"},
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_crear_pelicula_anio_demasiado_antiguo_da_422(client, auth_headers):
    r = client.post(
        "/movies/",
        json={"title": "Vieja", "year": 1800, "director": "X"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_crear_pelicula_anio_futuro_da_422(client, auth_headers):
    r = client.post(
        "/movies/",
        json={"title": "Futura", "year": 3000, "director": "X"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_crear_pelicula_sin_titulo_da_422(client, auth_headers):
    r = client.post(
        "/movies/",
        json={"year": 2010, "director": "Nolan"},
        headers=auth_headers,
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /movies/
# ---------------------------------------------------------------------------


def test_listar_peliculas_requiere_auth(client):
    assert client.get("/movies/").status_code == 401


def test_listar_peliculas_ok(client, auth_headers, make_movie):
    make_movie(auth_headers, title="A", director="d1")
    make_movie(auth_headers, title="B", director="d2")
    r = client.get("/movies/", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_listar_peliculas_vacio(client, auth_headers):
    r = client.get("/movies/", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# GET /movies/{movie_id}/reviews  (NO requiere auth)
# ---------------------------------------------------------------------------


def test_reviews_de_pelicula_sin_auth_ok(client, auth_headers, make_movie, make_review):
    movie = make_movie(auth_headers)
    make_review(auth_headers, movie_id=movie["id"], rating=7)
    # Esta ruta no exige token.
    r = client.get(f"/movies/{movie['id']}/reviews")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["movie_id"] == movie["id"]


def test_reviews_de_pelicula_inexistente_da_lista_vacia(client):
    # No hay validación de existencia: devuelve [] en vez de 404.
    r = client.get("/movies/99999/reviews")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# PATCH /movies/{movie_id}
# ---------------------------------------------------------------------------


def test_actualizar_pelicula_ok(client, auth_headers, make_movie):
    movie = make_movie(auth_headers, title="Viejo título")
    r = client.patch(
        f"/movies/{movie['id']}",
        json={"title": "Nuevo título"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Nuevo título"


def test_actualizar_pelicula_inexistente_da_404(client, auth_headers):
    r = client.patch(
        "/movies/99999",
        json={"title": "X"},
        headers=auth_headers,
    )
    assert r.status_code == 404


def test_actualizar_pelicula_sin_auth_da_401(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    r = client.patch(f"/movies/{movie['id']}", json={"title": "X"})
    assert r.status_code == 401


def test_actualizar_pelicula_anio_invalido_da_422(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    r = client.patch(
        f"/movies/{movie['id']}",
        json={"year": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /movies/{movie_id}
# ---------------------------------------------------------------------------


def test_borrar_pelicula_ok(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    r = client.delete(f"/movies/{movie['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    # Ya no aparece al listar.
    listado = client.get("/movies/", headers=auth_headers).json()
    assert all(m["id"] != movie["id"] for m in listado)


def test_borrar_pelicula_inexistente_da_404(client, auth_headers):
    r = client.delete("/movies/99999", headers=auth_headers)
    assert r.status_code == 404


def test_borrar_pelicula_sin_auth_da_401(client, auth_headers, make_movie):
    movie = make_movie(auth_headers)
    assert client.delete(f"/movies/{movie['id']}").status_code == 401

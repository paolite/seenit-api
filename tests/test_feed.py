"""
Tests de integración para las rutas de /feed.

Todas requieren auth. Montan grafos de follows y reviews para comprobar que
los feeds y recomendaciones filtran correctamente (solo seguidos, excluir lo
propio, excluir a quien ya sigues, etc.).
"""


def _follow(client, follower, followed_id):
    return client.post(f"/users/{followed_id}/follow", headers=follower["headers"])


# ---------------------------------------------------------------------------
# GET /feed/posts
# ---------------------------------------------------------------------------


def test_feed_posts_muestra_posts_de_seguidos(client, make_user, make_post):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    _follow(client, a, b["id"])
    make_post(b["headers"], text="post de B")

    r = client.get("/feed/posts", headers=a["headers"])
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["text"] == "post de B"
    assert data[0]["user_id"] == b["id"]
    assert data[0]["user_name"] == "Bob"


def test_feed_posts_no_incluye_los_propios(client, make_user, make_post):
    a = make_user(name="Ana")
    # a no sigue a nadie y publica su propio post.
    make_post(a["headers"], text="mio")
    r = client.get("/feed/posts", headers=a["headers"])
    assert r.status_code == 200
    # El feed solo trae posts de seguidos, no los propios.
    assert r.json() == []


def test_feed_posts_no_incluye_posts_de_no_seguidos(client, make_user, make_post):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    # a NO sigue a b.
    make_post(b["headers"], text="post de B")
    r = client.get("/feed/posts", headers=a["headers"])
    assert r.status_code == 200
    assert r.json() == []


def test_feed_posts_sin_auth_da_401(client):
    assert client.get("/feed/posts").status_code == 401


# ---------------------------------------------------------------------------
# GET /feed/reviews
# ---------------------------------------------------------------------------


def test_feed_reviews_muestra_reviews_de_seguidos(
    client, make_user, make_movie, make_review
):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    _follow(client, a, b["id"])
    movie = make_movie(a["headers"])
    make_review(b["headers"], movie_id=movie["id"], rating=9, text="me encantó")

    r = client.get("/feed/reviews", headers=a["headers"])
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["user_id"] == b["id"]
    assert data[0]["rating"] == 9
    assert data[0]["movie_id"] == movie["id"]


def test_feed_reviews_vacio_si_no_sigue_a_nadie(client, make_user):
    a = make_user(name="Ana")
    r = client.get("/feed/reviews", headers=a["headers"])
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# GET /feed/recommend
# ---------------------------------------------------------------------------


def test_recommend_trae_reviews_de_otros_sobre_mis_peliculas(
    client, make_user, make_movie, make_review
):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    movie = make_movie(a["headers"])
    # Ambos valoran la MISMA película (no hace falta seguirse).
    make_review(a["headers"], movie_id=movie["id"], rating=8)
    make_review(b["headers"], movie_id=movie["id"], rating=4, text="a mí no")

    r = client.get("/feed/recommend", headers=a["headers"])
    assert r.status_code == 200
    data = r.json()
    # Solo la review de B (la mía se excluye).
    assert len(data) == 1
    assert data[0]["user_id"] == b["id"]


def test_recommend_excluye_mis_propias_reviews(
    client, make_user, make_movie, make_review
):
    a = make_user(name="Ana")
    movie = make_movie(a["headers"])
    make_review(a["headers"], movie_id=movie["id"], rating=8)
    r = client.get("/feed/recommend", headers=a["headers"])
    assert r.status_code == 200
    # Nadie más valoró esa película -> vacío (y la mía no cuenta).
    assert r.json() == []


def test_recommend_vacio_si_no_tengo_reviews(
    client, make_user, make_movie, make_review
):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    movie = make_movie(b["headers"])
    make_review(b["headers"], movie_id=movie["id"], rating=8)
    # a no ha valorado nada -> no hay base para recomendar.
    r = client.get("/feed/recommend", headers=a["headers"])
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# GET /feed/people  (seguidos de tus seguidos)
# ---------------------------------------------------------------------------


def test_people_recomienda_seguidos_de_mis_seguidos(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    c = make_user(name="Cris")
    # a sigue a b; b sigue a c. -> a debería ver a c recomendado.
    _follow(client, a, b["id"])
    _follow(client, b, c["id"])

    r = client.get("/feed/people", headers=a["headers"])
    assert r.status_code == 200
    nombres = {p["name"] for p in r.json()}
    assert "Cris" in nombres


def test_people_excluye_a_quien_ya_sigo_y_a_mi_mismo(client, make_user):
    a = make_user(name="Ana")
    b = make_user(name="Bob")
    c = make_user(name="Cris")
    # a sigue a b y a c; b sigue a c y a a.
    _follow(client, a, b["id"])
    _follow(client, a, c["id"])
    _follow(client, b, c["id"])
    _follow(client, b, a["id"])

    r = client.get("/feed/people", headers=a["headers"])
    assert r.status_code == 200
    nombres = {p["name"] for p in r.json()}
    # c ya lo sigo -> excluido; a soy yo -> excluido.
    assert "Cris" not in nombres
    assert "Ana" not in nombres


def test_people_vacio_si_no_sigo_a_nadie(client, make_user):
    a = make_user(name="Ana")
    r = client.get("/feed/people", headers=a["headers"])
    assert r.status_code == 200
    assert r.json() == []


def test_people_sin_auth_da_401(client):
    assert client.get("/feed/people").status_code == 401


def test_feed_reviews_sin_auth_da_401(client):
    r= client.get("/feed/reviews")
    assert r.status_code == 401


def test_feed_posts_muestra_post_de_seguido(client, make_user, make_post):
    a= make_user(name= "Ana")
    b= make_user(name= "Bob")
    _follow(client, a, b["id"])
    p= make_post(b["headers"], text= "Me aburro mundo")
    r= client.get("/feed/posts", headers= a["headers"])
    assert r.status_code == 200
    assert len(r.json())== 1
    assert r.json()[0]["user_id"] == 2




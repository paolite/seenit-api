"""
Configuración compartida para los tests de integración de seenit-api.

Estrategia:
- Base de datos de tests en memoria (SQLite `sqlite://`) usando `StaticPool`,
  de forma que todas las conexiones comparten la MISMA base en memoria.
- Se sobreescribe la dependencia `get_session` de la app para que use esa base
  de tests en vez de `seenit.db`.
- Cada test recibe una base limpia (fixture de ámbito `function`), por lo que
  los tests están aislados entre sí.
- `TestClient` (basado en httpx) lanza peticiones HTTP reales contra la app
  en memoria, sin levantar un servidor.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Importamos los modelos para que SQLModel.metadata conozca TODAS las tablas
# antes de hacer create_all (si no, faltarían tablas en la base de tests).
from src import modelos  # noqa: F401
from src.database import get_session
from src.main import app


@pytest.fixture(name="session")
def session_fixture():
    """Crea una base de datos SQLite en memoria nueva para cada test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """TestClient con la dependencia de base de datos sobreescrita."""

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers de autenticación
# ---------------------------------------------------------------------------

# Un contador simple para generar emails únicos cuando no se especifica uno.
_user_counter = {"n": 0}


def _next_email() -> str:
    _user_counter["n"] += 1
    return f"user{_user_counter['n']}@example.com"


@pytest.fixture(autouse=True)
def _reset_user_counter():
    """Reinicia el contador de emails antes de cada test para reproducibilidad."""
    _user_counter["n"] = 0
    yield


@pytest.fixture
def make_user(client: TestClient):
    """
    Factory que registra un usuario, hace login y devuelve un dict con sus datos:
    {id, name, email, password, token, headers}.

    Permite crear varios usuarios distintos en un mismo test:
        a = make_user()
        b = make_user(name="Bob")
    """

    def _make_user(name="Tester", email=None, password="secret123", bio=None):
        email = email or _next_email()
        payload = {"name": name, "email": email, "password": password}
        if bio is not None:
            payload["bio"] = bio

        r = client.post("/users/registro", json=payload)
        assert r.status_code == 201, f"registro falló: {r.text}"
        user = r.json()

        r = client.post(
            "/users/login",
            data={"username": email, "password": password},
        )
        assert r.status_code == 200, f"login falló: {r.text}"
        token = r.json()["access_token"]

        return {
            "id": user["id"],
            "name": name,
            "email": email,
            "password": password,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    return _make_user


@pytest.fixture
def user(make_user):
    """Un usuario ya registrado y autenticado, listo para usar."""
    return make_user()


@pytest.fixture
def auth_headers(user):
    """Cabeceras Authorization de un usuario autenticado."""
    return user["headers"]


# ---------------------------------------------------------------------------
# Helpers de creación de recursos (para no repetir en cada test)
# ---------------------------------------------------------------------------


@pytest.fixture
def make_movie(client: TestClient):
    """Crea una película (requiere auth) y devuelve su JSON."""

    def _make_movie(
        headers,
        title="Inception",
        year=2010,
        director="Nolan",
        sinopsis=None,
        poster_url=None,
    ):
        payload = {"title": title, "year": year, "director": director}
        if sinopsis is not None:
            payload["sinopsis"] = sinopsis
        if poster_url is not None:
            payload["poster_url"] = poster_url
        r = client.post("/movies/", json=payload, headers=headers)
        assert r.status_code == 200, f"crear película falló: {r.text}"
        return r.json()

    return _make_movie


@pytest.fixture
def make_review(client: TestClient):
    """Crea una review sobre una película (requiere auth) y devuelve su JSON."""

    def _make_review(headers, movie_id, rating=8, text="Buena"):
        payload = {"movie_id": movie_id, "rating": rating, "text": text}
        r = client.post("/reviews/", json=payload, headers=headers)
        assert r.status_code == 200, f"crear review falló: {r.text}"
        return r.json()

    return _make_review


@pytest.fixture
def make_post(client: TestClient):
    """Crea un post (requiere auth) y devuelve su JSON."""

    def _make_post(headers, text="Hola mundo", image_url=None):
        payload = {"text": text}
        if image_url is not None:
            payload["image_url"] = image_url
        r = client.post("/posts/", json=payload, headers=headers)
        assert r.status_code == 200, f"crear post falló: {r.text}"
        return r.json()

    return _make_post

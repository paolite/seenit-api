"""
Tests de los casos límite de autenticación (dependencia get_usuario_actual).

Fabricamos tokens a mano con jose para forzar situaciones que no se pueden
provocar por el flujo normal de login (token caducado, sub inexistente, etc.).
Usamos GET /users/me como ruta representativa protegida por auth.
"""

from datetime import UTC, datetime, timedelta

from jose import jwt

from src.auth import ALGORITHM, SECRET_KEY, hacer_token


def _token(payload: dict) -> str:
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def test_token_con_sub_inexistente_da_401(client):
    # Token bien firmado, pero el email no corresponde a ningún usuario.
    token = hacer_token({"sub": "fantasma@example.com"})
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert "no encontrado" in r.json()["detail"].lower()


def test_token_sin_sub_da_401(client):
    # Sin claim "sub": email = None -> 401.
    exp = datetime.now(UTC) + timedelta(minutes=30)
    token = _token({"foo": "bar", "exp": exp})
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_caducado_da_401(client, make_user):
    make_user(email="real@example.com")
    # exp en el pasado -> jose lanza ExpiredSignatureError -> 401.
    exp = datetime.now(UTC) - timedelta(minutes=1)
    token = _token({"sub": "real@example.com", "exp": exp})
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_firmado_con_otra_clave_da_401(client, make_user):
    make_user(email="real@example.com")
    exp = datetime.now(UTC) + timedelta(minutes=30)
    token = jwt.encode(
        {"sub": "real@example.com", "exp": exp},
        "clave-equivocada",
        algorithm=ALGORITHM,
    )
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_basura_da_401(client):
    r = client.get("/users/me", headers={"Authorization": "Bearer esto-no-es-un-jwt"})
    assert r.status_code == 401

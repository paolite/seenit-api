from datetime import UTC, datetime, timedelta

from fastapi.security import OAuth2PasswordBearer

from jose import jwt

from passlib.context import CryptContext

import os

from dotenv import load_dotenv


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
EXPIRES_MINUTES = 30
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

load_dotenv()
SECRET_KEY= os.getenv("SECRET_KEY")



def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password_plana: str, password_hash: str) -> bool:
    return pwd_context.verify(password_plana, password_hash)


def hacer_token(datos: dict) -> str:
    payload = datos.copy()
    expiracion = datetime.now(UTC) + timedelta(minutes=EXPIRES_MINUTES)
    payload.update({"exp": expiracion})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlmodel import Session, select
from sqlalchemy import func

from src.auth import (
    ALGORITHM,
    SECRET_KEY,
    hacer_token,
    hashear_password,
    oauth2_scheme,
    verificar_password,
)
from src.database import get_session
from src.modelos import Follow, User, UserCreate, UserPublic, UserUpdate, UserProfile, Review, RecommendUser
from src.people_you_may_know import people_you_may_know

router = APIRouter(prefix="/users", tags=["users"])


def get_usuario_actual(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

    except Exception:
        raise HTTPException(
            status_code=401, detail="Token inválido o caducado"
        ) from None

    if email is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = session.exec(select(User).where(User.email == email)).first()
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario


@router.post("/registro", response_model=UserPublic, status_code=201)
def registrar_usuario(
    crear_usuario: UserCreate, session: Session = Depends(get_session)
):
    existe = session.exec(select(User).where(User.email == crear_usuario.email)).first()
    if existe:
        raise HTTPException(status_code=400, detail="Este correo ya ha sido utilizado")

    hashed = hashear_password(crear_usuario.password)
    user = User.model_validate(crear_usuario, update={"hashed_password": hashed})
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/", response_model=list[RecommendUser])
def listar_usuarios(
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_usuario_actual),
    search: str |None = None
):
    if search is None:
        return []

    if search == "":
        return people_you_may_know(session, usuario_actual)


    consulta = select(User)
    if search:
        consulta= consulta.where(User.name.ilike(f"%{search}%"))
    consulta= session.exec(consulta).all()

    return consulta


@router.post("/login", status_code=200)
def iniciar_sesion(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    usuario = session.exec(select(User).where(User.email == form_data.username)).first()
    if usuario is None:
        raise HTTPException(status_code=401, detail="No existe usuario con ese correo")
    es_valida = verificar_password(form_data.password, usuario.hashed_password)
    if not es_valida:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    token = hacer_token({"sub": usuario.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserPublic)
def perfil_propio(usuario_actual: User = Depends(get_usuario_actual)):
    return usuario_actual


@router.patch("/me", response_model=UserPublic)
def actualizar_usuario(
    modelo_actualizar: UserUpdate,
    usuario: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    if usuario is None:
        raise HTTPException(status_code=401, detail="No se encuentra al usuario")
    datos = modelo_actualizar.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(usuario, campo, valor)

    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.get("/{account_id}", response_model= UserProfile)
def watch_account(
    account_id: int,
    session: Session = Depends  (get_session)):

    account= session.get(User, account_id)
    if account is None:
        raise HTTPException(status_code=404,detail= "No existe tal usuario")
    
    n_followers= session.exec(select(func.count()).select_from(Follow).where(Follow.followed_id==account_id)).one()
    n_followed= session.exec(select(func.count()).select_from(Follow).where(Follow.follower_id==account_id)).one()
    n_reviews= session.exec(select(func.count()).select_from(Review).where(Review.user_id==account_id)).one()

    account = UserProfile.model_validate({"n_followers": n_followers, "n_followed": n_followed, "n_reviews": n_reviews, "name": account.name, "bio": account.bio, "profile_pic_url": account.profile_pic_url,"id": account.id })

    return account



@router.post("/{account_id}/follow", response_model=Follow)
def follow(
    account_id: int,
    me: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    if me.id == account_id:
        raise HTTPException(status_code=400, detail="No puedes seguirte a ti mismo")
    existe = session.exec(
        select(Follow).where(
            Follow.follower_id == me.id, Follow.followed_id == account_id
        )
    ).first()
    if existe is not None:
        raise HTTPException(status_code=409, detail="Usted ya sigue a este usuario")
    relacion = Follow.model_validate({"follower_id": me.id, "followed_id": account_id})
    session.add(relacion)
    session.commit()
    session.refresh(relacion)
    return relacion


@router.delete("/{account_id}/follow")
def unfollow(
    account_id: int,
    me: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    existe = session.exec(
        select(Follow).where(
            Follow.follower_id == me.id, Follow.followed_id == account_id
        )
    ).first()
    if existe is None:
        raise HTTPException(status_code=404, detail="El usuario no sigue a esta cuenta")
    session.delete(existe)
    session.commit()
    return {"ok": True}


@router.delete("/me/followers/{follower_id}")
def delete_follower(
    follower_id: int,
    me: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    existe = session.exec(
        select(Follow).where(
            Follow.follower_id == follower_id, Follow.followed_id == me.id
        )
    ).first()
    if existe is None:
        raise HTTPException(
            status_code=404, detail="El usuario seleccionado no te sigue"
        )
    session.delete(existe)
    session.commit()
    return {"ok": True}


@router.get("/me/followers", response_model=list[UserPublic])
def list_followers(
    me: User = Depends(get_usuario_actual), session: Session = Depends(get_session)
):

    followers = session.exec(
        select(User)
        .where(User.id == Follow.follower_id)
        .where(Follow.followed_id == me.id)
    ).all()
    return followers


@router.get("/me/followed", response_model=list[UserPublic])
def list_followed(
    me: User = Depends(get_usuario_actual), session: Session = Depends(get_session)
):

    followed = session.exec(
        select(User).where(
            User.id.in_(select(Follow.followed_id).where(Follow.follower_id == me.id))
        )
    ).all()
    return followed

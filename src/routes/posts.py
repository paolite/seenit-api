from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from src.database import get_session
from src.modelos import CreatePost, DislikePost, LikePost, Post
from src.routes.users import User, get_usuario_actual

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=Post)
def make_post(
    modelo_post: CreatePost,
    usuario_actual: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    nuevo_post = Post.model_validate(modelo_post, update={"user_id": usuario_actual.id})
    session.add(nuevo_post)
    session.commit()
    session.refresh(nuevo_post)
    return nuevo_post


@router.get("/", response_model=list[Post])
def list_posts(
    session: Session = Depends(get_session), user: User = Depends(get_usuario_actual)
):
    posts = session.exec(select(Post)).all()
    return posts


@router.patch("/{post_id}", response_model=Post)
def actualizar_post(
    post: CreatePost,
    post_id: int,
    usuario_actual: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    post_to_update = session.get(Post, post_id)
    if post_to_update is None:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    datos = post.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(post_to_update, campo, valor)
    session.add(post_to_update)
    session.commit()
    session.refresh(post_to_update)
    return post_to_update


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_usuario_actual),
):
    post_to_delete = session.get(Post, post_id)
    if post_to_delete is None:
        raise HTTPException(status_code=404, detail="No se pudo encontrar el post")
    session.delete(post_to_delete)
    session.commit()
    return {"ok": True}


@router.get("/{post_id}/like", response_model=list[LikePost])
def list_likes(
    post_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    likes = session.exec(select(LikePost).where(LikePost.post_id == post_id)).all()
    return likes


@router.post("/{post_id}/like", response_model=LikePost)
def like(
    post_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    existe = session.exec(
        select(LikePost)
        .where(LikePost.post_id == post_id)
        .where(user.id == LikePost.user_id)
    ).first()
    if existe is not None:
        raise HTTPException(status_code=409, detail="Usted ya ha dado like a este Post")
    nuevo_like = LikePost(user_id=user.id, post_id=post_id)
    session.add(nuevo_like)
    session.commit()
    session.refresh(nuevo_like)
    return nuevo_like


@router.delete("/{post_id}/like")
def quit_like(
    post_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    existe = session.exec(
        select(LikePost)
        .where(LikePost.post_id == post_id)
        .where(user.id == LikePost.user_id)
    ).first()
    if existe is None:
        raise HTTPException(status_code=404, detail="No se ha dado like a este post")

    session.delete(existe)
    session.commit()
    return {"ok": True}


@router.get("/{post_id}/dislikes", response_model=list[DislikePost])
def list_dislikes(
    post_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    dislikes = session.exec(
        select(DislikePost).where(DislikePost.post_id == post_id)
    ).all()
    return dislikes


@router.post("/{post_id}/dislike", response_model=DislikePost)
def dislike(
    post_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    existe = session.exec(
        select(DislikePost)
        .where(DislikePost.post_id == post_id)
        .where(user.id == DislikePost.user_id)
    ).first()
    if existe is not None:
        raise HTTPException(
            status_code=409, detail="Usted ya ha dado dislike a este Post"
        )
    nuevo_dislike = DislikePost(user_id=user.id, post_id=post_id)
    session.add(nuevo_dislike)
    session.commit()
    session.refresh(nuevo_dislike)
    return nuevo_dislike


@router.delete("/{post_id}/dislike")
def quit_dislike(
    post_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    existe = session.exec(
        select(DislikePost)
        .where(DislikePost.post_id == post_id)
        .where(user.id == DislikePost.user_id)
    ).first()
    if existe is None:
        raise HTTPException(status_code=404, detail="No se ha dado dislike a este post")

    session.delete(existe)
    session.commit()
    return {"ok": True}

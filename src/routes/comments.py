from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.database import get_session
from src.modelos import Comment, CommentCreate, User
from src.routes.users import get_usuario_actual

router = APIRouter(tags=["Comments"])


@router.post("/posts/{post_id}/comments", response_model=Comment)
def create_comment_to_post(
    post_id: int,
    comment: CommentCreate,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    comment_to_post = Comment.model_validate(
        comment, update={"user_id": user.id, "post_id": post_id}
    )
    session.add(comment_to_post)
    session.commit()
    session.refresh(comment_to_post)
    return comment_to_post


@router.post("/reviews/{review_id}/comments", response_model=Comment)
def create_comment_to_review(
    review_id: int,
    comment: CommentCreate,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    comment_to_post = Comment.model_validate(
        comment, update={"user_id": user.id, "review_id": review_id}
    )
    session.add(comment_to_post)
    session.commit()
    session.refresh(comment_to_post)
    return comment_to_post


@router.patch("/posts/{post_id}/comments/{comment_id}", response_model=Comment)
def update_comment_post(
    post_id: int,
    comment_id: int,
    comment: CommentCreate,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    comment_to_update = session.get(Comment, comment_id)

    if comment_to_update is None:
        raise HTTPException(status_code=404, detail="No se encuentra el comentario")

    if comment_to_update.user_id != user.id:
        raise HTTPException(status_code=403, detail="El comentario debe de ser tuyo")

    datos = comment.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(comment_to_update, campo, valor)

    session.add(comment_to_update)
    session.commit()
    session.refresh(comment_to_update)
    return comment_to_update


@router.patch("/reviews/{review_id}/comments/{comment_id}", response_model=Comment)
def update_comment_review(
    review_id: int,
    comment_id: int,
    comment: CommentCreate,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    comment_to_update = session.get(Comment, comment_id)
    if comment_to_update is None:
        raise HTTPException(status_code=404, detail="No se encuentra el comentario")
    if comment_to_update.user_id != user.id:
        raise HTTPException(status_code=403, detail="El comentario debe de ser tuyo")

    datos = comment.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(comment_to_update, campo, valor)
    session.add(comment_to_update)
    session.commit()
    session.refresh(comment_to_update)
    return comment_to_update


@router.delete("/posts/{post_id}/comments/{comment_id}")
def delete_comment_post(
    comment_id: int,
    post_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    comment_to_delete = session.get(Comment, comment_id)
    if comment_to_delete is None:
        raise HTTPException(status_code=404, detail="No se encuentra el comentario")
    if comment_to_delete.user_id != user.id:
        raise HTTPException(status_code=403, detail="El comentario debe de ser tuyo")

    session.delete(comment_to_delete)
    session.commit()
    return {"ok": True}


@router.delete("/reviews/{review_id}/comments/{comment_id}")
def delete_comment_review(
    comment_id: int,
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    comment_to_delete = session.get(Comment, comment_id)
    if comment_to_delete is None:
        raise HTTPException(status_code=404, detail="No se encuentra el comentario")
    if comment_to_delete.user_id != user.id:
        raise HTTPException(status_code=403, detail="El comentario debe de ser tuyo")
    session.delete(comment_to_delete)
    session.commit()
    return {"ok": True}

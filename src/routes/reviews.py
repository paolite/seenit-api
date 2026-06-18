from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from src.database import get_session
from src.modelos import CreateReview, DislikeReview, LikeReview, Review, UpdateReview
from src.routes.users import User, get_usuario_actual

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=Review)
def create_review(
    review: CreateReview,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    existe = session.exec(
        select(Review).where(
            Review.movie_id == review.movie_id, Review.user_id == user.id
        )
    ).first()
    if existe is not None:
        raise HTTPException(status_code=409, detail="Esta película ya ha sido valorada")
    nuevaReview = Review.model_validate(review, update={"user_id": user.id})
    session.add(nuevaReview)
    session.commit()
    session.refresh(nuevaReview)
    return nuevaReview


@router.get("/", response_model=list[Review])
def list_reviews(session: Session = Depends(get_session)):

    reviews = session.exec(select(Review)).all()
    return reviews


@router.get("/{review_id}", response_model=Review)
def get_review(review_id: int, session: Session = Depends(get_session)):
    review = session.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="No se ha encontrado la review")
    return review


@router.patch("/{review_id}", response_model=Review)
def update_review(
    review: UpdateReview,
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    review_to_update = session.get(Review, review_id)
    if review_to_update is None:
        raise HTTPException(status_code=404, detail="Review no encontrada")
    if review_to_update.user_id != user.id:
        raise HTTPException(status_code=403, detail="La review no pertenece al usuario")
    datos = review.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(review_to_update, campo, valor)
    session.add(review_to_update)
    session.commit()
    session.refresh(review_to_update)
    return review_to_update


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    review_to_delete = session.get(Review, review_id)
    if review_to_delete is None:
        raise HTTPException(status_code=404, detail="Review no encontrada")
    if review_to_delete.user_id != user.id:
        raise HTTPException(status_code=403, detail="La review no pertenece al usuario")
    session.delete(review_to_delete)
    session.commit()
    return {"ok": True}


@router.get("/{review_id}/likes", response_model=list[LikeReview])
def list_likes(
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    likes = session.exec(
        select(LikeReview).where(LikeReview.review_id == review_id)
    ).all()
    return likes


@router.post("/{review_id}/like", response_model=LikeReview)
def like(
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    existe = session.exec(
        select(LikeReview)
        .where(LikeReview.review_id == review_id)
        .where(user.id == LikeReview.user_id)
    ).first()
    if existe is not None:
        raise HTTPException(
            status_code=409, detail="Usted ya ha dado like a esta review"
        )
    nuevo_like = LikeReview(user_id=user.id, review_id=review_id)
    session.add(nuevo_like)
    session.commit()
    session.refresh(nuevo_like)
    return nuevo_like


@router.delete("/{review_id}/like")
def quit_like(
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    existe = session.exec(
        select(LikeReview)
        .where(LikeReview.review_id == review_id)
        .where(user.id == LikeReview.user_id)
    ).first()
    if existe is None:
        raise HTTPException(status_code=404, detail="No se ha dado like a esta review")

    session.delete(existe)
    session.commit()
    return {"ok": True}


@router.get("/{review_id}/dislikes", response_model=list[DislikeReview])
def list_dislikes(
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    dislikes = session.exec(
        select(DislikeReview).where(DislikeReview.review_id == review_id)
    ).all()
    return dislikes


@router.post("/{review_id}/dislike", response_model=DislikeReview)
def dislike(
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    existe = session.exec(
        select(DislikeReview)
        .where(DislikeReview.review_id == review_id)
        .where(DislikeReview.user_id == user.id)
    ).first()
    if existe is not None:
        raise HTTPException(
            status_code=409, detail="Ya tiene un dislike en esta review"
        )
    new_dislike = DislikeReview(user_id=user.id, review_id=review_id)
    session.add(new_dislike)
    session.commit()
    session.refresh(new_dislike)
    return new_dislike


@router.delete("/{review_id}/dislike")
def quit_dislike(
    review_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):

    existe = session.exec(
        select(DislikeReview)
        .where(DislikeReview.review_id == review_id)
        .where(DislikeReview.user_id == user.id)
    ).first()

    if existe is None:
        raise HTTPException(
            status_code=404, detail="No tiene un dislike en esta review"
        )

    session.delete(existe)
    session.commit()
    return {"ok": True}

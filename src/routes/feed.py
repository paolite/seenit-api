from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from src.database import get_session
from src.modelos import Follow, Post, PostFeed, RecommendUser, Review, ReviewFeed
from src.routes.users import User, get_usuario_actual

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/posts", response_model=list[PostFeed])
def post_feed(
    session: Session = Depends(get_session), me: User = Depends(get_usuario_actual)
):

    posts_followed = session.exec(
        select(Post, User)
        .join(User, User.id == Post.user_id)
        .join(Follow, Follow.followed_id == Post.user_id)
        .where(me.id == Follow.follower_id)
    ).all()

    posts = []

    for post, user in posts_followed:
        full_post = PostFeed(
            user_name=user.name,
            user_pic=user.profile_pic_url,
            user_id=user.id,
            text=post.text,
            image_url=post.image_url,
            fecha=post.fecha,
            id=post.id,
        )
        posts.append(full_post)

    return posts


@router.get("/reviews", response_model=list[ReviewFeed])
def review_feed(
    session: Session = Depends(get_session), me: User = Depends(get_usuario_actual)
):

    reviews_followed = session.exec(
        select(Review, User)
        .join(User, User.id == Review.user_id)
        .join(Follow, Follow.followed_id == User.id)
        .where(Follow.follower_id == me.id)
    )

    reviews = []

    for review, user in reviews_followed:
        full_review = ReviewFeed(
            id=review.id,
            user_name=user.name,
            user_id=user.id,
            user_pic=user.profile_pic_url,
            text=review.text,
            rating=review.rating,
            movie_id=review.movie_id,
            fecha=review.fecha,
        )
        reviews.append(full_review)
    return reviews


@router.get("/recommend", response_model=list[ReviewFeed])
def reviews_like_you(
    session: Session = Depends(get_session), me: User = Depends(get_usuario_actual)
):

    my_id_reviews = session.exec(
        select(Review.movie_id).where(Review.user_id == me.id)
    ).all()
    same_movie_review = session.exec(
        select(Review, User)
        .join(User, User.id == Review.user_id)
        .where(Review.movie_id.in_(my_id_reviews))
        .where(Review.user_id != me.id)
    )

    reviews = []

    for review, user in same_movie_review:
        full_review = ReviewFeed(
            id=review.id,
            user_name=user.name,
            user_id=user.id,
            user_pic=user.profile_pic_url,
            text=review.text,
            rating=review.rating,
            movie_id=review.movie_id,
            fecha=review.fecha,
        )
        reviews.append(full_review)

    return reviews


@router.get("/people", response_model=list[RecommendUser])
def follower_of_followed(
    session: Session = Depends(get_session), me: User = Depends(get_usuario_actual)
):

    followed_ids = session.exec(
        select(Follow.followed_id).where(Follow.follower_id == me.id)
    ).all()

    followed_by_followed = session.exec(
        select(User)
        .join(Follow, User.id== Follow.followed_id)
        .where(Follow.follower_id.in_(followed_ids))
        .where(Follow.followed_id != me.id)
        .where(Follow.followed_id.not_in(followed_ids))
        .distinct()
    )

    people = []

    for followed in followed_by_followed:
        res = RecommendUser(profile_pic_URL=followed.profile_pic_url, name=followed.name, id= followed.id)
        people.append(res)

    return people

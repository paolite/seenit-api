
from sqlmodel import Session, select

from src.modelos import User, Follow, RecommendUser



def people_you_may_know(
    session: Session,
    usuario_actual: User):

    followed_ids = session.exec(
        select(Follow.followed_id).where(Follow.follower_id == usuario_actual.id)
    ).all()

    followed_by_followed = session.exec(
        select(User)
        .join(Follow, User.id== Follow.followed_id)
        .where(Follow.follower_id.in_(followed_ids))
        .where(Follow.followed_id != usuario_actual.id)
        .where(Follow.followed_id.not_in(followed_ids))
        .distinct()
    )

    people = []

    for followed in followed_by_followed:
        res = RecommendUser(profile_pic_url=followed.profile_pic_url, name=followed.name, id= followed.id)
        people.append(res)

    return people


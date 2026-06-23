from datetime import UTC, datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel, UniqueConstraint


class UserBase(SQLModel):
    name: str = Field(..., min_length=2, max_length=20)
    email: str = Field(..., unique=True, index=True, min_length=2, max_length=255)
    bio: str | None = None

    @field_validator("email")
    @classmethod
    def email_arroba(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("El email debe tener un arroba")
        return v


class User(UserBase, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    fecha_alta: datetime = Field(default_factory=lambda: datetime.now(UTC))
    profile_pic_url: str | None = Field(default=None)


class RecommendUser(SQLModel):
    name: str
    profile_pic_url: str | None = Field(default=None)
    id:int


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=30)


class UserPublic(UserBase):
    id: int | None = Field(default=None)
    fecha_alta: datetime


class UserLogin(SQLModel):
    email: str
    password: str


class UserUpdate(SQLModel):
    name: str | None = Field(default=None)
    bio: str | None = Field(default=None)
    email: str | None = Field(default=None)
    profile_pic_url: str | None = Field(default=None)


class UserProfile(SQLModel):
    name: str | None = Field (default=None)
    id: int  | None = Field (default=None)
    profile_pic_url: str  | None = Field (default=None)
    bio:str   | None = Field (default=None)
    n_followers: int | None = Field (default=None)
    n_followed: int | None = Field (default=None)
    n_reviews: int | None = Field (default=None)


class Movie(SQLModel, table=True):
    __tablename__ = "movies"
    id: int | None = Field(default=None, primary_key=True)
    title: str
    year: int = Field(..., ge=1888, le=2100)
    director: str = Field(..., max_length=200)
    sinopsis: str | None = Field(default=None, max_length=500)
    poster_url: str | None = Field(default=None)


class CreateMovie(SQLModel):
    title: str
    year: int = Field(..., ge=1888, le=2100)
    director: str = Field(..., max_length=200)
    sinopsis: str | None = Field(default=None, max_length=500)
    poster_url: str | None = Field(default=None)


class MovieUpdate(SQLModel):
    id: int | None = Field(default=None)
    title: str | None = Field(default=None)
    year: int | None = Field(None, ge=1888, le=2100)
    director: str | None = Field(None, max_length=200)
    sinopsis: str | None = Field(default=None, max_length=500)
    poster_url: str | None = Field(default=None)


class Genre(SQLModel, table=True):
    __tablename__ = "genres"
    name: str
    id: int | None = Field(default=None, primary_key=True)


class MovieGenre(SQLModel, table=True):
    __tablename__ = "movies_genre"
    movie_id: int = Field(foreign_key="movies.id", primary_key=True)
    genre_id: int = Field(foreign_key="genres.id", primary_key=True)


class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("movie_id", "user_id", name="unique_review_movie"),
    )
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    movie_id: int = Field(foreign_key="movies.id")
    rating: int = Field(ge=0, le=10)
    text: str | None = Field(default=None)
    fecha: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CreateReview(SQLModel):
    rating: int = Field(ge=0, le=10)
    text: str | None = Field(default=None)
    movie_id: int


class UpdateReview(SQLModel):
    rating: int | None = Field(None, ge=0, le=10)
    text: str | None = Field(default=None)


class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    id: int | None = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key="users.id")
    review_id: int | None = Field(default=None, foreign_key="reviews.id")
    post_id: int | None = Field(default=None, foreign_key="posts.id")
    text: str = Field(..., min_length=1, max_length=1000)
    fecha: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CommentCreate(SQLModel):
    text: str = Field(..., min_length=1, max_length=1000)


class Post(SQLModel, table=True):
    __tablename__ = "posts"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    text: str | None = Field(default=None)
    image_url: str | None = Field(default=None)
    fecha: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PostFeed(SQLModel):
    id: int
    user_name: str | None = Field(default=None)
    user_id: int | None = Field(default=None)
    user_pic: str | None = Field(default=None)
    text: str | None = Field(default=None)
    image_url: str | None = Field(default=None)
    fecha: datetime


class ReviewFeed(SQLModel):
    id: int
    user_name: str | None = Field(default=None)
    user_id: int | None = Field(default=None)
    user_pic: str | None = Field(default=None)
    text: str | None = Field(default=None)
    rating: int
    movie_id: int
    fecha: datetime


class CreatePost(SQLModel):
    text: str | None = Field(default=None)
    image_url: str | None = Field(default=None)


class Follow(SQLModel, table=True):
    __tablename__ = "follows"

    follower_id: int = Field(foreign_key="users.id", primary_key=True)
    followed_id: int = Field(foreign_key="users.id", primary_key=True)


class LikeReview(SQLModel, table=True):
    __tablename__ = "like_review"
    user_id: int = Field(primary_key=True, foreign_key="users.id")
    review_id: int = Field(primary_key=True, foreign_key="reviews.id")


class LikePost(SQLModel, table=True):
    __tablename__ = "like_post"
    user_id: int = Field(primary_key=True, foreign_key="users.id")
    post_id: int = Field(primary_key=True, foreign_key="posts.id")


class DislikeReview(SQLModel, table=True):
    __tablename__ = "dislike_review"
    user_id: int = Field(primary_key=True, foreign_key="users.id")
    review_id: int = Field(primary_key=True, foreign_key="reviews.id")


class DislikePost(SQLModel, table=True):
    __tablename__ = "dislike_post"
    user_id: int = Field(primary_key=True, foreign_key="users.id")
    post_id: int = Field(primary_key=True, foreign_key="posts.id")

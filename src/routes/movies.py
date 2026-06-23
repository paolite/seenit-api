from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from src.database import get_session
from src.modelos import CreateMovie, Movie, MovieUpdate, Review
from src.routes.users import User, get_usuario_actual

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/{movie_id}/reviews", response_model=list[Review])
def reviews_movie(movie_id: int, session: Session = Depends(get_session)):

    movie_reviews = session.exec(
        select(Review).where(Review.movie_id == movie_id)
    ).all()
    return movie_reviews


@router.post("/", response_model=Movie)
def post_movie(
    movie: CreateMovie,
    session: Session = Depends(get_session),
    usuario: User = Depends(get_usuario_actual),
):
    existe = session.exec(
        select(Movie).where(
            Movie.director == movie.director, Movie.title == movie.title
        )
    ).first()
    if existe is not None:
        raise HTTPException(
            status_code=409,
            detail="La película que intenta añadir ya existe en el catálogo",
        )
    new_movie = Movie.model_validate(movie)
    session.add(new_movie)
    session.commit()
    session.refresh(new_movie)
    return new_movie


@router.get("/{movie_id}", response_model= Movie)
def one_movie(
    movie_id: int,
    session: Session = Depends (get_session)):

    movie= session.get(Movie, movie_id)
    if movie is None: 
        raise HTTPException(status_code=404, detail= "La pelicula no existe")
    return movie 
 

@router.get("/", response_model=list[Movie])
def list_movies(
    search: str |None = None,
    session: Session = Depends(get_session)
):
    
    consulta = select(Movie)
    if search:
        consulta = consulta.where(Movie.title.ilike(f"%{search}%"))

    movies = session.exec(consulta).all()
    return movies


@router.patch("/{movie_id}", response_model=Movie)
def update_movie(
    movie: MovieUpdate,
    movie_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    movie_to_update = session.get(Movie, movie_id)
    if movie_to_update is None:
        raise HTTPException(status_code=404, detail="No se encuentra la película")
    datos = movie.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(movie_to_update, campo, valor)

    session.add(movie_to_update)
    session.commit()
    session.refresh(movie_to_update)
    return movie_to_update


@router.delete("/{movie_id}")
def delete_movie(
    movie_id: int,
    user: User = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    movie_to_delete = session.get(Movie, movie_id)
    if movie_to_delete is None:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    session.delete(movie_to_delete)
    session.commit()
    return {"ok": True}



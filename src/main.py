from fastapi import FastAPI

from src.routes import comments, feed, movies, posts, reviews, users

app = FastAPI(title="seenit", description="your criteria is valid", version="1.0.0")


@app.get("/")
def healthcheck():
    return {"status": "OK", "version": "1.0.0"}


app.include_router(users.router)
app.include_router(movies.router)
app.include_router(comments.router)
app.include_router(posts.router)
app.include_router(reviews.router)
app.include_router(feed.router)

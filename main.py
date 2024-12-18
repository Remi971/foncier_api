from fastapi import FastAPI, Path, Query, Depends
from dependencies import oauth2_scheme
from routers import data
from routers import process
from routers import users
from routers import auth

app = FastAPI(
    title="Demo of testing FastApi",
    description="Exploration of fastapi framework and test of good practice",
    version="0.0.1",
    )

app.include_router(auth.router)
app.include_router(data.router)
app.include_router(process.router)
app.include_router(users.router)


@app.get('/')
def read_root(token: str = Depends(oauth2_scheme)):
    '''Basic Get request'''
    return f"Hello world ... : {token}"

@app.get(
    "/onlyparams",
    responses={
        404: {"description": "Not Found"},
        400: {"description": "No arguments specified"}
    })
def read_params(
    param1: int = Query(default=None, gt=0), 
    param2: str| None = Query(default=None, min_length=1),
    ):
    return {"param1": param1, "param2": param2}

@app.get("/items/{item_id}")
def read_items(
    item_id: int | None = Path(gt=0),
    ):
    return {"item_id": item_id}

@app.get("/items")
def test():
    return "Test"
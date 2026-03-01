from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from .database import Base, engine
from .routers import config_router, execute_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dynamic API Wrapper")

templates = Jinja2Templates(directory="app/templates")

app.include_router(config_router.router)
app.include_router(execute_router.router)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.views.api import router as api_router
from app.views.search import router as search_router
from app.views.unloading import router as unloading_router

from app.api.v1.endpoints import router as api_v1_router
from app.events import create_start_app_handler, create_stop_app_handler
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def get_application() -> FastAPI:

    application = FastAPI()

    application.mount(
        "/css", StaticFiles(directory="app/static/css"), name="css")
    application.mount(
        "/js", StaticFiles(directory="app/static/js"), name="js")
    application.mount(
        "/fonts", StaticFiles(directory="app/static/fonts"), name="fonts")
    application.mount(
        "/images", StaticFiles(directory="app/static/images"), name="images")
    application.mount(
        "/static", StaticFiles(directory="app/static"), name="static")

    application.add_event_handler(
        "startup",
        create_start_app_handler(application, settings),
    )
    application.add_event_handler(
        "shutdown",
        create_stop_app_handler(application),
    )

    application.include_router(api_router)
    application.include_router(search_router)
    application.include_router(unloading_router)
    application.include_router(api_v1_router)

    return application


app = get_application()

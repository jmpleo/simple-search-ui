import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from app.api.api import router as api_router
from app.views.root import router as view_router

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
    application.include_router(view_router)

    return application


app = get_application()

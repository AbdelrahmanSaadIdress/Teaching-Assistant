from fastapi import FastAPI, APIRouter, Depends, Body
from helpers import get_settings, Settings

startRoute = APIRouter(
    prefix="/api/TA",
    tags=["start_router"]
)

@startRoute.get("/welcome")
async def welcome_function(
    app_settings: Settings = Depends(get_settings),
    ):
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION

    return {
        "app_name":app_name,
        "app_version":app_version
    }


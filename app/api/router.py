from fastapi import APIRouter
from app.api.routes import scan, settings, tasks, downloads, subscriptions, utils, library

api_router = APIRouter()

api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(downloads.router, prefix="/downloads", tags=["downloads"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(library.router, prefix="/library", tags=["library"])

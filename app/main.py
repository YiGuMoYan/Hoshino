from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import webbrowser
import os
from contextlib import asynccontextmanager # Added for lifespan
from contextlib import asynccontextmanager
from app.api.routes import scan, settings, downloads, tasks, subscriptions, logs, library, utils
from app.core.logger import setup_logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logger()
    # Initialize DB on startup
    from app.db.session import init_db
    from app.services.system.settings_service import SettingsService
    init_db()
    SettingsService.initialize_defaults()
    yield
    # Shutdown
    pass

app = FastAPI(title="Hoshino API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(scan.router, prefix="/api/scan", tags=["scan"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(downloads.router, prefix="/api/downloads", tags=["download"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(subscriptions.router, prefix="/api/subscription", tags=["subscription"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(library.router, prefix="/api/library", tags=["library"])
app.include_router(utils.router, prefix="/api/utils", tags=["utils"])

# 挂载静态文件 (仅在生产环境下且存在 dist 目录时)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

if os.path.exists("web/dist"):
    app.mount("/", StaticFiles(directory="web/dist", html=True), name="static")
    
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        if not request.url.path.startswith("/api"):
            return FileResponse("web/dist/index.html")
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

@app.get("/health")
async def health():
    return {"status": "ok"}

def start():
    """Launched with `poetry run start` at root level"""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()

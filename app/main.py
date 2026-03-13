from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import auth, workers, dashboard, alerts, reports, portal, documents, leave, calendar, bgverify, platform, saas

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://protexi.vercel.app",
        "https://protexi.com",
        "https://www.protexi.com",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin / Staff routes
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(workers.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(leave.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(bgverify.router, prefix="/api")
app.include_router(platform.router, prefix="/api")
app.include_router(saas.router, prefix="/api")

# Employee portal routes
app.include_router(portal.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}

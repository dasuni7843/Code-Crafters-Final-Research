"""FastAPI application entry point — Sri Lanka Tourism AI System."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import APP_TITLE, APP_VERSION, CORS_ORIGINS, RESULTS_DIR
from app.routers import integrated, module1, module2, module4, results
from app.services import module1_service, module2_service, module4_service

logger = logging.getLogger("tourism_ai")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve training result charts as static files
if RESULTS_DIR.exists():
    app.mount("/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")

app.include_router(module1.router, prefix="/api/module1", tags=["Module 1"])
app.include_router(module2.router, prefix="/api/module2", tags=["Module 2"])
app.include_router(module4.router, prefix="/api/module4", tags=["Module 4"])
app.include_router(integrated.router, prefix="/api/integrated", tags=["Integrated"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])


@app.on_event("startup")
def warm_models() -> None:
    """Load models into cache at startup so the first request is fast."""
    module1_service.models_loaded()
    module2_service.models_loaded()
    module4_service.models_loaded()
    logger.info("Models warmed up.")


@app.get("/api/health")
def health() -> dict:
    loaded = (
        module1_service.models_loaded()
        and module2_service.models_loaded()
        and module4_service.models_loaded()
    )
    return {"status": "ok", "models_loaded": loaded}


# ── Global, user-friendly error handling ──
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": str(exc.detail), "detail": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", []) if p != "body") or "input"
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": f"Please check your input: {field} is invalid or required.",
            "detail": str(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error at %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "The prediction model encountered an issue. Please try again.",
            "detail": str(exc),
        },
    )

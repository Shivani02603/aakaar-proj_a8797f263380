import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from database.config import init_db

# Import routers
from backend.routers.auth import router as auth_router
from backend.routers.core_ai_query import router as core_ai_query_router
from backend.routers.data_persistence import router as data_persistence_router
from backend.routers.data_storage import router as data_storage_router
from backend.routers.document_management import router as document_management_router
from backend.routers.document_processing import router as document_processing_router
from backend.routers.sessions import router as sessions_router
from backend.routers.users import router as users_router

# Initialize FastAPI app
app = FastAPI(
    title="Aakaar Project",
    description="Backend API for Aakaar Project",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse({"detail": str(exc)}, status_code=429)


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Mount routers
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/api/users", tags=["Users"])
api_router.include_router(sessions_router, prefix="/api/sessions", tags=["Sessions"])
api_router.include_router(document_management_router, prefix="/api/document_management", tags=["Document_management"])
api_router.include_router(document_processing_router, prefix="/api/document_processing", tags=["Document_processing"])
api_router.include_router(data_storage_router, prefix="/api/data_storage", tags=["Data_storage"])
api_router.include_router(core_ai_query_router, prefix="/api/core_ai_query", tags=["Core_ai_query"])
api_router.include_router(data_persistence_router, prefix="/api/data_persistence", tags=["Data_persistence"])
app.include_router(auth_router, prefix='/api/auth', tags=['Auth'])
app.include_router(core_ai_query_router, prefix='/api/ai', tags=['Core Ai Query'])
app.include_router(data_persistence_router, prefix='/api/chat', tags=['Data Persistence'])
app.include_router(data_storage_router, prefix='/api/chat/sessions', tags=['Data Storage'])
app.include_router(document_management_router, prefix='/api/documents', tags=['Document Management'])
app.include_router(document_processing_router, prefix='/api', tags=['Document Processing'])
app.include_router(sessions_router, prefix='/api/chat/sessions', tags=['Sessions'])
app.include_router(users_router, prefix='/api/documents', tags=['Users'])

# Lifespan context manager
@app.on_event("startup")
async def startup_event():
    init_db()


@app.on_event("shutdown")
async def shutdown_event():
    pass

# AI_ROUTER_INJECTION_POINT — do not remove this line
# AI layer — mounted by Agent 8B
from ai.routes import router as ai_router
app.include_router(ai_router, prefix='/api/ai', tags=['AI'])

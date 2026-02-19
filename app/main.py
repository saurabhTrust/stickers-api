# """
# FastAPI Application for GPU Sticker Generation Service
# (Production hardened)
# """
# import sys
# import uuid
# import asyncio
# from typing import List, Optional

# from fastapi import FastAPI, HTTPException, status, Request, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel, Field
# from loguru import logger

# from app.config import settings, ensure_directories, AVAILABLE_EXPRESSIONS
# from app.model_manager import model_manager
# from app.sticker_service import sticker_service
# from app.security import verify_api_key, rate_limit


# # Configure logging
# logger.remove()
# logger.add(
#     sys.stdout,
#     format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
#            "<cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
#     level=settings.LOG_LEVEL,
# )
# logger.add(
#     settings.LOG_FILE,
#     rotation="100 MB",
#     retention="7 days",
#     level=settings.LOG_LEVEL,
# )

# # Backpressure semaphore: limits how many requests can wait while GPU is busy
# _pending_sem = asyncio.Semaphore(int(settings.MAX_PENDING_REQUESTS))


# # Pydantic Models
# class StickerRequest(BaseModel):
#     image: str = Field(..., description="Base64 encoded image")
#     seed: Optional[int] = Field(None, description="Random seed for reproducibility")
#     expressions: Optional[List[str]] = Field(None, description="Specific expressions to generate")


# class StickerItem(BaseModel):
#     mood: str
#     image: str


# class StickerResponse(BaseModel):
#     success: bool
#     processing_time: float
#     stickers: List[StickerItem]
#     metadata: Optional[dict] = None
#     timings: Optional[dict] = None


# class ErrorResponse(BaseModel):
#     success: bool = False
#     error: str
#     detail: Optional[str] = None


# class HealthResponse(BaseModel):
#     status: str
#     model_loaded: bool
#     gpu_available: bool
#     gpu_info: Optional[dict] = None
#     available_expressions: List[str]




# app = FastAPI(
#     title="GPU Sticker Generation Service",
#     description="Generate expression-based 3D cartoon stickers using SDXL + LoRA",
#     version="1.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc",
# )

# # CORS middleware (safe origins)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.parsed_cors_origins(),
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Middleware: request-id + payload size guard
# @app.middleware("http")
# async def request_hardening_middleware(request: Request, call_next):
#     request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
#     request.state.request_id = request_id

#     # request size check
#     cl = request.headers.get("content-length")
#     if cl is not None:
#         try:
#             if int(cl) > int(settings.MAX_REQUEST_BYTES):
#                 return JSONResponse(
#                     status_code=413,
#                     content={"success": False, "error": "Payload too large"},
#                     headers={"X-Request-Id": request_id},
#                 )
#         except ValueError:
#             pass

#     logger.info(f"[{request_id}] {request.method} {request.url.path} start")

#     try:
#         response = await call_next(request)
#     except Exception as e:
#         logger.error(f"[{request_id}] Middleware exception: {e}")
#         return JSONResponse(
#             status_code=500,
#             content={"success": False, "error": "Internal server error"},
#             headers={"X-Request-Id": request_id},
#         )

#     response.headers["X-Request-Id"] = request_id
#     logger.info(f"[{request_id}] {request.method} {request.url.path} done {response.status_code}")
#     return response


# @app.on_event("startup")
# async def startup_event():
#     logger.info("=" * 70)
#     logger.info("GPU STICKER GENERATION SERVICE - STARTING")
#     logger.info("=" * 70)

#     try:
#         ensure_directories()
#         logger.info("✅ Directories initialized")

#         logger.info("Loading models...")
#         await asyncio.to_thread(model_manager.load_models)
#         logger.info("✅ Models loaded successfully")

#         logger.info("=" * 70)
#         logger.info(f"🚀 Service ready on http://{settings.API_HOST}:{settings.API_PORT}")
#         logger.info(f"📚 API docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
#         logger.info(f"🎨 Available expressions: {', '.join(AVAILABLE_EXPRESSIONS)}")
#         logger.info("=" * 70)

#     except Exception as e:
#         logger.error(f"❌ Startup failed: {e}")
#         raise


# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("Shutting down service...")
#     model_manager.cleanup()
#     logger.info("✅ Cleanup complete")


# @app.get("/")
# async def root():
#     return {
#         "service": "GPU Sticker Generation Service",
#         "version": "1.0.0",
#         "status": "running",
#         "endpoints": {
#             "generate_stickers": "POST /api/generate-stickers",
#             "health": "GET /api/health",
#             "info": "GET /api/info",
#         },
#     }


# @app.post(
#     "/api/generate-stickers",
#     response_model=StickerResponse,
#     responses={200: {"model": StickerResponse}, 400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
# )
# async def generate_stickers(
#     request: StickerRequest,
#     _: None = Depends(verify_api_key),
#     __: None = Depends(rate_limit),
# ):
#     try:
#         if not request.image:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No image provided")

#         # Allow case-insensitive expressions at API layer
#         if request.expressions:
#             allowed = [e.lower() for e in AVAILABLE_EXPRESSIONS]
#             invalid = [e for e in request.expressions if str(e).strip().lower() not in allowed]
#             if invalid:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail=f"Invalid expressions: {invalid}. Available: {AVAILABLE_EXPRESSIONS}",
#                 )

#         # Backpressure: reject if too many are waiting
#         try:
#             await asyncio.wait_for(_pending_sem.acquire(), timeout=0.1)
#         except asyncio.TimeoutError:
#             raise HTTPException(status_code=503, detail="Server busy. Please retry shortly.")

#         try:
#             result = await asyncio.wait_for(
#                 sticker_service.generate_stickers_from_base64(
#                     base64_image=request.image,
#                     seed=request.seed,
#                     expressions=request.expressions,
#                 ),
#                 timeout=int(settings.REQUEST_TIMEOUT_SECONDS),
#             )
#         finally:
#             _pending_sem.release()

#         return result

#     except HTTPException:
#         raise
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     except asyncio.TimeoutError:
#         raise HTTPException(status_code=504, detail="Request timed out while generating stickers")
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate stickers: {e}")


# @app.get("/api/health", response_model=HealthResponse)
# async def health_check():
#     try:
#         health_status = model_manager.get_health_status()
#         return {
#             "status": "healthy" if health_status["model_loaded"] else "unhealthy",
#             "model_loaded": health_status["model_loaded"],
#             "gpu_available": health_status["gpu_available"],
#             "gpu_info": health_status.get("gpu_info"),
#             "available_expressions": AVAILABLE_EXPRESSIONS,
#         }
#     except Exception as e:
#         return {
#             "status": "unhealthy",
#             "model_loaded": False,
#             "gpu_available": False,
#             "gpu_info": {"error": str(e)},
#             "available_expressions": AVAILABLE_EXPRESSIONS,
#         }


# @app.get("/api/info")
# async def get_info():
#     return {
#         "service": "GPU Sticker Generation Service",
#         "version": "1.0.0",
#         "model": {
#             "base_model": settings.SDXL_MODEL_ID,
#             "lora_model": settings.LORA_MODEL_ID,
#             "lora_scale": settings.LORA_SCALE,
#         },
#         "generation_settings": {
#             "image_size": settings.IMAGE_SIZE,
#             "guidance_scale": settings.GUIDANCE_SCALE,
#             "num_inference_steps": settings.NUM_INFERENCE_STEPS,
#             "strength": settings.STRENGTH,
#         },
#         "available_expressions": AVAILABLE_EXPRESSIONS,
#         "num_expressions": len(AVAILABLE_EXPRESSIONS),
#     }


# @app.exception_handler(Exception)
# async def global_exception_handler(request: Request, exc: Exception):
#     request_id = getattr(request.state, "request_id", None)
#     logger.error(f"[{request_id}] Unhandled exception: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={
#             "success": False,
#             "error": "Internal server error",
#             "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None,
#         },
#         headers={"X-Request-Id": request_id} if request_id else None,
#     )


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(
#         "app.main:app",
#         host=settings.API_HOST,
#         port=settings.API_PORT,
#         reload=False,
#         log_level=settings.LOG_LEVEL.lower(),
#     )


"""
FastAPI Application for GPU Sticker Generation Service
Fixed: Deprecated on_event replaced with lifespan
Fixed: Pydantic model_ namespace warning
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from loguru import logger
import sys

from app.config import settings, ensure_directories, AVAILABLE_EXPRESSIONS
from app.model_manager import model_manager
from app.sticker_service import sticker_service


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    settings.LOG_FILE,
    rotation="100 MB",
    retention="7 days",
    level=settings.LOG_LEVEL
)


# ========================
# Pydantic Models
# ========================

class StickerRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded image")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    expressions: Optional[List[str]] = Field(None, description="Specific expressions to generate")

    class Config:
        json_schema_extra = {
            "example": {
                "image": "base64_encoded_string_here...",
                "seed": 42,
                "expressions": ["happy", "sad", "excited"]
            }
        }


class StickerItem(BaseModel):
    mood: str
    image: str


class StickerResponse(BaseModel):
    success: bool
    processing_time: float
    stickers: List[StickerItem]
    metadata: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    is_loaded: bool
    gpu_available: bool
    gpu_info: Optional[dict] = None
    available_expressions: List[str]

    model_config = {"protected_namespaces": ()}  # Fix Pydantic warning


# ========================
# Lifespan (replaces deprecated on_event)
# ========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("=" * 70)
    logger.info("GPU STICKER GENERATION SERVICE - STARTING")
    logger.info("=" * 70)

    try:
        ensure_directories()
        logger.info("✅ Directories initialized")

        logger.info("Loading models...")
        model_manager.load_models()
        logger.info("✅ Models loaded successfully")

        logger.info("=" * 70)
        logger.info(f"🚀 Service ready on http://{settings.API_HOST}:{settings.API_PORT}")
        logger.info(f"📚 API docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
        logger.info(f"🎨 Available expressions: {', '.join(AVAILABLE_EXPRESSIONS)}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield  # App runs here

    # SHUTDOWN
    logger.info("Shutting down service...")
    model_manager.cleanup()
    logger.info("✅ Cleanup complete")


# ========================
# FastAPI App
# ========================

app = FastAPI(
    title="GPU Sticker Generation Service",
    description="Generate expression-based 3D cartoon stickers using SDXL + LoRA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================
# Endpoints
# ========================

@app.get("/")
async def root():
    return {
        "service": "GPU Sticker Generation Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "generate_stickers": "POST /api/generate-stickers",
            "health": "GET /api/health",
            "info": "GET /api/info"
        }
    }


@app.post("/api/generate-stickers", response_model=StickerResponse)
async def generate_stickers(request: StickerRequest):
    try:
        logger.info("📥 Received sticker generation request")

        if not request.image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image provided"
            )

        if request.expressions:
            invalid = [e for e in request.expressions if e not in AVAILABLE_EXPRESSIONS]
            if invalid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid expressions: {invalid}. Available: {AVAILABLE_EXPRESSIONS}"
                )

        result = await sticker_service.generate_stickers_from_base64(
            base64_image=request.image,
            seed=request.seed,
            expressions=request.expressions
        )

        logger.info(f"✅ Request completed in {result['processing_time']}s")
        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    try:
        health = model_manager.get_health_status()
        return {
            "status": "healthy" if health["model_loaded"] else "unhealthy",
            "is_loaded": health["model_loaded"],
            "gpu_available": health["gpu_available"],
            "gpu_info": health.get("gpu_info"),
            "available_expressions": AVAILABLE_EXPRESSIONS
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "is_loaded": False,
            "gpu_available": False,
            "available_expressions": AVAILABLE_EXPRESSIONS
        }


@app.get("/api/info")
async def get_info():
    return {
        "service": "GPU Sticker Generation Service",
        "version": "1.0.0",
        "model": {
            "base_model": settings.SDXL_MODEL_ID,
            "lora_model": settings.LORA_MODEL_ID,
            "lora_scale": settings.LORA_SCALE
        },
        "generation_settings": {
            "image_size": settings.IMAGE_SIZE,
            "guidance_scale": settings.GUIDANCE_SCALE,
            "num_inference_steps": settings.NUM_INFERENCE_STEPS,
            "strength": settings.STRENGTH
        },
        "available_expressions": AVAILABLE_EXPRESSIONS,
        "num_expressions": len(AVAILABLE_EXPRESSIONS)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )
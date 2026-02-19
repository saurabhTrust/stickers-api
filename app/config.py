"""
Configuration for GPU Sticker Service
Production-hardened version
"""

from ast import Expression
from pydantic_settings import BaseSettings
from typing import Dict, List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # ========================
    # Server Configuration
    # ========================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 5000

    # Optional security
    API_KEY: str | None = None

    # CORS (comma-separated)
    CORS_ORIGINS: str = "http://localhost:3000"

    # Request limits
    MAX_REQUEST_BYTES: int = 12_000_000           # ~12MB request body
    REQUEST_TIMEOUT_SECONDS: int = 180            # seconds

    # Rate limiting (per IP)
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Backpressure (how many requests can wait while GPU is busy)
    MAX_PENDING_REQUESTS: int = 2

    # ========================
    # Model Configuration
    # ========================
    SDXL_MODEL_ID: str = "stabilityai/stable-diffusion-xl-base-1.0"
    LORA_MODEL_ID: str = "artificialguybr/3DRedmond-V1"
    LORA_FILENAME: str = "3DRedmond-3DRenderStyle-3DRenderAF.safetensors"
    LORA_SCALE: float = 0.65

    MODEL_CACHE_DIR: str = "./model_cache"
    LORA_DIR: str = "./models/lora"

    # ========================
    # Generation Settings
    # ========================
    IMAGE_SIZE: int = 1024
    GUIDANCE_SCALE: float = 8.5
    NUM_INFERENCE_STEPS: int = 35
    STRENGTH: float = 0.32
    SEED_BASE: int = 42

    # ========================
    # Performance Settings
    # ========================
    MAX_CONCURRENT_REQUESTS: int = 1
    ENABLE_XFORMERS: bool = True
    GPU_MEMORY_FRACTION: float = 0.9  # Must be applied in model_manager

    # ========================
    # Storage
    # ========================
    OUTPUT_DIR: str = "./output"
    SAVE_TO_DISK: bool = True
    LOG_DIR: str = "./logs"
    LOG_FILE: str = "./logs/sticker_service.log"

    # ========================
    # Expressions
    # ========================
    NUM_EXPRESSIONS: int = 5
    
    # ========================
    # Logging
    # ========================
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def parsed_cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

# ========================
# Expression Prompts
# ========================

# EXPRESSION_PROMPTS: Dict[str, Dict[str, str]] = {
#     "happy": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "happy laughing face, big smile, closed happy eyes, joyful expression, "
#             "HaHa text bubble, sparkle effects, star decorations, "
#             "bold black outlines, simple clean shapes, solid bright colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "sad angry crying, blurry messy, low quality, inconsistent, "
#             "western cartoon, CGI, photograph"
#         ),
#     },
    
#     "sad": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "sad confused face, thinking expression, question mark symbol, "
#             "downcast eyes, slight frown, puzzled look, "
#             "bold black outlines, simple clean shapes, solid muted colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "happy smiling laughing, blurry messy, low quality, inconsistent, "
#             "western cartoon, CGI, photograph"
#         ),
#     },
    
#     "excited": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "excited happy face, wide open mouth, sparkling eyes, "
#             "waving hand gesture, star decorations, yellow sparkles, "
#             "bold black outlines, simple clean shapes, solid bright colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "sad tired bored, blurry messy, low quality, inconsistent, "
#             "western cartoon, CGI, photograph"
#         ),
#     },
    
#     "angry": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "angry furious face, GRRR text, fire effects, flames, "
#             "clenched fists, intense eyes, furrowed brows, red angry marks, "
#             "bold black outlines, simple clean shapes, solid red orange colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "happy calm smiling, blurry messy, low quality, inconsistent, "
#             "western cartoon, CGI, photograph"
#         ),
#     },
    
#     "crying": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "crying sobbing face, HuHu text, big tears streaming, "
#             "open crying mouth, watery eyes, blue tear drops, sad expression, "
#             "bold black outlines, simple clean shapes, solid blue colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "happy laughing smiling, blurry messy, low quality, inconsistent, "
#             "western cartoon, CGI, photograph"
#         ),
#     },
    
#     # BONUS: Additional expressions matching your sticker sheet
    
#     "thinking": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "thinking confused face, question mark above head, "
#             "finger on chin, puzzled expression, hmm gesture, "
#             "bold black outlines, simple clean shapes, solid colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "certain confident, blurry messy, low quality, inconsistent"
#         ),
#     },
    
#     "thumbs_up": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "happy approving face, thumbs up gesture, OK text, "
#             "big smile, winking, positive vibes, star sparkles, "
#             "bold black outlines, simple clean shapes, solid bright colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "thumbs down negative, blurry messy, low quality, inconsistent"
#         ),
#     },
    
#     "love": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "blushing happy face, closed eyes smile, heart symbols, "
#             "hands together praying, pink hearts floating, love expression, "
#             "bold black outlines, simple clean shapes, solid pink red colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "angry hateful, blurry messy, low quality, inconsistent"
#         ),
#     },
    
#     "surprised": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "shocked surprised face, wide open eyes, open mouth, "
#             "!!! exclamation marks, sweat drops, dizzy symbols, "
#             "bold black outlines, simple clean shapes, solid colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "calm bored, blurry messy, low quality, inconsistent"
#         ),
#     },
    
#     "peace": {
#         "positive": (
#             "chibi style, emoji sticker, flat 2d cartoon illustration, "
#             "happy smiling face, peace sign gesture, V sign with fingers, "
#             "winking eye, cheerful expression, sparkle effects, "
#             "bold black outlines, simple clean shapes, solid bright colors, "
#             "kawaii cute aesthetic, sticker design, vector style, "
#             "clean illustration, consistent character, high quality, "
#             "white background, png sticker"
#         ),
#         "negative": (
#             "3d render, realistic photo, complex shading, gradient, soft edges, "
#             "watercolor, painting, anime film, ghibli, detailed background, "
#             "sad angry, blurry messy, low quality, inconsistent"
#         ),
#     },
# }

EXPRESSION_PROMPTS: Dict[str, Dict[str, str]] = {
    "happy": {
        "positive": (
            "ghibli style, studio ghibli, smiling happy face, joyful cheerful expression, "
            "bright eyes, warm genuine smile, positive emotion, delighted, "
            "anime style, hand-painted aesthetic, soft colors, dreamy atmosphere, "
            "detailed facial features, high quality, consistent style"
        ),
        "negative": (
            "sad, angry, crying, upset, neutral, serious, frowning, "
            "realistic photo, 3d render, CGI, western cartoon, "
            "blurry, low quality, distorted, deformed, ugly, bad anatomy"
        ),
    },
    "sad": {
        "positive": (
            "ghibli style, studio ghibli, sad melancholic face, downcast eyes, slight frown, "
            "unhappy expression, gloomy disappointed mood, dejected, "
            "anime style, hand-painted aesthetic, muted colors, emotional atmosphere, "
            "detailed facial features, high quality, consistent style"
        ),
        "negative": (
            "happy, smiling, laughing, excited, joyful, cheerful, "
            "realistic photo, 3d render, CGI, western cartoon, "
            "blurry, low quality, distorted, deformed, ugly, bad anatomy"
        ),
    },
    "excited": {
        "positive": (
            "ghibli style, studio ghibli, excited energetic face, wide bright eyes, "
            "big enthusiastic smile, surprised-happy expression, energetic animated, "
            "anime style, hand-painted aesthetic, vibrant colors, dynamic atmosphere, "
            "detailed facial features, high quality, consistent style"
        ),
        "negative": (
            "sad, tired, bored, sleepy, neutral, calm, depressed, "
            "realistic photo, 3d render, CGI, western cartoon, "
            "blurry, low quality, distorted, deformed, ugly, bad anatomy"
        ),
    },
    "angry": {
        "positive": (
            "ghibli style, studio ghibli, angry fierce face, furrowed brows, intense eyes, "
            "mad frustrated expression, aggressive emotion, stern annoyed, "
            "anime style, hand-painted aesthetic, intense colors, dramatic atmosphere, "
            "detailed facial features, high quality, consistent style"
        ),
        "negative": (
            "happy, calm, peaceful, smiling, relaxed, content, "
            "realistic photo, 3d render, CGI, western cartoon, "
            "blurry, low quality, distorted, deformed, ugly, bad anatomy"
        ),
    },
    "crying": {
        "positive": (
            "ghibli style, studio ghibli, crying emotional face, tears streaming, "
            "sad teary eyes, upset sobbing expression, watery eyes, emotional distress, "
            "anime style, hand-painted aesthetic, gentle blue tones, touching atmosphere, "
            "detailed facial features, high quality, consistent style"
        ),
        "negative": (
            "happy, laughing, smiling, joyful, cheerful, excited, "
            "realistic photo, 3d render, CGI, western cartoon, "
            "blurry, low quality, distorted, deformed, ugly, bad anatomy"
        ),
    },
}

AVAILABLE_EXPRESSIONS: List[str] = list(EXPRESSION_PROMPTS.keys())


def get_lora_path() -> str:
    """Get full path to LoRA file"""
    return str(Path(settings.LORA_DIR) / settings.LORA_FILENAME)


def ensure_directories():
    """Create required directories if they don't exist"""
    directories = [
        settings.OUTPUT_DIR,
        settings.MODEL_CACHE_DIR,
        settings.LORA_DIR,
        settings.LOG_DIR,
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
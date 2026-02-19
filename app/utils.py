"""
Utility functions for image processing and validation
Production-ready version
"""

import base64
import io
import os
import gc
from PIL import Image
import torch
from typing import Optional
from loguru import logger


# ==============================
# Configuration
# ==============================

MAX_IMAGE_SIZE_MB = 10  # Max allowed input image size


# ==============================
# Base64 <-> PIL Conversion
# ==============================

def base64_to_pil(base64_str: str) -> Image.Image:
    """
    Convert base64 string to PIL Image safely
    """

    try:
        # Remove data URL prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]

        # Prevent extremely large payload attacks
        max_base64_length = MAX_IMAGE_SIZE_MB * 1024 * 1024 * 1.37
        if len(base64_str) > max_base64_length:
            raise ValueError("Image exceeds maximum allowed size")

        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        image = image.convert("RGB")

        return image

    except Exception as e:
        logger.error(f"Failed to decode base64 image: {e}")
        raise ValueError(f"Invalid base64 image data: {e}")


def pil_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    Convert PIL Image to base64 string
    """

    try:
        buffer = io.BytesIO()
        image.save(buffer, format=format, optimize=True)
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    except Exception as e:
        logger.error(f"Failed to encode image to base64: {e}")
        raise ValueError(f"Failed to convert image to base64: {e}")


# ==============================
# Image Processing
# ==============================

def resize_image(image: Image.Image, target_size: int) -> Image.Image:
    """
    Resize image maintaining aspect ratio and pad to square
    """

    # Maintain aspect ratio
    image.thumbnail((target_size, target_size), Image.LANCZOS)

    # Create square canvas
    new_image = Image.new("RGB", (target_size, target_size), (255, 255, 255))
    new_image.paste(
        image,
        (
            (target_size - image.width) // 2,
            (target_size - image.height) // 2,
        ),
    )

    return new_image


def validate_base64_image(base64_str: str) -> bool:
    """
    Validate if string is a valid base64 image
    """
    try:
        base64_to_pil(base64_str)
        return True
    except Exception:
        return False


# ==============================
# GPU Utilities
# ==============================

def get_gpu_memory_info() -> dict:
    """
    Get detailed GPU memory information
    """

    if not torch.cuda.is_available():
        return {
            "available": False,
            "error": "CUDA not available"
        }

    try:
        device = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(device)

        total = props.total_memory / 1024**3  # GB
        reserved = torch.cuda.memory_reserved(device) / 1024**3
        allocated = torch.cuda.memory_allocated(device) / 1024**3
        free = total - reserved

        return {
            "available": True,
            "device": props.name,
            "total_gb": round(total, 2),
            "reserved_gb": round(reserved, 2),
            "allocated_gb": round(allocated, 2),
            "free_gb": round(free, 2),
            "utilization_percent": round((reserved / total) * 100, 2),
        }

    except Exception as e:
        logger.error(f"Failed to get GPU memory info: {e}")
        return {
            "available": True,
            "error": str(e),
        }


def clear_gpu_memory():
    """
    Clear GPU memory cache safely
    """

    if torch.cuda.is_available():
        try:
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            logger.info("GPU memory cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear GPU memory: {e}")


# ==============================
# File Handling
# ==============================

def save_image_to_disk(image: Image.Image, filepath: str):
    """
    Save PIL Image to disk safely
    """

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        image.save(filepath)
        logger.info(f"Image saved to: {filepath}")
    except Exception as e:
        logger.error(f"Failed to save image to {filepath}: {e}")
        raise


# ==============================
# Validation
# ==============================

def validate_expression(expression: str, available_expressions: list) -> bool:
    """
    Validate if expression is in available list (case-insensitive)
    """
    return expression.lower() in [exp.lower() for exp in available_expressions]
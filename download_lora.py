#!/usr/bin/env python3
"""
Download LoRA model from Hugging Face (production-ready)
"""

import os
from pathlib import Path
from huggingface_hub import hf_hub_download
from loguru import logger

from app.config import settings, get_lora_path


def download_lora() -> str:
    """
    Download LoRA model from Hugging Face if not already present.

    Returns:
        str: local path to LoRA file
    """
    try:
        lora_dir = Path(settings.LORA_DIR)
        lora_path = Path(get_lora_path())

        # Ensure directory exists
        lora_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 60)
        logger.info("LoRA Download Check")
        logger.info("=" * 60)
        logger.info(f"Model: {settings.LORA_MODEL_ID}")
        logger.info(f"File: {settings.LORA_FILENAME}")
        logger.info(f"Destination: {lora_dir}")

        # ✅ Skip if already exists and looks valid
        if lora_path.exists() and lora_path.stat().st_size > 10_000_000:
            logger.info("✅ LoRA already present — skipping download")
            logger.info(f"📁 Location: {lora_path}")
            return str(lora_path)

        logger.info("")
        logger.info("Downloading LoRA (~143 MB)...")

        # Download from Hugging Face
        downloaded_path = hf_hub_download(
            repo_id=settings.LORA_MODEL_ID,
            filename=settings.LORA_FILENAME,
            local_dir=str(lora_dir),
            token=getattr(settings, "HUGGINGFACE_TOKEN", None),
        )

        # ✅ Post-download validation
        if not Path(downloaded_path).exists():
            raise RuntimeError("Downloaded file not found")

        logger.info("=" * 60)
        logger.info("✅ LoRA model downloaded successfully!")
        logger.info(f"📁 Location: {downloaded_path}")
        logger.info("=" * 60)

        return downloaded_path

    except Exception as e:
        logger.error(f"❌ Failed to download LoRA: {e}")
        logger.error("Troubleshooting:")
        logger.error("1. Check internet connection")
        logger.error("2. Verify Hugging Face access")
        logger.error(f"3. Try manual download: https://huggingface.co/{settings.LORA_MODEL_ID}")
        raise


if __name__ == "__main__":
    download_lora()
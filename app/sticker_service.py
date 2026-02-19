"""
Sticker Generation Service: Core logic for generating expression stickers
(Optimized production version)

Key improvements:
- Validates requested expressions early (fast failure, better errors)
- Runs background removal in a thread executor to avoid blocking FastAPI event loop
- Adds per-step timing for easier profiling/monitoring
- Keeps GPU generation sequential (safe) while CPU background removal is async-friendly
"""
import time
import os
import uuid
import asyncio
from typing import List, Tuple, Optional, Dict

from PIL import Image
from rembg import remove, new_session
from loguru import logger

from app.model_manager import model_manager
from app.config import settings, EXPRESSION_PROMPTS, AVAILABLE_EXPRESSIONS
from app.utils import (
    base64_to_pil,
    pil_to_base64,
    resize_image,
    save_image_to_disk,
    clear_gpu_memory,
)


class StickerGenerationService:
    """
    Service for generating expression-based stickers
    """

    def __init__(self):
        # Initialize background removal session once (good for perf)
        logger.info("Initializing background removal session...")
        self.bg_session = new_session("u2net")
        logger.info("✅ Background removal ready")

    # ---------------------------
    # Validation helpers
    # ---------------------------

    def _validate_expressions(self, expressions: Optional[List[str]]) -> List[str]:
        """
        Validate and normalize requested expressions.
        Returns final list of expressions to generate.
        """
        target = expressions or AVAILABLE_EXPRESSIONS

        if not isinstance(target, list) or not target:
            raise ValueError("expressions must be a non-empty list")

        # Normalize to lower-case (API friendliness)
        normalized = [str(e).strip().lower() for e in target if str(e).strip()]
        if not normalized:
            raise ValueError("expressions must contain at least one valid expression")

        # Validate against available expressions
        available = set([e.lower() for e in AVAILABLE_EXPRESSIONS])
        invalid = [e for e in normalized if e not in available]
        if invalid:
            raise ValueError(f"Invalid expressions requested: {invalid}. Allowed: {AVAILABLE_EXPRESSIONS}")

        # Keep original order but remove duplicates
        seen = set()
        unique = []
        for e in normalized:
            if e not in seen:
                unique.append(e)
                seen.add(e)

        return unique

    # ---------------------------
    # Preprocess
    # ---------------------------

    async def preprocess_image(self, base64_image: str) -> Image.Image:
        """
        Decode + resize the input image for SDXL.
        """
        try:
            image = base64_to_pil(base64_image)
            image = resize_image(image, settings.IMAGE_SIZE)
            logger.info(f"Image preprocessed: {image.size}")
            return image
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise ValueError(f"Failed to preprocess image: {e}")

    # ---------------------------
    # SDXL generation
    # ---------------------------

    async def generate_single_expression(
        self,
        image: Image.Image,
        expression: str,
        seed: int,
    ) -> Tuple[str, Image.Image]:
        """
        Generate a single expression sticker with SDXL + LoRA.
        """
        prompts = EXPRESSION_PROMPTS.get(expression)
        if not prompts:
            raise ValueError(f"Unknown expression: {expression}")

        positive_prompt = prompts["positive"]
        negative_prompt = prompts["negative"]

        logger.info(f"Generating '{expression}'...")

        generated_image = await model_manager.generate_sticker(
            image=image,
            prompt=positive_prompt,
            negative_prompt=negative_prompt,
            seed=seed,
        )

        logger.info(f"✅ '{expression}' generated")
        return expression, generated_image

    async def generate_all_expressions(
        self,
        image: Image.Image,
        seed: int,
        expressions: Optional[List[str]] = None,
    ) -> List[Tuple[str, Image.Image]]:
        """
        Generate requested expression stickers sequentially (safe for GPU).
        """
        target_expressions = self._validate_expressions(expressions)

        logger.info(f"Generating {len(target_expressions)} expressions: {target_expressions}")

        stickers: List[Tuple[str, Image.Image]] = []
        for idx, expression in enumerate(target_expressions):
            expression_seed = int(seed) + idx
            stickers.append(
                await self.generate_single_expression(
                    image=image,
                    expression=expression,
                    seed=expression_seed,
                )
            )

        logger.info(f"✅ All {len(stickers)} expressions generated")
        return stickers

    # ---------------------------
    # Background removal (optimized)
    # ---------------------------

    def _remove_background_sync(self, image: Image.Image) -> Image.Image:
        """
        Synchronous background removal (CPU-bound).
        Wrapped by run_in_executor to avoid blocking the event loop.
        """
        try:
            return remove(image, session=self.bg_session)
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            return image  # fallback to original image if removal fails

    async def remove_backgrounds_batch(
        self,
        stickers: List[Tuple[str, Image.Image]],
        max_concurrency: int = 2,
    ) -> List[Tuple[str, Image.Image]]:
        """
        Remove backgrounds from all stickers without blocking event loop.
        Uses a small concurrency limit to avoid CPU overload.
        """
        logger.info(f"Removing backgrounds from {len(stickers)} stickers...")

        loop = asyncio.get_running_loop()
        sem = asyncio.Semaphore(max(1, int(max_concurrency)))

        async def _process_one(expression: str, img: Image.Image) -> Tuple[str, Image.Image]:
            async with sem:
                no_bg = await loop.run_in_executor(None, self._remove_background_sync, img)
                logger.info(f"  ✓ Background removed: {expression}")
                return expression, no_bg

        tasks = [_process_one(expr, img) for expr, img in stickers]
        processed = await asyncio.gather(*tasks)

        logger.info("✅ All backgrounds removed")
        return list(processed)

    # ---------------------------
    # Persistence + encoding
    # ---------------------------

    async def save_stickers_to_disk(
        self,
        stickers: List[Tuple[str, Image.Image]],
        job_id: str,
    ) -> List[str]:
        """
        Save stickers to disk.
        """
        filepaths: List[str] = []

        for expression, image in stickers:
            filename = f"sticker-{job_id}-{expression}.png"
            filepath = os.path.join(settings.OUTPUT_DIR, filename)
            save_image_to_disk(image, filepath)
            filepaths.append(filepath)

        logger.info(f"✅ {len(filepaths)} stickers saved to disk")
        return filepaths

    async def encode_stickers(
        self,
        stickers: List[Tuple[str, Image.Image]],
    ) -> List[dict]:
        """
        Encode stickers to base64 for API response.
        """
        encoded: List[dict] = []
        for expression, image in stickers:
            encoded.append(
                {
                    "mood": expression,
                    "image": pil_to_base64(image, format="PNG"),
                }
            )

        logger.info(f"✅ {len(encoded)} stickers encoded")
        return encoded

    # ---------------------------
    # Main orchestration
    # ---------------------------

    async def generate_stickers_from_base64(
        self,
        base64_image: str,
        seed: Optional[int] = None,
        expressions: Optional[List[str]] = None,
        save_to_disk: bool = True,
        job_id: Optional[str] = None,
    ) -> dict:
        """
        Main orchestration method: Generate stickers from base64 image.
        """
        t0 = time.time()
        timings: Dict[str, float] = {}

        try:
            logger.info("=" * 60)
            logger.info("Starting sticker generation process")
            logger.info("=" * 60)

            generation_seed = int(seed) if seed is not None else int(settings.SEED_BASE)
            logger.info(f"Using seed: {generation_seed}")

            # Validate expressions early (fast failure)
            requested_expressions = self._validate_expressions(expressions)

            # Step 1: Preprocess
            logger.info("Step 1/5: Preprocessing image...")
            s = time.time()
            input_image = await self.preprocess_image(base64_image)
            timings["preprocess_s"] = round(time.time() - s, 3)

            # Step 2: Generate (GPU)
            logger.info("Step 2/5: Generating expressions...")
            s = time.time()
            generated_stickers = await self.generate_all_expressions(
                image=input_image,
                seed=generation_seed,
                expressions=requested_expressions,
            )
            timings["generation_s"] = round(time.time() - s, 3)

            # Step 3: Remove background (CPU, non-blocking)
            logger.info("Step 3/5: Removing backgrounds...")
            s = time.time()
            stickers_no_bg = await self.remove_backgrounds_batch(
                generated_stickers,
                max_concurrency=2,  # safe default; tune based on CPU cores
            )
            timings["bg_removal_s"] = round(time.time() - s, 3)

            # Step 4: Save to disk (optional)
            if save_to_disk and settings.SAVE_TO_DISK:
                logger.info("Step 4/5: Saving to disk...")
                s = time.time()
                save_job_id = job_id or str(uuid.uuid4())[:8]
                await self.save_stickers_to_disk(stickers_no_bg, save_job_id)
                timings["disk_save_s"] = round(time.time() - s, 3)
            else:
                logger.info("Step 4/5: Skipping disk save")

            # Step 5: Encode to base64
            logger.info("Step 5/5: Encoding stickers...")
            s = time.time()
            encoded_stickers = await self.encode_stickers(stickers_no_bg)
            timings["encode_s"] = round(time.time() - s, 3)

            processing_time = round(time.time() - t0, 2)

            # Cleanup GPU cache (safe; optional to tune later)
            clear_gpu_memory()

            logger.info("=" * 60)
            logger.info(f"✅ Generation complete in {processing_time}s")
            logger.info(f"Generated {len(encoded_stickers)} stickers")
            logger.info(f"Timings: {timings}")
            logger.info("=" * 60)

            return {
                "success": True,
                "processing_time": processing_time,
                "timings": timings,
                "stickers": encoded_stickers,
                "metadata": {
                    "seed": generation_seed,
                    "num_stickers": len(encoded_stickers),
                    "expressions": [s["mood"] for s in encoded_stickers],
                },
            }

        except Exception as e:
            processing_time = round(time.time() - t0, 2)
            logger.error(f"❌ Generation failed after {processing_time}s: {e}")

            clear_gpu_memory()
            raise


# Global service instance
sticker_service = StickerGenerationService()
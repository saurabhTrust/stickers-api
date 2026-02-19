# """
# Model Manager: Handles loading and managing SDXL + LoRA models
# (Production-hardened version)
# """
# import os
# import asyncio
# from typing import Optional

# import torch
# from diffusers import StableDiffusionXLImg2ImgPipeline
# from PIL import Image
# from loguru import logger

# from app.config import settings, get_lora_path
# from app.utils import clear_gpu_memory, get_gpu_memory_info


# class ModelManager:
#     """
#     Manages SDXL pipeline with LoRA for sticker generation
#     """

#     def __init__(self):
#         self.pipeline: Optional[StableDiffusionXLImg2ImgPipeline] = None
#         self.device = "cuda" if torch.cuda.is_available() else "cpu"
#         self.dtype = torch.float16 if self.device == "cuda" else torch.float32
#         self.generation_lock = asyncio.Lock()
#         self.is_loaded = False

#         logger.info(f"ModelManager initialized on device: {self.device}")

#     def load_models(self):
#         """
#         Load SDXL pipeline and LoRA weights
#         """
#         try:
#             logger.info("=" * 60)
#             logger.info("Starting model loading process...")
#             logger.info("=" * 60)

#             # Check GPU availability
#             if not torch.cuda.is_available():
#                 raise RuntimeError("CUDA is not available. GPU is required.")

#             # Apply GPU memory fraction (IMPORTANT: makes config effective)
#             try:
#                 torch.cuda.set_per_process_memory_fraction(
#                     settings.GPU_MEMORY_FRACTION,
#                     device=torch.cuda.current_device()
#                 )
#                 logger.info(f"✓ GPU memory fraction set to: {settings.GPU_MEMORY_FRACTION}")
#             except Exception as e:
#                 logger.warning(f"Could not set GPU memory fraction: {e}")

#             gpu_info = get_gpu_memory_info()
#             logger.info(f"GPU: {gpu_info.get('device', 'Unknown')}")
#             logger.info(f"Total GPU Memory: {gpu_info.get('total_gb', 0)} GB")

#             # Step 1: Load SDXL Img2Img Pipeline
#             logger.info(f"Loading SDXL model: {settings.SDXL_MODEL_ID}")
#             self.pipeline = StableDiffusionXLImg2ImgPipeline.from_pretrained(
#                 settings.SDXL_MODEL_ID,
#                 torch_dtype=self.dtype,
#                 use_safetensors=True,
#                 cache_dir=settings.MODEL_CACHE_DIR,
#             )
#             logger.info("SDXL model loaded")

#             # Disable safety checker (prevents random blocked outputs)
#             self.pipeline.safety_checker = None

#             # Step 2: Load LoRA weights (if present)
#             lora_path = get_lora_path()
#             lora_dir = os.path.dirname(lora_path)
#             if os.path.exists(lora_path):
#                 logger.info(f"Loading LoRA from: {lora_path}")
#                 self.pipeline.load_lora_weights(
#                     lora_dir,
#                     weight_name=settings.LORA_FILENAME
#                 )

#                 # Fuse LoRA for performance + consistent scaling
#                 try:
#                     self.pipeline.fuse_lora(lora_scale=settings.LORA_SCALE)
#                     logger.info(f"LoRA fused with scale: {settings.LORA_SCALE}")
#                 except Exception as e:
#                     # If fuse isn't supported, fallback to cross_attention_kwargs in generation
#                     logger.warning(f"LoRA fuse failed, will use runtime scaling: {e}")

#                 logger.info("LoRA loaded")
#             else:
#                 logger.warning(f"LoRA file not found at: {lora_path}")
#                 logger.warning("Service will work but without LoRA style")

#             # Step 3: Move to GPU
#             logger.info("Moving pipeline to GPU...")
#             self.pipeline = self.pipeline.to(self.device)

#             # Step 4: Enable optimizations
#             logger.info("Enabling optimizations...")

#             # Enable attention slicing
#             self.pipeline.enable_attention_slicing()
#             logger.info("  ✓ Attention slicing enabled")

#             # Enable VAE slicing
#             self.pipeline.enable_vae_slicing()
#             logger.info("  ✓ VAE slicing enabled")

#             # Enable xformers if available
#             if settings.ENABLE_XFORMERS:
#                 try:
#                     self.pipeline.enable_xformers_memory_efficient_attention()
#                     logger.info("  ✓ xformers enabled")
#                 except Exception as e:
#                     logger.warning(f" xformers not available: {e}")

#             # Step 5: Warm-up run
#             logger.info("Performing warm-up generation...")
#             self._warmup()

#             self.is_loaded = True

#             # Final memory check
#             final_gpu_info = get_gpu_memory_info()
#             logger.info("=" * 60)
#             logger.info("Model loading complete!")
#             logger.info(f"GPU Memory Reserved: {final_gpu_info.get('reserved_gb', 0)} GB")
#             logger.info(f"GPU Memory Allocated: {final_gpu_info.get('allocated_gb', 0)} GB")
#             logger.info(f"GPU Memory Free: {final_gpu_info.get('free_gb', 0)} GB")
#             logger.info("=" * 60)

#         except Exception as e:
#             logger.error(f"Failed to load models: {e}")
#             raise

#     def _warmup(self):
#         """
#         Perform a warm-up generation to initialize CUDA kernels
#         """
#         try:
#             if self.pipeline is None:
#                 return

#             # Create a dummy image (use configured size)
#             dummy_image = Image.new(
#                 "RGB",
#                 (settings.IMAGE_SIZE, settings.IMAGE_SIZE),
#                 color="white"
#             )

#             generator = torch.Generator(device=self.device).manual_seed(settings.SEED_BASE)

#             # Warm-up uses minimal steps
#             with torch.inference_mode():
#                 _ = self.pipeline(
#                     prompt="3DRenderAF, cartoon character, high quality",
#                     negative_prompt="low quality, blurry, distorted",
#                     image=dummy_image,
#                     strength=min(0.35, max(0.1, settings.STRENGTH)),
#                     num_inference_steps=5,
#                     guidance_scale=settings.GUIDANCE_SCALE,
#                     generator=generator,
#                 )

#             logger.info("Warm-up generation complete")

#         except Exception as e:
#             logger.warning(f"Warm-up failed (non-critical): {e}")

#     async def generate_sticker(
#         self,
#         image: Image.Image,
#         prompt: str,
#         negative_prompt: str,
#         seed: int
#     ) -> Image.Image:
#         """
#         Generate a single sticker using SDXL + LoRA
#         """
#         if not self.is_loaded or self.pipeline is None:
#             raise RuntimeError("Models not loaded. Call load_models() first.")

#         # Use lock to prevent concurrent GPU access
#         async with self.generation_lock:
#             try:
#                 generator = torch.Generator(device=self.device).manual_seed(seed)

#                 # Use inference_mode for lower memory + faster speed
#                 with torch.inference_mode():
#                     output = self.pipeline(
#                         prompt=prompt,
#                         negative_prompt=negative_prompt,
#                         image=image,
#                         strength=settings.STRENGTH,
#                         num_inference_steps=settings.NUM_INFERENCE_STEPS,
#                         guidance_scale=settings.GUIDANCE_SCALE,
#                         generator=generator,
#                     )

#                 return output.images[0]

#             except Exception as e:
#                 logger.error(f"Generation failed: {e}")
#                 raise

#     def get_health_status(self) -> dict:
#         """
#         Get health status of model manager
#         """
#         gpu_info = get_gpu_memory_info()

#         return {
#             "model_loaded": self.is_loaded,
#             "device": self.device,
#             "dtype": str(self.dtype),
#             "gpu_available": torch.cuda.is_available(),
#             "gpu_info": gpu_info,
#         }

#     def cleanup(self):
#         """
#         Cleanup GPU memory
#         """
#         clear_gpu_memory()
#         logger.info("Model manager cleanup complete")


# # Global model manager instance
# model_manager = ModelManager()

"""
Model Manager: Handles loading and managing SDXL + LoRA models
(Ultra-optimized production version)
"""

import os
import asyncio
from typing import Optional

import torch
from diffusers import StableDiffusionXLImg2ImgPipeline
from PIL import Image
from loguru import logger

from app.config import settings, get_lora_path
from app.utils import clear_gpu_memory, get_gpu_memory_info


class ModelManager:
    """
    Manages SDXL pipeline with LoRA for sticker generation
    """

    def __init__(self):
        self.pipeline: Optional[StableDiffusionXLImg2ImgPipeline] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.generation_lock = asyncio.Lock()
        self.is_loaded = False

        logger.info(f"ModelManager initialized on device: {self.device}")

    def load_models(self):
        """Load SDXL pipeline and LoRA weights"""
        try:
            logger.info("=" * 60)
            logger.info("Starting model loading process...")
            logger.info("=" * 60)

            if not torch.cuda.is_available():
                raise RuntimeError("CUDA is not available. GPU is required.")

            # TF32 SPEED BOOST
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            logger.info("✓ TF32 enabled")

            # GPU memory fraction
            try:
                torch.cuda.set_per_process_memory_fraction(
                    settings.GPU_MEMORY_FRACTION,
                    device=torch.cuda.current_device(),
                )
                logger.info(f"✓ GPU memory fraction set to: {settings.GPU_MEMORY_FRACTION}")
            except Exception as e:
                logger.warning(f"Could not set GPU memory fraction: {e}")

            gpu_info = get_gpu_memory_info()
            logger.info(f"GPU: {gpu_info.get('device', 'Unknown')}")
            logger.info(f"Total GPU Memory: {gpu_info.get('total_gb', 0)} GB")

            # ========================
            # Load SDXL
            # ========================
            logger.info(f"Loading SDXL model: {settings.SDXL_MODEL_ID}")

            self.pipeline = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                settings.SDXL_MODEL_ID,
                torch_dtype=self.dtype,
                use_safetensors=True,
                cache_dir=settings.MODEL_CACHE_DIR,
            )

            # MOVE TO GPU EARLY (IMPORTANT)
            self.pipeline = self.pipeline.to(self.device)
            logger.info("✓ Pipeline moved to GPU early")

            # Disable safety checker
            self.pipeline.safety_checker = None

            # ========================
            # Load LoRA
            # ========================
            lora_path = get_lora_path()
            lora_dir = os.path.dirname(lora_path)

            if os.path.exists(lora_path):
                logger.info(f"Loading LoRA from: {lora_path}")

                self.pipeline.load_lora_weights(
                    lora_dir,
                    weight_name=settings.LORA_FILENAME,
                )

                try:
                    self.pipeline.fuse_lora(lora_scale=settings.LORA_SCALE)
                    logger.info(f"✓ LoRA fused (scale={settings.LORA_SCALE})")
                except Exception as e:
                    logger.warning(f"LoRA fuse failed, using runtime scaling: {e}")
            else:
                logger.warning(f"LoRA file not found at: {lora_path}")

            # ========================
            # Optimizations
            # ========================
            logger.info("Enabling optimizations...")

            # xformers first
            xformers_enabled = False
            if settings.ENABLE_XFORMERS:
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                    xformers_enabled = True
                    logger.info("  ✓ xformers enabled")
                except Exception as e:
                    logger.warning(f"xformers not available: {e}")

            # attention slicing ONLY if no xformers
            if not xformers_enabled:
                self.pipeline.enable_attention_slicing()
                logger.info("  ✓ Attention slicing enabled")

            # VAE optimizations
            self.pipeline.enable_vae_slicing()
            self.pipeline.enable_vae_tiling()
            logger.info("  ✓ VAE slicing + tiling enabled")

            # ========================
            # Optional UNet compile
            # ========================
            # try:
            #     logger.info("Compiling UNet with torch.compile...")
            #     self.pipeline.unet = torch.compile(
            #         self.pipeline.unet,
            #         mode="reduce-overhead",
            #     )
            #     logger.info("✓ UNet compiled")
            # except Exception as e:
            #     logger.warning(f"UNet compile skipped: {e}")

            # ========================
            # Warmup
            # ========================
            logger.info("Performing warm-up generation...")
            self._warmup()

            self.is_loaded = True

            final_gpu_info = get_gpu_memory_info()
            logger.info("=" * 60)
            logger.info("Model loading complete!")
            logger.info(f"GPU Memory Allocated: {final_gpu_info.get('allocated_gb', 0)} GB")
            logger.info(f"GPU Memory Free: {final_gpu_info.get('free_gb', 0)} GB")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise

    def _warmup(self):
        """Warm-up CUDA kernels"""
        try:
            if self.pipeline is None:
                return

            dummy_image = Image.new(
                "RGB",
                (512,512),
                color="white",
            )

            generator = torch.Generator(device=self.device).manual_seed(settings.SEED_BASE)

            with torch.inference_mode():
                _ = self.pipeline(
                    prompt="3DRenderAF, cartoon character",
                    negative_prompt="low quality, blurry",
                    image=dummy_image,
                    strength=settings.STRENGTH,
                    num_inference_steps=4,  # faster warmup
                    guidance_scale=settings.GUIDANCE_SCALE,
                    generator=generator,
                )

            logger.info("✓ Warm-up complete")

        except Exception as e:
            logger.warning(f"Warm-up failed (non-critical): {e}")

    async def generate_sticker(
        self,
        image: Image.Image,
        prompt: str,
        negative_prompt: str,
        seed: int,
    ) -> Image.Image:
        """Generate a single sticker"""
        if not self.is_loaded or self.pipeline is None:
            raise RuntimeError("Models not loaded.")

        async with self.generation_lock:
            try:
                generator = torch.Generator(device=self.device).manual_seed(seed)

                with torch.inference_mode():
                    output = self.pipeline(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        image=image,
                        strength=settings.STRENGTH,
                        num_inference_steps=settings.NUM_INFERENCE_STEPS,
                        guidance_scale=settings.GUIDANCE_SCALE,
                        generator=generator,
                    )

                return output.images[0]

            except Exception as e:
                logger.error(f"Generation failed: {e}")
                raise

    def get_health_status(self) -> dict:
        gpu_info = get_gpu_memory_info()
        return {
            "model_loaded": self.is_loaded,
            "device": self.device,
            "dtype": str(self.dtype),
            "gpu_available": torch.cuda.is_available(),
            "gpu_info": gpu_info,
        }

    def cleanup(self):
        clear_gpu_memory()
        logger.info("Model manager cleanup complete")


model_manager = ModelManager()
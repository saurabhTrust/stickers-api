#!/bin/bash

# Production launcher for GPU Sticker Generation Service

set -e

echo "======================================================================="
echo "🚀 Starting GPU Sticker Generation Service"
echo "======================================================================="
echo ""

# --------------------------------------------------

# Activate virtual environment

# --------------------------------------------------

if [ -d "venv" ]; then
source venv/bin/activate
echo "✅ Virtual environment activated"
else
echo "❌ Virtual environment not found"
echo "   Please run ./install.sh first"
exit 1
fi

# --------------------------------------------------

# Load environment variables

# --------------------------------------------------

if [ -f ".env" ]; then
export $(grep -v '^#' .env | xargs)
fi

# --------------------------------------------------

# GPU sanity check

# --------------------------------------------------

echo "🔍 Checking GPU..."
python - <<EOF
import torch
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
print("GPU:", torch.cuda.get_device_name(0))
EOF
echo ""

# --------------------------------------------------

# First-run SDXL notice

# --------------------------------------------------

if [ ! -d "model_cache" ] || [ -z "$(ls -A model_cache 2>/dev/null)" ]; then
echo "⏳ First run detected!"
echo "   SDXL models will be downloaded (~6 GB)"
echo "   This will take 10-15 minutes"
echo ""
fi

# --------------------------------------------------

# Ensure LoRA exists

# --------------------------------------------------

LORA_PATH="./models/lora/3DRedmond-3DRenderStyle-3DRenderAF.safetensors"

if [ ! -f "$LORA_PATH" ]; then
echo "⚠️  LoRA model not found — downloading..."
python download_lora.py
fi

# --------------------------------------------------

# Server info

# --------------------------------------------------

HOST=${API_HOST:-0.0.0.0}
PORT=${API_PORT:-5000}

echo ""
echo "📍 Service will start at:"
echo "   http://$HOST:$PORT"
echo ""
echo "📚 API Docs:"
echo "   http://$HOST:$PORT/docs"
echo ""
echo "======================================================================="
echo ""

# --------------------------------------------------

# Start FastAPI (production uvicorn)

# --------------------------------------------------

exec uvicorn app.main:app 
--host "$HOST" 
--port "$PORT" 
--workers 1 
--timeout-keep-alive 120 
--log-level info

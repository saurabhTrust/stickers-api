#!/bin/bash

# Production Installation script for GPU Sticker Service

set -e  # Exit on error

echo "======================================================================="
echo "GPU Sticker Generation Service - Installation"
echo "======================================================================="
echo ""

# ------------------------------------------------------------------

# Root check

# ------------------------------------------------------------------

if [ "$EUID" -ne 0 ]; then
echo "⚠️  Please run as root"
exit 1
fi

# ------------------------------------------------------------------

# CUDA check

# ------------------------------------------------------------------

echo "🔍 Checking CUDA..."
if ! command -v nvidia-smi &> /dev/null; then
echo "❌ nvidia-smi not found. Please install NVIDIA drivers."
exit 1
fi

nvidia-smi
echo ""

# ------------------------------------------------------------------

# Python check

# ------------------------------------------------------------------

echo "🐍 Python version:"
python3 --version
echo ""

# ------------------------------------------------------------------

# Disk space check (SDXL is heavy)

# ------------------------------------------------------------------

echo "💾 Disk space:"
df -h .
echo ""

# ------------------------------------------------------------------

# System packages

# ------------------------------------------------------------------

echo "📦 Updating system packages..."
apt update
apt install -y python3-pip python3-venv git

# ------------------------------------------------------------------

# Virtual environment

# ------------------------------------------------------------------

echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# ------------------------------------------------------------------

# Pip upgrade

# ------------------------------------------------------------------

echo "📦 Upgrading pip..."
pip install --upgrade pip wheel setuptools

# ------------------------------------------------------------------

# PyTorch (CUDA wheels)

# ------------------------------------------------------------------

echo "🔥 Installing PyTorch 2.2.1 (CUDA 12.1 wheels)..."
echo "   This may take 5-10 minutes..."
pip install torch==2.2.1 torchvision==0.17.1 torchaudio==2.2.1 
--index-url https://download.pytorch.org/whl/cu121

# ------------------------------------------------------------------

# Other requirements

# ------------------------------------------------------------------

echo "📦 Installing Python dependencies..."
echo "   This may take 5-10 minutes..."
pip install -r requirements.txt

# ------------------------------------------------------------------

# xformers check (non-fatal)

# ------------------------------------------------------------------

python -c "import xformers; print('✓ xformers OK')" || echo "⚠️ xformers not available"

# ------------------------------------------------------------------

# Create directories

# ------------------------------------------------------------------

echo "📁 Creating directories..."
mkdir -p models/lora
mkdir -p output
mkdir -p logs
mkdir -p model_cache

# ------------------------------------------------------------------

# Download LoRA

# ------------------------------------------------------------------

echo ""
echo "📥 Downloading LoRA model..."
echo "   This may take 2-5 minutes (~143 MB)..."
python download_lora.py

echo ""
echo "======================================================================="
echo "✅ Installation Complete!"
echo "======================================================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start service: python -m app.main"
echo ""
echo "Note: First run will download SDXL models (~6 GB)"
echo "======================================================================="

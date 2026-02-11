#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# Single-Node Multi-GPU Fine-Tuning with LlamaFactory
# ──────────────────────────────────────────────────────────
#
# What this does:
#   Launches LoRA fine-tuning across all GPUs on one machine.
#   LlamaFactory wraps torchrun + DDP internally.
#
# Prerequisites:
#   - LlamaFactory installed (pip install llamafactory)
#   - CUDA-compatible GPUs visible (nvidia-smi)
#   - Dataset registered in LlamaFactory's dataset_info.json
#
# Usage:
#   bash scripts/finetune_single_node.sh
#
# Flags may vary by LlamaFactory version.
# ──────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration (edit these) ──────────────────────────

MODEL_NAME_OR_PATH="meta-llama/Llama-3.1-8B-Instruct"
DATA_PATH="my_support_data"          # dataset name in dataset_info.json
OUTPUT_DIR="./output/lora_single_node"
CONFIG_FILE="configs/finetune_lora_single_node.yaml"

# Number of GPUs (auto-detect or set manually)
NUM_GPUS=$(nvidia-smi -L | wc -l)

echo "============================================"
echo "  Single-Node Multi-GPU Fine-Tuning"
echo "  GPUs detected: ${NUM_GPUS}"
echo "  Model: ${MODEL_NAME_OR_PATH}"
echo "  Dataset: ${DATA_PATH}"
echo "  Output: ${OUTPUT_DIR}"
echo "============================================"

# ── Option A: Let LlamaFactory handle everything ────────
# Simplest approach — auto-detects GPUs.

llamafactory-cli train "${CONFIG_FILE}"

# ── Option B: Explicit torchrun (if you need control) ───
# Uncomment below and comment out Option A if needed.
#
# torchrun \
#     --nproc_per_node="${NUM_GPUS}" \
#     --master_port=29500 \
#     -m llamafactory.train \
#     "${CONFIG_FILE}"

echo "============================================"
echo "  Training complete."
echo "  Adapter saved to: ${OUTPUT_DIR}"
echo "============================================"

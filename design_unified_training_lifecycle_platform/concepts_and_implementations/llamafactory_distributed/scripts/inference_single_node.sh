#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# Single-Node Multi-GPU Inference with LlamaFactory
# ──────────────────────────────────────────────────────────
#
# What this does:
#   Launches an OpenAI-compatible API server using vLLM.
#   vLLM auto-detects GPUs for tensor parallel or data parallel.
#
# Prerequisites:
#   - LlamaFactory installed with vLLM backend
#   - Model weights available locally or on HuggingFace
#
# Usage:
#   bash scripts/inference_single_node.sh
#
# Flags may vary by LlamaFactory version.
# ──────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration (edit these) ──────────────────────────

MODEL_NAME_OR_PATH="meta-llama/Llama-3.1-8B-Instruct"
CONFIG_FILE="configs/inference_single_node.yaml"
PORT=8000

echo "============================================"
echo "  Single-Node Inference Server"
echo "  Model: ${MODEL_NAME_OR_PATH}"
echo "  Port: ${PORT}"
echo "  Backend: vLLM"
echo "============================================"

# ── Option A: LlamaFactory API server ───────────────────
# Starts an OpenAI-compatible API at http://localhost:${PORT}

llamafactory-cli api "${CONFIG_FILE}"

# ── Option B: Run specific GPUs only ────────────────────
# Uncomment to restrict to specific GPUs.
#
# CUDA_VISIBLE_DEVICES=0,1 llamafactory-cli api "${CONFIG_FILE}"

# ── Test it ──────────────────────────────────────────────
# curl http://localhost:8000/v1/chat/completions \
#   -H "Content-Type: application/json" \
#   -d '{
#     "model": "meta-llama/Llama-3.1-8B-Instruct",
#     "messages": [{"role": "user", "content": "Hello!"}],
#     "max_tokens": 100
#   }'

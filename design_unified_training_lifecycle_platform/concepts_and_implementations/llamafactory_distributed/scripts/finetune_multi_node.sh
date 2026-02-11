#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# Multi-Node Multi-GPU Fine-Tuning with LlamaFactory
# ──────────────────────────────────────────────────────────
#
# What this does:
#   Launches LoRA fine-tuning across multiple machines.
#   Uses torchrun with rendezvous for multi-node DDP.
#
# Prerequisites:
#   - Same LlamaFactory version on ALL nodes
#   - Same model + dataset accessible on ALL nodes (shared storage)
#   - Network connectivity between all nodes (NCCL port open)
#
# Usage:
#   Run this script on EACH node with the correct NODE_RANK.
#
#   Node 0: NODE_RANK=0 bash scripts/finetune_multi_node.sh
#   Node 1: NODE_RANK=1 bash scripts/finetune_multi_node.sh
#
# Flags may vary by LlamaFactory version.
# ──────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration (edit these) ──────────────────────────

MODEL_NAME_OR_PATH="meta-llama/Llama-3.1-8B-Instruct"
DATA_PATH="my_support_data"
OUTPUT_DIR="./output/lora_multi_node"
CONFIG_FILE="configs/finetune_lora_multi_node.yaml"

# ── Multi-node settings ─────────────────────────────────
# MASTER_ADDR: IP of node 0 (the rendezvous point)
# MASTER_PORT: any free port — must be the same on all nodes
# NNODES: total number of machines
# NODE_RANK: 0 for master, 1 for second node, etc.
#            Set via environment variable before running.

MASTER_ADDR="${MASTER_ADDR:-10.0.0.1}"
MASTER_PORT="${MASTER_PORT:-29500}"
NNODES="${NNODES:-2}"
NODE_RANK="${NODE_RANK:-0}"
NPROC_PER_NODE="${NPROC_PER_NODE:-4}"

echo "============================================"
echo "  Multi-Node Fine-Tuning"
echo "  Node rank: ${NODE_RANK} / ${NNODES}"
echo "  GPUs per node: ${NPROC_PER_NODE}"
echo "  Master: ${MASTER_ADDR}:${MASTER_PORT}"
echo "  Model: ${MODEL_NAME_OR_PATH}"
echo "  Output: ${OUTPUT_DIR}"
echo "============================================"

# ── NCCL tuning (optional but recommended) ──────────────
# Timeout: fail faster on network issues (default is 30 min)
export NCCL_TIMEOUT=300

# Use InfiniBand if available (comment out if not)
# export NCCL_IB_DISABLE=0
# export NCCL_NET_GDR_LEVEL=5

# ── Launch training ──────────────────────────────────────

torchrun \
    --nnodes="${NNODES}" \
    --nproc_per_node="${NPROC_PER_NODE}" \
    --node_rank="${NODE_RANK}" \
    --master_addr="${MASTER_ADDR}" \
    --master_port="${MASTER_PORT}" \
    -m llamafactory.train \
    "${CONFIG_FILE}"

echo "============================================"
echo "  Node ${NODE_RANK}: Training complete."
echo "============================================"

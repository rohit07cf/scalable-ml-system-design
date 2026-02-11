#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# Multi-Node Inference with LlamaFactory
# ──────────────────────────────────────────────────────────
#
# What this does:
#   Launches an independent inference replica on this node.
#   Each node is a standalone vLLM server.
#   A load balancer in front distributes requests.
#
# Architecture:
#   Load Balancer → [Node 0 :8000] [Node 1 :8000] [Node 2 :8000]
#   Each node = independent, no cross-node communication.
#
# Prerequisites:
#   - Model weights accessible on this node (shared storage / local cache)
#   - Load balancer configured separately (nginx, HAProxy, K8s Service)
#
# Usage:
#   Run this on EACH node:
#   bash scripts/inference_multi_node.sh
#
# Flags may vary by LlamaFactory version.
# ──────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration (edit these) ──────────────────────────

MODEL_NAME_OR_PATH="/models/llama-3-8b-support"  # local cached path
CONFIG_FILE="configs/inference_multi_node.yaml"
PORT="${PORT:-8000}"

# Identify this node (for logging)
NODE_ID="${HOSTNAME:-$(hostname)}"

echo "============================================"
echo "  Multi-Node Inference Replica"
echo "  Node: ${NODE_ID}"
echo "  Model: ${MODEL_NAME_OR_PATH}"
echo "  Port: ${PORT}"
echo "============================================"

# ── Pre-flight check ────────────────────────────────────
# Ensure model weights are available locally.
# In production, an init container or startup script
# would pull from S3/NFS before this runs.

if [ ! -d "${MODEL_NAME_OR_PATH}" ]; then
    echo "WARNING: Model path ${MODEL_NAME_OR_PATH} not found locally."
    echo "In production, pull from shared storage first."
    echo "Example: aws s3 sync s3://models/llama-3-8b-support/ ${MODEL_NAME_OR_PATH}"
fi

# ── Launch inference server ──────────────────────────────
# Each node is independent — no rendezvous needed.

llamafactory-cli api "${CONFIG_FILE}"

# ── Note on load balancer ────────────────────────────────
# Configure your load balancer to route to all nodes:
#
# nginx example:
#   upstream llm {
#       least_conn;
#       server node0:8000;
#       server node1:8000;
#       server node2:8000;
#   }
#
# K8s: use a Deployment + Service (see 06_multi_node_inference.md)

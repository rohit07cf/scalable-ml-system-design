"""
Minimal LlamaFactory Launcher
==============================

A small Python wrapper that:
  1. Validates inputs using Pydantic (paths, GPU count, mode)
  2. Builds the exact LlamaFactory / torchrun command
  3. Prints the command (for review)
  4. Optionally runs it (subprocess)

Usage:
  python minimal_llamafactory_launcher.py

This is interview/learning reference code.
"""

import subprocess
import shutil
from pathlib import Path
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


# ──────────────────────────────────────────────
# Pydantic Models for Validation
# ──────────────────────────────────────────────

class LaunchMode(str, Enum):
    """What are we doing?"""
    TRAIN = "train"         # fine-tuning
    API = "api"             # inference server


class NodeConfig(BaseModel):
    """Multi-node settings. Only needed for multi-node training."""
    nnodes: int = 1
    node_rank: int = 0
    master_addr: str = "127.0.0.1"
    master_port: int = 29500


class LaunchConfig(BaseModel):
    """
    Everything needed to build a LlamaFactory launch command.
    Pydantic validates all inputs before we build the command.
    """

    mode: LaunchMode                    # train or api
    config_path: str                    # path to YAML config
    num_gpus: int = 1                   # GPUs on this machine
    node_config: Optional[NodeConfig] = None  # multi-node settings (optional)
    dry_run: bool = True                # print command only (don't execute)

    # ── Validators ────────────────────────────

    @field_validator("config_path")
    @classmethod
    def config_must_exist(cls, v: str) -> str:
        """Check that the config file actually exists."""
        if not Path(v).exists():
            raise ValueError(f"Config file not found: {v}")
        return v

    @field_validator("num_gpus")
    @classmethod
    def gpus_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"num_gpus must be >= 1, got {v}")
        return v


# ──────────────────────────────────────────────
# Command Builder
# ──────────────────────────────────────────────

def build_command(config: LaunchConfig) -> list[str]:
    """
    Build the exact shell command based on launch config.

    Returns a list of command parts (like subprocess expects).
    """

    # ── Inference mode: simple, no torchrun ──
    if config.mode == LaunchMode.API:
        return ["llamafactory-cli", "api", config.config_path]

    # ── Training mode ──

    # Single-node: let LlamaFactory handle it
    if config.num_gpus == 1 and (config.node_config is None or config.node_config.nnodes == 1):
        return ["llamafactory-cli", "train", config.config_path]

    # Multi-GPU or multi-node: use torchrun
    cmd = [
        "torchrun",
        f"--nproc_per_node={config.num_gpus}",
    ]

    # Add multi-node flags if needed
    nc = config.node_config
    if nc and nc.nnodes > 1:
        cmd.extend([
            f"--nnodes={nc.nnodes}",
            f"--node_rank={nc.node_rank}",
            f"--master_addr={nc.master_addr}",
            f"--master_port={nc.master_port}",
        ])
    else:
        cmd.append("--master_port=29500")

    # The actual training module
    cmd.extend(["-m", "llamafactory.train", config.config_path])

    return cmd


# ──────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────

def run(config: LaunchConfig) -> None:
    """Build, print, and optionally execute the command."""

    cmd = build_command(config)
    cmd_str = " ".join(cmd)

    print("=" * 60)
    print(f"  Mode:     {config.mode.value}")
    print(f"  Config:   {config.config_path}")
    print(f"  GPUs:     {config.num_gpus}")
    if config.node_config and config.node_config.nnodes > 1:
        nc = config.node_config
        print(f"  Nodes:    {nc.nnodes} (this is rank {nc.node_rank})")
        print(f"  Master:   {nc.master_addr}:{nc.master_port}")
    print(f"  Dry run:  {config.dry_run}")
    print("=" * 60)
    print(f"\n  Command:\n  {cmd_str}\n")

    if config.dry_run:
        print("  (dry run — command not executed)")
        print("  Set dry_run=False to actually run.\n")
        return

    # Check that the tool exists
    if not shutil.which(cmd[0]):
        print(f"  ERROR: '{cmd[0]}' not found in PATH.")
        print("  Install LlamaFactory: pip install llamafactory")
        return

    print("  Executing...\n")
    subprocess.run(cmd, check=True)


# ──────────────────────────────────────────────
# Example usage
# ──────────────────────────────────────────────

if __name__ == "__main__":

    # Example 1: Single-node LoRA training (4 GPUs)
    print("\n--- Example 1: Single-node training ---\n")
    try:
        config = LaunchConfig(
            mode=LaunchMode.TRAIN,
            config_path="configs/finetune_lora_single_node.yaml",
            num_gpus=4,
            dry_run=True,
        )
        run(config)
    except Exception as e:
        print(f"  Validation error: {e}\n")

    # Example 2: Multi-node training (2 nodes × 4 GPUs)
    print("\n--- Example 2: Multi-node training ---\n")
    try:
        config = LaunchConfig(
            mode=LaunchMode.TRAIN,
            config_path="configs/finetune_lora_multi_node.yaml",
            num_gpus=4,
            node_config=NodeConfig(
                nnodes=2,
                node_rank=0,
                master_addr="10.0.0.1",
                master_port=29500,
            ),
            dry_run=True,
        )
        run(config)
    except Exception as e:
        print(f"  Validation error: {e}\n")

    # Example 3: Inference server
    print("\n--- Example 3: Inference server ---\n")
    try:
        config = LaunchConfig(
            mode=LaunchMode.API,
            config_path="configs/inference_single_node.yaml",
            dry_run=True,
        )
        run(config)
    except Exception as e:
        print(f"  Validation error: {e}\n")

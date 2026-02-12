"""
Three-Phase Training Toy Example
=================================

This is an EDUCATIONAL TOY, not production code.

It demonstrates the pipeline structure of frontier LLM training:
  Phase 1: Pre-training   (self-supervised next-token prediction)
  Phase 2: SFT            (supervised instruction following)
  Phase 3: Alignment      (DPO-style preference optimization)

Uses a tiny dummy model (embedding + linear) so the script is
self-contained — no HuggingFace downloads, no GPU required.

The point: understand the FLOW of data and objectives across phases.
"""

import json
import os
import random
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


# ──────────────────────────────────────────────
# TINY MODEL
# ──────────────────────────────────────────────
# A minimal "language model" with:
#   - Token embedding
#   - One linear hidden layer
#   - Output projection to vocabulary
#
# This is NOT a transformer. It's intentionally
# trivial so you can focus on the training phases,
# not the architecture.

VOCAB_SIZE = 64        # tiny vocabulary
EMBED_DIM = 32         # embedding dimension
HIDDEN_DIM = 64        # hidden layer size
SEQ_LEN = 8           # sequence length for training


class TinyLM(nn.Module):
    """Minimal language model: embed -> linear -> project to vocab."""

    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(VOCAB_SIZE, EMBED_DIM)
        self.hidden = nn.Linear(EMBED_DIM, HIDDEN_DIM)
        self.head = nn.Linear(HIDDEN_DIM, VOCAB_SIZE)

    def forward(self, token_ids):
        """
        token_ids: [batch, seq_len]
        returns:   logits [batch, seq_len, vocab_size]
        """
        x = self.embed(token_ids)         # [batch, seq, embed]
        x = F.relu(self.hidden(x))        # [batch, seq, hidden]
        logits = self.head(x)             # [batch, seq, vocab]
        return logits

    def score_sequence(self, token_ids):
        """
        Returns the average log-probability of the sequence.
        Used in the DPO alignment phase to score chosen vs rejected.
        """
        logits = self.forward(token_ids)                       # [batch, seq, vocab]
        # Shift: predict token t+1 from position t
        log_probs = F.log_softmax(logits[:, :-1, :], dim=-1)  # [batch, seq-1, vocab]
        targets = token_ids[:, 1:]                             # [batch, seq-1]
        # Gather the log-prob of each actual next token
        token_log_probs = log_probs.gather(2, targets.unsqueeze(-1)).squeeze(-1)
        return token_log_probs.mean(dim=-1)                    # [batch] average log-prob


# ──────────────────────────────────────────────
# HELPER: text <-> tokens (toy tokenizer)
# ──────────────────────────────────────────────
# Real tokenizers (BPE, SentencePiece) map text to subword IDs.
# Ours just maps each character to a number mod VOCAB_SIZE.

def text_to_ids(text, length=SEQ_LEN):
    """Convert a string to a list of token IDs (fixed length)."""
    ids = [ord(c) % VOCAB_SIZE for c in text]
    # Pad or truncate to fixed length
    ids = ids[:length]
    ids += [0] * (length - len(ids))
    return ids


def ids_to_text(ids):
    """Convert token IDs back to a rough string (for display only)."""
    return "".join(chr((i % 26) + ord('a')) for i in ids if i != 0)


# ──────────────────────────────────────────────
# PHASE 1: PRE-TRAINING (Self-Supervised)
# ──────────────────────────────────────────────
# Goal:    Learn patterns from raw text.
# Data:    Unlabeled text strings.
# Loss:    Cross-entropy on next-token prediction.
# Analogy: A student reading millions of books,
#          learning grammar and facts, but not
#          how to answer questions.

def build_pretrain_dataset():
    """
    Toy 'web crawl' — raw text the model learns patterns from.
    In real training: trillions of tokens from web, code, books.
    """
    raw_texts = [
        "the cat sat on the mat and looked around",
        "customer support helps people solve problems",
        "machine learning models learn from data",
        "the weather today is sunny and warm outside",
        "python is a popular programming language",
        "neural networks have layers of parameters",
        "the quick brown fox jumps over the lazy dog",
        "training a model requires data and compute",
    ]
    # Convert to token IDs
    return [torch.tensor([text_to_ids(t)]) for t in raw_texts]


def train_pretrain(model, dataset, steps=50, lr=0.01):
    """
    Pre-training loop: next-token prediction.

    For each text sequence:
      - Input:  tokens [0, 1, 2, ..., N-1]
      - Target: tokens [1, 2, 3, ..., N]
      - Loss:   cross-entropy(predicted[t], actual[t+1])

    This is how GPT, Llama, Claude, etc. are pre-trained.
    The only difference: scale (trillions of tokens, months, 10K+ GPUs).
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    print("=" * 55)
    print("  PHASE 1: PRE-TRAINING (self-supervised)")
    print("  Objective: next-token prediction")
    print("=" * 55)

    for step in range(steps):
        sample = random.choice(dataset)         # pick a random text
        logits = model(sample)                  # [1, seq, vocab]

        # Shift: predict token t+1 from position t
        pred = logits[:, :-1, :].reshape(-1, VOCAB_SIZE)
        target = sample[:, 1:].reshape(-1)

        loss = F.cross_entropy(pred, target)

        optimizer.zero_grad()
        loss.backward()                         # compute gradients
        optimizer.step()                        # update ALL weights

        if step % 10 == 0:
            print(f"  step {step:3d}  loss={loss.item():.4f}")

    print("  Pre-training complete.\n")
    return model


# ──────────────────────────────────────────────
# PHASE 2: SFT (Supervised Fine-Tuning)
# ──────────────────────────────────────────────
# Goal:    Learn to follow instructions.
# Data:    (instruction, expected_response) pairs.
# Loss:    Cross-entropy on expected response tokens.
# Analogy: The student now gets a tutor who shows
#          "when asked X, answer Y."

def build_sft_dataset():
    """
    Toy instruction-response pairs.
    In real training: 100K–10M pairs, human + synthetic.
    """
    pairs = [
        ("greet the customer", "hello how can i help you today"),
        ("apologize for delay", "i am sorry for the delay let me help"),
        ("ask for order id", "could you please share your order id"),
        ("confirm refund", "your refund has been processed successfully"),
        ("say goodbye", "thank you for contacting us have a great day"),
    ]
    dataset = []
    for instruction, response in pairs:
        # Combine instruction + response into one sequence
        # (real SFT formats this as a chat template)
        combined = instruction + " -> " + response
        ids = torch.tensor([text_to_ids(combined, length=SEQ_LEN)])
        dataset.append(ids)
    return dataset


def train_sft(model, dataset, steps=40, lr=0.005):
    """
    SFT loop: same loss as pre-training (next-token prediction),
    but on INSTRUCTION data instead of raw text.

    Key difference from pre-training:
      - Data is curated (instruction, response) pairs
      - Model learns the FORMAT of helpful responses
      - Much smaller dataset, much fewer steps
      - Typically uses the pre-trained checkpoint as starting point
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    print("=" * 55)
    print("  PHASE 2: SFT (supervised fine-tuning)")
    print("  Objective: learn instruction-following format")
    print("=" * 55)

    for step in range(steps):
        sample = random.choice(dataset)
        logits = model(sample)

        pred = logits[:, :-1, :].reshape(-1, VOCAB_SIZE)
        target = sample[:, 1:].reshape(-1)

        loss = F.cross_entropy(pred, target)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % 10 == 0:
            print(f"  step {step:3d}  loss={loss.item():.4f}")

    print("  SFT complete.\n")
    return model


# ──────────────────────────────────────────────
# PHASE 3: ALIGNMENT (DPO-Style)
# ──────────────────────────────────────────────
# Goal:    Prefer "chosen" responses over "rejected" ones.
# Data:    (prompt, chosen, rejected) triplets.
# Loss:    DPO loss — no reward model needed.
# Analogy: The tutor now shows pairs of answers:
#          "This one is better than that one. Learn why."

def build_preference_dataset():
    """
    Toy preference triplets: (prompt, chosen, rejected).
    In real training: 500K–5M pairs from human annotators or AI judges.
    """
    triplets = [
        (
            "order is late",
            "i am sorry let me check your order now",     # chosen (polite, helpful)
            "check the tracking page yourself",            # rejected (dismissive)
        ),
        (
            "product broke",
            "i apologize we will send a replacement",      # chosen
            "that happens sometimes",                       # rejected
        ),
        (
            "want a refund",
            "let me process your refund right away",       # chosen
            "no refunds after thirty days",                # rejected
        ),
        (
            "wrong item",
            "sorry about that let me fix this for you",    # chosen
            "are you sure it is wrong",                    # rejected
        ),
    ]
    dataset = []
    for prompt, chosen, rejected in triplets:
        p_ids = torch.tensor([text_to_ids(prompt + " -> " + chosen, SEQ_LEN)])
        r_ids = torch.tensor([text_to_ids(prompt + " -> " + rejected, SEQ_LEN)])
        dataset.append((p_ids, r_ids))
    return dataset


def train_align_dpo(model, dataset, steps=30, lr=0.001, beta=0.1):
    """
    DPO alignment loop (simplified).

    How DPO works in plain English:
      1. Score how likely the model thinks the CHOSEN response is
      2. Score how likely the model thinks the REJECTED response is
      3. Also score both under a FROZEN reference model
      4. Loss pushes the model to prefer "chosen" more than the
         reference does, relative to "rejected"

    Simplified here:
      - We use a frozen copy of the model as the reference
      - The DPO loss increases chosen probability and decreases rejected

    Why no reward model:
      DPO bakes the preference signal directly into the loss function.
      This is why it's simpler and cheaper than PPO-based RLHF.
    """
    # Freeze a copy as the reference model (anchor)
    ref_model = TinyLM()
    ref_model.load_state_dict(model.state_dict())
    ref_model.eval()
    for p in ref_model.parameters():
        p.requires_grad = False

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    print("=" * 55)
    print("  PHASE 3: ALIGNMENT (DPO-style preference optimization)")
    print("  Objective: prefer chosen over rejected responses")
    print("=" * 55)

    for step in range(steps):
        chosen_ids, rejected_ids = random.choice(dataset)

        # Score sequences under the policy (model being trained)
        policy_chosen_score = model.score_sequence(chosen_ids)
        policy_rejected_score = model.score_sequence(rejected_ids)

        # Score sequences under the reference (frozen copy)
        with torch.no_grad():
            ref_chosen_score = ref_model.score_sequence(chosen_ids)
            ref_rejected_score = ref_model.score_sequence(rejected_ids)

        # DPO loss (simplified):
        #   log_ratio_chosen  = policy(chosen)  - ref(chosen)
        #   log_ratio_rejected = policy(rejected) - ref(rejected)
        #   loss = -log(sigmoid(beta * (log_ratio_chosen - log_ratio_rejected)))
        #
        # In words: "Make the policy prefer chosen over rejected
        #            MORE than the reference model does."

        chosen_diff = policy_chosen_score - ref_chosen_score
        rejected_diff = policy_rejected_score - ref_rejected_score
        logits_diff = beta * (chosen_diff - rejected_diff)
        loss = -F.logsigmoid(logits_diff).mean()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % 10 == 0:
            print(f"  step {step:3d}  loss={loss.item():.4f}"
                  f"  chosen_adv={chosen_diff.item():.3f}"
                  f"  rejected_adv={rejected_diff.item():.3f}")

    print("  Alignment complete.\n")
    return model


# ──────────────────────────────────────────────
# EVALUATION: Show behavior across phases
# ──────────────────────────────────────────────

def evaluate_model(model, label, prompts):
    """
    Show the model's 'response' to each prompt.
    Uses argmax over logits (greedy decoding) — not real generation,
    but enough to see how the model's behavior shifts across phases.
    """
    print(f"  --- Eval: {label} ---")
    model.eval()
    with torch.no_grad():
        for prompt_text in prompts:
            ids = torch.tensor([text_to_ids(prompt_text, SEQ_LEN)])
            logits = model(ids)
            # Take argmax of last few positions as "response"
            predicted_ids = logits[0, -4:, :].argmax(dim=-1).tolist()
            response = ids_to_text(predicted_ids)
            print(f"  prompt: '{prompt_text[:30]:<30s}'  -> output tokens: {predicted_ids}  ('{response}')")
    model.train()
    print()


# ──────────────────────────────────────────────
# CHECKPOINT SAVING (Simulated)
# ──────────────────────────────────────────────

def save_checkpoint(model, phase_name, output_dir="./toy_checkpoints"):
    """
    Save model state dict to disk.
    In real training: checkpoints are 100s of GB, saved to parallel
    file systems (Lustre/WEKA), then replicated to S3/GCS.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = os.path.join(output_dir, f"{phase_name}.pt")
    torch.save(model.state_dict(), path)
    size = os.path.getsize(path)
    print(f"  Saved {phase_name} checkpoint: {path} ({size:,} bytes)")


def load_checkpoint(model, phase_name, output_dir="./toy_checkpoints"):
    """Load a previously saved checkpoint."""
    path = os.path.join(output_dir, f"{phase_name}.pt")
    model.load_state_dict(torch.load(path, weights_only=True))
    print(f"  Loaded checkpoint: {path}")
    return model


# ──────────────────────────────────────────────
# MAIN: Run all three phases
# ──────────────────────────────────────────────

def main():
    print("\n" + "=" * 55)
    print("  THREE-PHASE TRAINING TOY EXAMPLE")
    print("  Pre-train -> SFT -> Align (DPO)")
    print("=" * 55 + "\n")

    # Evaluation prompts — same across all phases to show progression
    eval_prompts = [
        "order is late",
        "greet the customer",
        "product broke",
    ]

    # ── Phase 1: Pre-training ────────────────
    model = TinyLM()
    pretrain_data = build_pretrain_dataset()
    model = train_pretrain(model, pretrain_data, steps=50)
    save_checkpoint(model, "pretrained")
    evaluate_model(model, "After Pre-training", eval_prompts)

    # ── Phase 2: SFT ─────────────────────────
    # Start from the pre-trained checkpoint (not from scratch!)
    model = load_checkpoint(model, "pretrained")
    sft_data = build_sft_dataset()
    model = train_sft(model, sft_data, steps=40)
    save_checkpoint(model, "sft")
    evaluate_model(model, "After SFT", eval_prompts)

    # ── Phase 3: Alignment (DPO) ─────────────
    # Start from the SFT checkpoint (not from scratch!)
    model = load_checkpoint(model, "sft")
    pref_data = build_preference_dataset()
    model = train_align_dpo(model, pref_data, steps=30)
    save_checkpoint(model, "aligned")
    evaluate_model(model, "After Alignment (DPO)", eval_prompts)

    # ── Summary ──────────────────────────────
    print("=" * 55)
    print("  PIPELINE COMPLETE")
    print()
    print("  Phase 1 (Pre-train):  Raw text -> next-token prediction")
    print("  Phase 2 (SFT):        Instruction pairs -> format learning")
    print("  Phase 3 (Alignment):  Preference pairs -> DPO optimization")
    print()
    print("  Checkpoints saved in: ./toy_checkpoints/")
    print("    pretrained.pt  -> base model")
    print("    sft.pt         -> instruction-following model")
    print("    aligned.pt     -> preference-aligned model")
    print("=" * 55)


if __name__ == "__main__":
    main()


# ──────────────────────────────────────────────
# HOW TO RUN
# ──────────────────────────────────────────────
#
# Prerequisites:
#   pip install torch
#
# Run:
#   python three_phase_training_toy.py
#
# What to observe:
#   - Loss decreases in each phase
#   - Output tokens shift across phases (different objectives)
#   - Checkpoints are saved after each phase
#   - Phase 2 starts from phase 1 checkpoint (not random)
#   - Phase 3 starts from phase 2 checkpoint (not random)
#
# This is a toy — in real training:
#   - Model is a transformer with billions of parameters
#   - Pre-training takes months on 10K+ GPUs
#   - SFT uses 100K–10M curated examples
#   - DPO uses 500K–5M preference pairs
#   - Checkpoints are hundreds of GB, saved to parallel file systems

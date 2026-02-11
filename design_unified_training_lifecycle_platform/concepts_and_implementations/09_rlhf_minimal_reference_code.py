"""
Minimal RLHF Reference Code
============================

Goal: Show the core DPO + PPO flows at a code level.
This is interview/learning code — heavily commented,
minimal dependencies, toy data.

Sections:
  Part 1: Create toy preference dataset
  Part 2: DPO training outline (practical, near-runnable)
  Part 3: PPO training outline (high-level pseudocode)
"""

# ──────────────────────────────────────────────
# PART 1: Toy Preference Dataset
# ──────────────────────────────────────────────

# This is what preference data looks like in practice.
# Each example: (prompt, chosen_response, rejected_response)

PREFERENCE_DATA = [
    {
        "prompt": "Customer: My order hasn't arrived.\nAgent:",
        "chosen": (
            " I'm so sorry about the delay! Let me look up your order "
            "right now and get you an update within the hour."
        ),
        "rejected": (
            " Check the tracking page on our website."
        ),
    },
    {
        "prompt": "Customer: I want a refund.\nAgent:",
        "chosen": (
            " I completely understand. Let me start the refund process "
            "for you — it should arrive in 3–5 business days."
        ),
        "rejected": (
            " Refunds take 7–14 days. Please wait."
        ),
    },
    {
        "prompt": "Customer: Your product broke after one day.\nAgent:",
        "chosen": (
            " That's not the experience we want you to have! I'll send a "
            "replacement today and include a prepaid return label."
        ),
        "rejected": (
            " Did you follow the instructions? Products usually don't break."
        ),
    },
    {
        "prompt": "Customer: How do I change my shipping address?\nAgent:",
        "chosen": (
            " Great question! You can update it in account settings, or I "
            "can change it for you right now — which do you prefer?"
        ),
        "rejected": (
            " Go to settings and change it yourself."
        ),
    },
    {
        "prompt": "Customer: I was charged twice.\nAgent:",
        "chosen": (
            " I'm sorry about that! I can see the duplicate charge and I'll "
            "reverse it immediately. You'll see the credit within 24 hours."
        ),
        "rejected": (
            " Contact your bank about the duplicate charge."
        ),
    },
]


def prepare_preference_dataset(raw_data):
    """
    Convert raw preference data into the format DPO/PPO expects.
    In production you'd use HuggingFace datasets.Dataset.
    """
    formatted = []
    for example in raw_data:
        formatted.append({
            "prompt": example["prompt"],
            "chosen": example["prompt"] + example["chosen"],     # full text
            "rejected": example["prompt"] + example["rejected"], # full text
        })
    return formatted


dataset = prepare_preference_dataset(PREFERENCE_DATA)
# Split: in production, split by prompt to prevent leakage
train_data = dataset[:4]
eval_data = dataset[4:]


# ──────────────────────────────────────────────
# PART 2: DPO Training Outline
# ──────────────────────────────────────────────
#
# This is near-runnable with the `trl` library.
# TRL (Transformer Reinforcement Learning) is HuggingFace's
# library for RLHF — it provides DPOTrainer and PPOTrainer.

from transformers import AutoModelForCausalLM, AutoTokenizer

# -- In production, you'd use a real model like "meta-llama/Llama-3-8B"
# -- Here we use a tiny model for demonstration
MODEL_NAME = "facebook/opt-350m"


def dpo_training_outline():
    """
    DPO training using HuggingFace TRL library.
    This is the practical approach most teams use.
    """
    from trl import DPOConfig, DPOTrainer
    from datasets import Dataset

    # 1. Load the model we want to align (the "policy")
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token

    # 2. DPO also needs a reference model (frozen copy)
    #    DPOTrainer creates this automatically if not provided.
    #    Internally: ref_model = copy.deepcopy(model).eval()

    # 3. Prepare dataset in DPO format
    #    Each row needs: "prompt", "chosen", "rejected"
    train_dataset = Dataset.from_list([
        {
            "prompt": ex["prompt"],
            "chosen": ex["chosen"],
            "rejected": ex["rejected"],
        }
        for ex in PREFERENCE_DATA[:4]
    ])

    # 4. Configure DPO training
    training_args = DPOConfig(
        output_dir="./dpo_output",
        num_train_epochs=3,
        per_device_train_batch_size=2,
        learning_rate=5e-7,        # DPO uses lower LR than SFT
        beta=0.1,                  # KL constraint strength
                                   #   higher = more conservative
                                   #   lower = allow more change
        logging_steps=1,
        report_to="none",
    )

    # 5. Create DPO trainer and train
    #    Under the hood, for each batch:
    #      - Compute log_probs of chosen & rejected from policy
    #      - Compute log_probs of chosen & rejected from reference
    #      - DPO loss: push policy to widen the gap
    #        between chosen and rejected (relative to reference)
    trainer = DPOTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        processing_class=tokenizer,
    )

    trainer.train()

    # 6. Save the aligned model
    trainer.save_model("./dpo_aligned_model")

    return model


# ──────────────────────────────────────────────
# PART 3: PPO Training Outline (Pseudocode)
# ──────────────────────────────────────────────
#
# PPO is more complex. This is high-level pseudocode
# showing where each component fits.
#
# In practice, use trl.PPOTrainer.

def ppo_training_outline_pseudocode():
    """
    PPO training flow — pseudocode for understanding.
    Shows the key components and where they connect.
    """

    # ── Step 0: Train Reward Model (separate step, done once) ──
    #
    # reward_model = train_reward_model(preference_data)
    #
    # The RM takes (prompt, response) and outputs a scalar score.
    # Training loss:
    #   For each (prompt, chosen, rejected):
    #     score_chosen  = RM(prompt + chosen)
    #     score_rejected = RM(prompt + rejected)
    #     loss = -log(sigmoid(score_chosen - score_rejected))
    #
    # After training: RM(prompt, good_reply) > RM(prompt, bad_reply)

    # ── Step 1: Set up the 4 models ──
    #
    # policy_model     = load_model(sft_checkpoint)    # trainable
    # reference_model  = load_model(sft_checkpoint)    # frozen
    # reward_model     = load_model(rm_checkpoint)     # frozen
    # value_model      = load_model(sft_checkpoint)    # trainable
    #
    # Total GPU memory: ~4x model size
    # For 7B: ~56 GB minimum

    # ── Step 2: PPO training loop ──
    #
    # for batch in prompt_dataloader:
    #
    #     # 2a. Generate responses from the policy
    #     responses = policy_model.generate(batch["prompts"])
    #
    #     # 2b. Score responses with the reward model
    #     rewards = reward_model.score(batch["prompts"], responses)
    #
    #     # 2c. Compute KL penalty (keep policy near reference)
    #     policy_logprobs = policy_model.log_prob(responses)
    #     ref_logprobs = reference_model.log_prob(responses)
    #     kl_penalty = policy_logprobs - ref_logprobs
    #
    #     # 2d. Adjusted reward = reward - beta * kl_penalty
    #     adjusted_rewards = rewards - beta * kl_penalty
    #
    #     # 2e. Compute advantages using value model
    #     values = value_model(batch["prompts"], responses)
    #     advantages = adjusted_rewards - values  # "better or worse than expected?"
    #
    #     # 2f. PPO policy update
    #     #   Increase probability of high-advantage tokens
    #     #   BUT clip the update (don't change too much at once)
    #     #
    #     #   ratio = policy_prob / old_policy_prob
    #     #   clipped_ratio = clip(ratio, 1-epsilon, 1+epsilon)
    #     #   loss = -min(ratio * advantage, clipped_ratio * advantage)
    #     policy_loss = ppo_loss(policy_model, advantages)
    #     policy_model.update(policy_loss)
    #
    #     # 2g. Update value model
    #     value_loss = mse(values, adjusted_rewards)
    #     value_model.update(value_loss)
    #
    # ── Step 3: Save aligned model ──
    # policy_model.save("ppo_aligned_model")

    pass


# ──────────────────────────────────────────────
# PART 4: Quick comparison
# ──────────────────────────────────────────────

COMPARISON = """
╔══════════════════╦═══════════════════════╦════════════════════════╗
║                  ║       DPO             ║       PPO              ║
╠══════════════════╬═══════════════════════╬════════════════════════╣
║ Models in memory ║ 2 (policy + ref)      ║ 4 (policy + ref +     ║
║                  ║                       ║   RM + value)          ║
╠══════════════════╬═══════════════════════╬════════════════════════╣
║ Training input   ║ Preference pairs      ║ Prompts (RM trained   ║
║                  ║ directly              ║ separately on prefs)   ║
╠══════════════════╬═══════════════════════╬════════════════════════╣
║ Key hyperparam   ║ beta (KL strength)    ║ beta, epsilon (clip),  ║
║                  ║                       ║ RM quality matters     ║
╠══════════════════╬═══════════════════════╬════════════════════════╣
║ Library          ║ trl.DPOTrainer        ║ trl.PPOTrainer         ║
╠══════════════════╬═══════════════════════╬════════════════════════╣
║ Start here?      ║ YES (simpler)         ║ Only if needed         ║
╚══════════════════╩═══════════════════════╩════════════════════════╝
"""


if __name__ == "__main__":
    print("=" * 60)
    print("RLHF Reference Code — Interview Learning Aid")
    print("=" * 60)
    print()
    print("Preference dataset examples:")
    for i, ex in enumerate(PREFERENCE_DATA[:2]):
        print(f"\n  Example {i+1}:")
        print(f"    Prompt:   {ex['prompt']}")
        print(f"    Chosen:   {ex['chosen'][:60]}...")
        print(f"    Rejected: {ex['rejected'][:60]}...")
    print()
    print(COMPARISON)
    print()
    print("To run DPO training: call dpo_training_outline()")
    print("PPO is pseudocode only — see ppo_training_outline_pseudocode()")

"""
Minimal PEFT LoRA Fine-Tuning Example
======================================

Goal: Fine-tune a small LLM to write polite customer support replies.

What this script demonstrates (in order):
  1. Load a base model
  2. Apply LoRA config
  3. Train on a tiny toy dataset
  4. Save the adapter
  5. Load base + adapter separately
  6. Merge adapter into base and save

This is interview/learning reference code.
Uses HuggingFace transformers + peft libraries.
"""

from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, PeftModel, TaskType


# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

# Use a small model for demonstration.
# In production you'd use "meta-llama/Llama-3-8B" etc.
BASE_MODEL = "facebook/opt-350m"

LORA_RANK = 8           # Low-rank dimension (small = fewer params)
LORA_ALPHA = 16         # Scaling factor (alpha / rank = scaling)
LORA_DROPOUT = 0.05     # Regularization
TARGET_MODULES = [       # Which layers get LoRA adapters
    "q_proj",            #   query projection in attention
    "v_proj",            #   value projection in attention
]


# ──────────────────────────────────────────────
# STEP 1: Load base model + tokenizer
# ──────────────────────────────────────────────

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.pad_token = tokenizer.eos_token  # needed for some models

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    # For QLoRA you'd add: load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16
)


# ──────────────────────────────────────────────
# STEP 2: Apply LoRA config
# ──────────────────────────────────────────────
# This wraps the base model — freezes original weights,
# injects trainable LoRA matrices into target modules.

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,     # we're fine-tuning a causal language model
    r=LORA_RANK,                       # rank — controls adapter size
    lora_alpha=LORA_ALPHA,             # scaling factor
    lora_dropout=LORA_DROPOUT,
    target_modules=TARGET_MODULES,     # which layers get adapters
)

model = get_peft_model(base_model, lora_config)

# Show how few parameters we're actually training:
model.print_trainable_parameters()
# Output example: "trainable params: 294,912 || all params: 331,489,280 || trainable%: 0.089"


# ──────────────────────────────────────────────
# STEP 3: Prepare tiny toy dataset
# ──────────────────────────────────────────────
# In production: thousands of examples from your support tickets.
# Here: just a few to show the pattern.

raw_data = [
    {
        "text": (
            "Customer: My order hasn't arrived yet.\n"
            "Agent: I'm sorry to hear about the delay! Let me check your "
            "order status right away and get back to you within the hour."
        )
    },
    {
        "text": (
            "Customer: I want a refund.\n"
            "Agent: I completely understand your frustration. Let me start "
            "the refund process for you — you should see it in 3–5 business days."
        )
    },
    {
        "text": (
            "Customer: Your product broke after one day.\n"
            "Agent: I'm really sorry about that! We'll send a replacement "
            "right away, and I'll include a prepaid return label for the "
            "defective item."
        )
    },
    {
        "text": (
            "Customer: How do I change my shipping address?\n"
            "Agent: Great question! You can update your shipping address in "
            "your account settings, or I can change it for you right now. "
            "Which would you prefer?"
        )
    },
]

dataset = Dataset.from_list(raw_data)


# Tokenize
def tokenize(example):
    tokens = tokenizer(
        example["text"],
        truncation=True,
        max_length=128,
        padding="max_length",
    )
    tokens["labels"] = tokens["input_ids"].copy()  # causal LM: labels = input
    return tokens


tokenized_dataset = dataset.map(tokenize, remove_columns=["text"])


# ──────────────────────────────────────────────
# STEP 4: Train
# ──────────────────────────────────────────────

training_args = TrainingArguments(
    output_dir="./lora_output",
    num_train_epochs=3,               # few epochs for demo
    per_device_train_batch_size=2,
    learning_rate=2e-4,               # typical LoRA learning rate
    logging_steps=1,
    save_strategy="epoch",
    report_to="none",                 # disable wandb etc for demo
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

trainer.train()


# ──────────────────────────────────────────────
# STEP 5: Save adapter weights (NOT the full model)
# ──────────────────────────────────────────────
# This saves only the LoRA matrices — typically ~10–50 MB.
# The base model is NOT included.

ADAPTER_PATH = "./lora_adapter"
model.save_pretrained(ADAPTER_PATH)

print(f"Adapter saved to {ADAPTER_PATH}")
# Files created:
#   adapter_config.json   — LoRA hyperparameters
#   adapter_model.bin     — the tiny trained weights


# ──────────────────────────────────────────────
# STEP 6: Load base + adapter from scratch
# ──────────────────────────────────────────────
# This is what you'd do at inference time (without merging).

# Load fresh base
fresh_base = AutoModelForCausalLM.from_pretrained(BASE_MODEL)

# Attach adapter
model_with_adapter = PeftModel.from_pretrained(fresh_base, ADAPTER_PATH)

# Now model_with_adapter runs: output = W·x + (A·B)·x
# Slightly slower than base alone, but adapter is swappable.


# ──────────────────────────────────────────────
# STEP 7: Merge adapter into base & save
# ──────────────────────────────────────────────
# merge_and_unload() does:  W_new = W_base + (A @ B) * scale
# Result: a standard model with no adapter hooks.

merged_model = model_with_adapter.merge_and_unload()

MERGED_PATH = "./merged_model"
merged_model.save_pretrained(MERGED_PATH)
tokenizer.save_pretrained(MERGED_PATH)

print(f"Merged model saved to {MERGED_PATH}")
# This is now a normal model — same size as original,
# but with fine-tuning baked in. No adapter needed at inference.


# ──────────────────────────────────────────────
# STEP 8: Quick inference test
# ──────────────────────────────────────────────

prompt = "Customer: I received the wrong item.\nAgent:"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = merged_model.generate(**inputs, max_new_tokens=60)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

# LLM Fundamentals

## What This Covers

How large language models work end-to-end, from tokenization through generation.


## Key Concepts

- Transformer architecture: attention, positional encoding, feed-forward layers
- Tokenization schemes (BPE, SentencePiece) and their downstream effects
- Decoding strategies: greedy, beam search, top-k, top-p, temperature


## Core Components

- Self-attention mechanism and KV cache
- Pre-training vs fine-tuning vs in-context learning
- Prompt structure and its effect on output quality
- Context window limits and how they constrain design
- Embedding representations and similarity search


## Key Trade-offs

- Larger context window vs quadratic attention cost
- Fine-tuning for quality vs prompt engineering for flexibility
- Open-weight models (cost, control) vs API models (convenience, capability)


## Must Explain in Interview

- Why autoregressive generation is sequential and what that means for latency
- How KV cache works and why it matters for throughput
- What temperature actually controls in the softmax distribution
- Why tokenization choices affect multilingual performance
- The difference between pre-training, fine-tuning, and RLHF

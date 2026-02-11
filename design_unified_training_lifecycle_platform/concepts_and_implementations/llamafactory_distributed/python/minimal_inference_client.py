"""
Minimal Inference Client
========================

Hits a LlamaFactory/vLLM OpenAI-compatible endpoint.
Shows both non-streaming and streaming modes.

Usage:
  python minimal_inference_client.py

Prerequisites:
  - Inference server running (see scripts/inference_single_node.sh)
  - pip install requests
"""

import json
import requests


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

BASE_URL = "http://localhost:8000"       # or load balancer URL
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"


# ──────────────────────────────────────────────
# Non-streaming request (simple)
# ──────────────────────────────────────────────

def chat_completion(prompt: str, max_tokens: int = 200) -> str:
    """
    Send a chat completion request and get the full response.
    This waits for the entire response before returning.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful customer support agent."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


# ──────────────────────────────────────────────
# Streaming request (token by token)
# ──────────────────────────────────────────────

def chat_completion_stream(prompt: str, max_tokens: int = 200):
    """
    Send a streaming chat completion request.
    Tokens arrive one at a time — good for real-time UIs.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful customer support agent."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True,             # enable streaming
    }

    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload,
        stream=True,                # stream the HTTP response
        timeout=60,
    )
    response.raise_for_status()

    # Parse Server-Sent Events (SSE)
    full_response = ""
    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode("utf-8")

        # SSE lines start with "data: "
        if not line.startswith("data: "):
            continue

        data_str = line[len("data: "):]

        # Stream ends with [DONE]
        if data_str.strip() == "[DONE]":
            break

        chunk = json.loads(data_str)
        delta = chunk["choices"][0].get("delta", {})
        token = delta.get("content", "")

        if token:
            print(token, end="", flush=True)   # print token as it arrives
            full_response += token

    print()  # newline after streaming finishes
    return full_response


# ──────────────────────────────────────────────
# Example usage
# ──────────────────────────────────────────────

if __name__ == "__main__":
    prompt = "My order arrived damaged. What should I do?"

    print("=" * 60)
    print("  Non-streaming request")
    print("=" * 60)
    try:
        result = chat_completion(prompt)
        print(f"\n  Response:\n  {result}\n")
    except requests.ConnectionError:
        print("\n  ERROR: Could not connect to inference server.")
        print("  Start the server first: bash scripts/inference_single_node.sh\n")
    except Exception as e:
        print(f"\n  ERROR: {e}\n")

    print("=" * 60)
    print("  Streaming request")
    print("=" * 60)
    try:
        print()
        chat_completion_stream(prompt)
    except requests.ConnectionError:
        print("\n  ERROR: Could not connect to inference server.\n")
    except Exception as e:
        print(f"\n  ERROR: {e}\n")

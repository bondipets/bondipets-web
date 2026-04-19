#!/usr/bin/env python3
"""Verify FAL_KEY loads correctly and authenticates against fal.ai.

Uses a minimal flux-schnell generation (square, 1 step, 1 image) as an
auth probe. Cost per run is a fraction of a cent. Never prints the key value.
"""
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.is_file():
    sys.exit(f"ERROR: {env_path} does not exist")
load_dotenv(env_path)

key = os.environ.get("FAL_KEY", "")
if not key:
    sys.exit("ERROR: FAL_KEY not set after load_dotenv")
print(f"OK: FAL_KEY loaded (length={len(key)})")


def redact(text: str) -> str:
    """Strip the API key from any string (defensive — error paths may echo URL/headers)."""
    return str(text).replace(key, "<REDACTED>") if key else str(text)


import fal_client  # noqa: E402

print("Calling fal-ai/flux/schnell with minimal payload (auth probe)...")
t0 = time.time()
try:
    result = fal_client.subscribe(
        "fal-ai/flux/schnell",
        arguments={
            "prompt": "x",
            "image_size": "square",
            "num_images": 1,
            "num_inference_steps": 1,
        },
    )
except Exception as e:
    sys.exit("ERROR: Fal call failed: " + redact(e))

elapsed = time.time() - t0
if not isinstance(result, dict):
    sys.exit(f"ERROR: unexpected response type {type(result).__name__}")

images = result.get("images", [])
img_url = images[0].get("url", "") if images else ""
seed = result.get("seed", "(no seed)")
print(f"OK: Fal auth VALID. Response in {elapsed:.1f}s.")
print(f"    Image URL (first 60 chars): {img_url[:60]}...")
print(f"    Seed: {seed}")
print("Note: flux-schnell @ square / 1 step ≈ $0.003. Actual billed amount appears on dashboard.")

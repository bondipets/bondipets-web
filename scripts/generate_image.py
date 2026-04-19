#!/usr/bin/env python3
"""Generate images via fal.ai (Nano Banana 2 / Nano Banana Pro).

Auth: reads FAL_KEY from /.env (via python-dotenv).
Pricing base (per image @ 1K, April 2026):
  - nano-banana-2:   $0.08
  - nano-banana-pro: $0.15
Resolution multipliers: 0.5K=0.75x, 1K=1.0x, 2K=1.5x, 4K=2.0x

Usage:
    python3 scripts/generate_image.py \\
        --prompt "a photo of a dog" \\
        --output frame.png \\
        --model nano-banana-2 \\
        --aspect-ratio 1:1 \\
        --resolution 1K
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

MODEL_ENDPOINTS = {
    "nano-banana-2": "fal-ai/nano-banana-2",
    "nano-banana-pro": "fal-ai/nano-banana-pro",
    "nano-banana-2/edit": "fal-ai/nano-banana-2/edit",
    "nano-banana-pro/edit": "fal-ai/nano-banana-pro/edit",
}
MODEL_BASE_COST = {
    "nano-banana-2": 0.08,
    "nano-banana-pro": 0.15,
    "nano-banana-2/edit": 0.08,
    "nano-banana-pro/edit": 0.15,
}
RESOLUTION_MULTIPLIER = {
    "0.5K": 0.75,
    "1K": 1.00,
    "2K": 1.50,
    "4K": 2.00,
}
ASPECT_RATIOS = [
    "auto", "21:9", "16:9", "3:2", "4:3", "5:4",
    "1:1", "4:5", "3:4", "2:3", "9:16",
]
RESOLUTIONS = list(RESOLUTION_MULTIPLIER.keys())
BACKOFFS_SEC = (10, 30, 60)


def load_api_key() -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)
    key = os.environ.get("FAL_KEY", "")
    if not key:
        sys.exit("ERROR: FAL_KEY not found (expected in .env)")
    return key


def redact(s: str, secret: str) -> str:
    return str(s).replace(secret, "<REDACTED>") if secret else str(s)


def is_retriable(err_msg: str) -> bool:
    up = err_msg.upper()
    return any(s in up for s in (
        "503", "UNAVAILABLE", "OVERLOADED",
        "429", "RATE LIMIT", "RATE_LIMIT",
        "TIMEOUT", "TEMPORARILY",
    ))


def upload_references(paths):
    """Upload local files to fal CDN and return hosted URLs."""
    import fal_client
    urls = []
    for p in paths:
        pp = Path(p)
        if not pp.is_file():
            sys.exit(f"ERROR: reference image not found: {pp}")
        urls.append(fal_client.upload_file(str(pp)))
    return urls


def call_fal(endpoint: str, prompt: str, aspect_ratio: str,
             resolution: str, num_images: int, image_urls=None):
    import fal_client
    arguments = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    }
    if image_urls:
        # Edit mode: image_urls list is required, num_images is not in the
        # edit schema so we omit it (API default = 1).
        arguments["image_urls"] = image_urls
    else:
        arguments["num_images"] = num_images
    return fal_client.subscribe(endpoint, arguments=arguments, with_logs=True)


def download(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as resp:
        data = resp.read()
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def main():
    ap = argparse.ArgumentParser(description="Generate images via fal.ai Nano Banana models")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="nano-banana-2",
                    choices=list(MODEL_ENDPOINTS.keys()))
    ap.add_argument("--aspect-ratio", default="1:1", choices=ASPECT_RATIOS)
    ap.add_argument("--resolution", default="1K", choices=RESOLUTIONS)
    ap.add_argument("--num-images", type=int, default=1,
                    help="How many images to generate per call (1-4, text-to-image only)")
    ap.add_argument("--reference-image", action="append", default=[],
                    metavar="PATH",
                    help="Local image path to use as reference (required for /edit "
                         "models; can be repeated up to 14 times)")
    default_output = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    ap.add_argument("--output", default=default_output,
                    help="Output PNG path (timestamp-based by default)")
    args = ap.parse_args()

    is_edit = args.model.endswith("/edit")
    if is_edit and not args.reference_image:
        sys.exit(f"ERROR: --reference-image is required when using {args.model}")
    if not is_edit and args.reference_image:
        print(f"WARN: --reference-image ignored for non-edit model {args.model}")

    api_key = load_api_key()
    os.environ["FAL_KEY"] = api_key  # make sure fal_client sees it

    endpoint = MODEL_ENDPOINTS[args.model]
    base = MODEL_BASE_COST[args.model]
    mult = RESOLUTION_MULTIPLIER[args.resolution]
    est_cost = base * mult * args.num_images

    print(f"Model:    {args.model}  ({endpoint})")
    print(f"Request:  aspect={args.aspect_ratio}, res={args.resolution}, n={args.num_images}, prompt_len={len(args.prompt)}")
    if is_edit:
        print(f"Refs:     {len(args.reference_image)} local image(s) to upload")
    print(f"Est cost: ${est_cost:.4f}")
    print()

    image_urls = None
    if is_edit:
        print("  [upload] uploading reference image(s) to fal CDN...", flush=True)
        image_urls = upload_references(args.reference_image)
        print(f"  [upload] done ({len(image_urls)} URL(s) returned)", flush=True)

    t0 = time.time()
    retries = 0
    last_err = None
    result = None

    for attempt in range(1 + len(BACKOFFS_SEC)):
        if attempt > 0:
            delay = BACKOFFS_SEC[attempt - 1]
            print(f"  [backoff] {delay}s before retry {attempt}/{len(BACKOFFS_SEC)}...", flush=True)
            time.sleep(delay)
        try:
            print(f"  [attempt {attempt + 1}] fal_client.subscribe({endpoint})...", flush=True)
            result = call_fal(
                endpoint,
                args.prompt,
                args.aspect_ratio,
                args.resolution,
                args.num_images,
                image_urls=image_urls,
            )
            break
        except Exception as e:
            msg = redact(str(e), api_key)
            last_err = msg
            if is_retriable(msg):
                retries += 1
                print(f"  [retriable] {msg[:300]}", flush=True)
                continue
            sys.exit(f"ERROR (non-retriable): {msg}")
    else:
        sys.exit(f"ERROR: retriable error persistent after {retries} retries. Last: {last_err}")

    if not isinstance(result, dict):
        sys.exit(f"ERROR: unexpected result type {type(result).__name__}")
    images = result.get("images", [])
    if not images:
        sys.exit(f"ERROR: no 'images' in response: {redact(json.dumps(result)[:500], api_key)}")

    output_path = Path(args.output)
    saved = []
    for i, img in enumerate(images):
        url = img.get("url")
        if not url:
            continue
        if len(images) > 1:
            dest = output_path.with_name(
                f"{output_path.stem}_{i+1}{output_path.suffix or '.png'}"
            )
        else:
            dest = output_path
        size = download(url, dest)
        saved.append((dest, size))

    elapsed = time.time() - t0

    print()
    print("=" * 60)
    for dest, size in saved:
        real_res = "(PIL unavailable)"
        try:
            from PIL import Image
            with Image.open(dest) as im:
                real_res = f"{im.size[0]}x{im.size[1]}"
        except Exception as e:
            real_res = f"(unreadable: {e})"
        print(f"OK: {dest}")
        print(f"    size: {size / 1024:.1f} KB ({size:,} bytes)")
        print(f"    resolution: {real_res}")
    print(f"Total time: {elapsed:.1f}s")
    print(f"Retries:    {retries}")
    print(f"Est cost:   ${est_cost:.4f}")


if __name__ == "__main__":
    main()

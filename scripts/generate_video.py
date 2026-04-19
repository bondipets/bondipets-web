#!/usr/bin/env python3
"""Generate videos via fal.ai Seedance 2.0 image-to-video (fast or pro tier).

Hardcoded override: generate_audio defaults to False to fit the Bondi Pets
pipeline where audio is added in post (CapCut). The Fal API itself defaults
to True, so we always explicitly send False unless overridden via CLI.

Usage:
    python3 scripts/generate_video.py \\
        --image ./tests/start.png \\
        --prompt "the chew rotates..." \\
        --output ./tests/out.mp4 \\
        --duration 5 \\
        --resolution 720p \\
        --aspect-ratio 1:1 \\
        --tier fast
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

TIER_ENDPOINTS = {
    # Partner models (bytedance) live directly under their org namespace on Fal;
    # no `fal-ai/` prefix (that prefix is only for fal-authored models).
    "fast": "bytedance/seedance-2.0/fast/image-to-video",
    "pro":  "bytedance/seedance-2.0/image-to-video",
}
# Published pricing at 720p (April 2026). 480p pricing not officially disclosed.
TIER_PRICE_PER_SEC_720P = {"fast": 0.2419, "pro": 0.3024}

ASPECT_RATIOS = ["auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]
RESOLUTIONS = ["480p", "720p"]
DURATIONS = ["auto"] + [str(n) for n in range(4, 16)]  # "auto", "4" .. "15"
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


def upload_image(path: str) -> str:
    import fal_client
    pp = Path(path)
    if not pp.is_file():
        sys.exit(f"ERROR: image not found: {pp}")
    return fal_client.upload_file(str(pp))


def call_fal(endpoint: str, arguments: dict):
    import fal_client
    return fal_client.subscribe(endpoint, arguments=arguments, with_logs=True)


def download(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as resp:
        data = resp.read()
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def main():
    ap = argparse.ArgumentParser(
        description="Generate video via fal.ai Seedance 2.0 image-to-video"
    )
    ap.add_argument("--image", required=True, help="Local path to start frame image")
    ap.add_argument("--end-image", default=None,
                    help="Optional local path to end frame image")
    ap.add_argument("--prompt", required=True)
    default_output = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    ap.add_argument("--output", default=default_output)
    ap.add_argument("--duration", default="5", choices=DURATIONS,
                    help="Seconds as string per API schema ('auto' or '4'..'15')")
    ap.add_argument("--resolution", default="720p", choices=RESOLUTIONS)
    ap.add_argument("--aspect-ratio", default="1:1", choices=ASPECT_RATIOS)
    ap.add_argument("--tier", default="fast", choices=list(TIER_ENDPOINTS.keys()))
    ap.add_argument("--generate-audio", default="false", choices=["true", "false"],
                    help="Default false (override Fal default of true; Bondi adds audio in post)")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    api_key = load_api_key()
    os.environ["FAL_KEY"] = api_key

    endpoint = TIER_ENDPOINTS[args.tier]
    # Cost estimate (720p only has an official rate; others are best-effort)
    if args.resolution == "720p":
        price_per_sec = TIER_PRICE_PER_SEC_720P[args.tier]
    else:
        price_per_sec = TIER_PRICE_PER_SEC_720P[args.tier]  # conservative fallback
    seconds_est = 10 if args.duration == "auto" else int(args.duration)
    est_cost = seconds_est * price_per_sec

    print(f"Tier:       {args.tier}  ({endpoint})")
    print(f"Resolution: {args.resolution}")
    print(f"Duration:   {args.duration}" + (" (auto ≈ 10s)" if args.duration == "auto" else "s"))
    print(f"Aspect:     {args.aspect_ratio}")
    print(f"Audio:      {args.generate_audio}")
    print(f"Est cost:   ${est_cost:.4f}")
    print()

    print("  [upload] uploading start frame...", flush=True)
    image_url = upload_image(args.image)
    print("  [upload] start frame URL acquired", flush=True)

    end_image_url = None
    if args.end_image:
        print("  [upload] uploading end frame...", flush=True)
        end_image_url = upload_image(args.end_image)
        print("  [upload] end frame URL acquired", flush=True)

    arguments = {
        "prompt": args.prompt,
        "image_url": image_url,
        "resolution": args.resolution,
        "duration": args.duration,  # NOTE: STRING per schema
        "aspect_ratio": args.aspect_ratio,
        "generate_audio": args.generate_audio == "true",
    }
    if end_image_url:
        arguments["end_image_url"] = end_image_url
    if args.seed is not None:
        arguments["seed"] = args.seed

    t0 = time.time()
    retries = 0
    last_err = None
    result = None

    for attempt in range(1 + len(BACKOFFS_SEC)):
        if attempt > 0:
            delay = BACKOFFS_SEC[attempt - 1]
            print(f"  [backoff] {delay}s before retry {attempt}/{len(BACKOFFS_SEC)}...",
                  flush=True)
            time.sleep(delay)
        try:
            print(f"  [attempt {attempt + 1}] fal_client.subscribe({endpoint})...",
                  flush=True)
            result = call_fal(endpoint, arguments)
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
        sys.exit(f"ERROR: retriable persistent after {retries} retries. Last: {last_err}")

    if not isinstance(result, dict):
        sys.exit(f"ERROR: unexpected result type {type(result).__name__}")
    video = result.get("video")
    video_url = video.get("url") if isinstance(video, dict) else None
    if not video_url:
        sys.exit(f"ERROR: no video.url in response: {redact(json.dumps(result)[:500], api_key)}")

    output_path = Path(args.output)
    size_bytes = download(video_url, output_path)
    elapsed = time.time() - t0
    seed = result.get("seed", "(no seed)")

    print()
    print("=" * 60)
    print(f"OK: {output_path}")
    print(f"    size: {size_bytes / (1024 * 1024):.2f} MB ({size_bytes:,} bytes)")
    print(f"    API seed: {seed}")
    print(f"Total time: {elapsed:.1f}s")
    print(f"Retries:    {retries}")
    print(f"Est cost:   ${est_cost:.4f}")


if __name__ == "__main__":
    main()

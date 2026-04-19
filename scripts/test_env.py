#!/usr/bin/env python3
"""Verify .env loads GEMINI_API_KEY correctly. Never prints the key value."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.is_file():
    sys.exit(f"ERROR: {env_path} does not exist")

load_dotenv(env_path)

key = os.environ.get("GEMINI_API_KEY", "")
if not key:
    sys.exit("ERROR: GEMINI_API_KEY not set after load_dotenv")
if not key.startswith("AIzaSy"):
    sys.exit(f"ERROR: key does not start with 'AIzaSy' (got prefix {key[:2]!r})")

print(f"OK: GEMINI_API_KEY loaded via python-dotenv (length={len(key)}, prefix=AIzaSy)")

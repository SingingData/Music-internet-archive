#!/usr/bin/env python3
"""
SELECTIVE FLAC DOWNLOADER — From item list to target path
======================================================
Downloads only FLAC files for the Archive.org item IDs listed in get_list.txt

Configuration now comes from .env file (DOWNLOAD_BASE_PATH)
"""

import urllib.request
import urllib.error
import json
import os
import time
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from tqdm import tqdm  # Optional: pip install tqdm for nicer progress

# ── Find and load .env relative to script location ───────────────────────────
script_dir = Path(__file__).parent.resolve()
dotenv_path = find_dotenv(str(script_dir / ".env"))
if dotenv_path:
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env from: {dotenv_path}")
else:
    print("⚠️  No .env file found. Create one with DOWNLOAD_BASE_PATH=...")

# ── Configuration from .env (with CLI override) ─────────────────────────────
DEFAULT_BASE_PATH = os.getenv("DOWNLOAD_BASE_PATH")

# ── Other settings (can also be moved to .env later if desired) ─────────────
ITEM_LIST_FILE = "get_list.txt"
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5

def log(message, also_print=True):
    if also_print:
        print(message)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass

def log_failed(item_id, filename, url, reason):
    try:
        with open(FAILED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{item_id}\t{filename}\t{url}\t{reason}\n")
    except Exception:
        pass

def log_success(item_id, filename, dest_path, size_bytes):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(SUCCESS_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"{timestamp}\t{item_id}\t{filename}\t{dest_path}\t"
                f"{human_readable(size_bytes)} ({size_bytes} bytes)\n"
            )
    except Exception:
        pass

def fetch_json(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (FLAC downloader)"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f" ⚠ Attempt {attempt + 1}/{retries} failed ({e})")
            if attempt < retries - 1:
                time.sleep(delay)
    return None

def load_item_ids_from_file(list_path):
    if not os.path.exists(list_path):
        print(f"\n✗ Item list file not found: {list_path}")
        sys.exit(1)
    seen = set()
    item_ids = []
    with open(list_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if line and line not in seen:
                seen.add(line)
                item_ids.append(line)
    if not item_ids:
        print(f"\n✗ No item IDs found in: {list_path}")
        sys.exit(1)
    return item_ids

def get_flac_files_for_item(item_id):
    url = f"https://archive.org/metadata/{item_id}/files"
    data = fetch_json(url)
    if not data:
        return []
    result = data.get("result", [])
    if isinstance(result, dict):
        result = [result]
    flac_files = []
    for f in result:
        if isinstance(f, dict) and f.get("name", "").lower().endswith(".flac"):
            try:
                size = int(f.get("size", 0))
            except (ValueError, TypeError):
                size = 0
            flac_files.append({
                "name": f["name"],
                "size": size,
                "url": f"https://archive.org/download/{item_id}/{urllib.request.quote(f['name'])}"
            })
    return flac_files

def human_readable(size_bytes):
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.2f} GB"
    elif size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.2f} MB"
    elif size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.2f} KB"
    return f"{size_bytes} bytes"

def show_progress(downloaded, total):
    if total <= 0:
        return
    pct = downloaded / total * 100
    filled = int(pct / 2)
    bar = "█" * filled + "░" * (50 - filled)
    print(f"\r [{bar}] {pct:5.1f}% {human_readable(downloaded)} / {human_readable(total)}",
          end="", flush=True)

def download_file(url, dest_path, expected_size=0):
    for attempt in range(RETRY_ATTEMPTS):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (FLAC downloader)"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", expected_size) or 0)
                downloaded = 0
                chunk_size = 1024 * 256
                tmp_path = dest_path + ".part"
                with open(tmp_path, "wb") as out_file:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        show_progress(downloaded, total)
                print()  # finish progress bar
                os.replace(tmp_path, dest_path)
                return True
        except Exception as e:
            print(f"\n ⚠ Error on attempt {attempt + 1}/{RETRY_ATTEMPTS}: {e}")
        # Clean up partial file
        tmp_path = dest_path + ".part"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if attempt < RETRY_ATTEMPTS - 1:
            print(f" Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    return False

def safe_folder_name(name):
    invalid = r'\/:*?"<>|'
    for ch in invalid:
        name = name.replace(ch, "_")
    return name.strip()

def main(base_path: str):
    global LOG_FILE, FAILED_FILE, SUCCESS_FILE

    LOG_FILE = os.path.join(base_path, "_download_log.txt")
    FAILED_FILE = os.path.join(base_path, "_failed_downloads.txt")
    SUCCESS_FILE = os.path.join(base_path, "_successful_downloads.txt")

    print("=" * 72)
    print(" SELECTIVE FLAC DOWNLOADER — From list to target path")
    print(f" Base path : {base_path}")
    print(f" Item list file : {ITEM_LIST_FILE}")
    print("=" * 72)

    os.makedirs(base_path, exist_ok=True)

    item_ids = load_item_ids_from_file(ITEM_LIST_FILE)
    print(f"\n✔ Loaded {len(item_ids)} unique item IDs.\n")

    total_downloaded = 0
    total_files_done = 0
    total_files_skip = 0
    total_files_fail = 0

    for item_num, item_id in enumerate(item_ids, start=1):
        print(f"\n[{item_num}/{len(item_ids)}] Item: {item_id}")
        flac_files = get_flac_files_for_item(item_id)
        if not flac_files:
            print(" — No FLAC files found, skipping.")
            continue

        item_folder = os.path.join(base_path, safe_folder_name(item_id))
        os.makedirs(item_folder, exist_ok=True)

        for file_info in flac_files:
            filename = file_info["name"]
            dest_path = os.path.join(item_folder, filename)

            if os.path.exists(dest_path):
                print(f" ⏭ SKIP (already exists): {filename}")
                total_files_skip += 1
                continue

            print(f" ⬇ Downloading: {filename} ({human_readable(file_info['size'])})")
            success = download_file(file_info["url"], dest_path, file_info["size"])

            if success:
                actual_size = os.path.getsize(dest_path)
                print(f" ✔ Done: {filename} ({human_readable(actual_size)})")
                log_success(item_id, filename, dest_path, actual_size)
                total_downloaded += actual_size
                total_files_done += 1
            else:
                print(f" ✗ Failed: {filename}")
                log_failed(item_id, filename, file_info["url"], "Download failed after retries")
                total_files_fail += 1

    # Final summary
    print("\n" + "=" * 72)
    print("DOWNLOAD SUMMARY")
    print("=" * 72)
    print(f"Items processed   : {len(item_ids)}")
    print(f"Files downloaded  : {total_files_done}")
    print(f"Files skipped     : {total_files_skip}")
    print(f"Files failed      : {total_files_fail}")
    print(f"Total data downloaded: {human_readable(total_downloaded)}")
    print("=" * 72)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Selective Archive.org FLAC downloader with .env support."
    )
    parser.add_argument(
        "--base_path", "-b",
        default=DEFAULT_BASE_PATH,
        help="Base path where item folders will be created (overrides DOWNLOAD_BASE_PATH in .env)"
    )
    args = parser.parse_args()

    if not args.base_path:
        print("❌ ERROR: No base path provided.")
        print("   → Create a .env file with:")
        print("     DOWNLOAD_BASE_PATH=/path/to/your/usb/or/folder")
        print("   → Or run with: --base_path /your/path")
        sys.exit(1)

    main(args.base_path)
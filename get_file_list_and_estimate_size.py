"""
ESTIMATE TOTAL FLAC SIZE — Resilient Version
============================================
- Reduced ROWS_PER_PAGE to 200 for better reliability
- Stronger exponential backoff with increased jitter
- Saves final report to ARTIST_REPORTS/complete_list_and_sizes.txt
"""

import os
import json
import time
import random
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# ========================== LOAD FROM .env ==========================
load_dotenv()

COLLECTION_ID = os.getenv("COLLECTION_ID", "aadamjacobs")
ARTIST_REPORTS = os.getenv("ARTIST_REPORTS")

if not ARTIST_REPORTS:
    raise ValueError("ARTIST_REPORTS is not set in .env file")

REPORT_DIR = Path(ARTIST_REPORTS)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ========================== SETTINGS ==========================
ROWS_PER_PAGE = 200          # Reduced for better reliability on Archive.org
MAX_WORKERS = 3              # Conservative parallel fetching
BASE_DELAY = 1.5             # Increased base delay

print("=" * 80)
print("FLAC SIZE ESTIMATOR — Resilient Version")
print(f"Collection : {COLLECTION_ID}")
print(f"Report will be saved to: {REPORT_DIR}/complete_list_and_sizes.txt")
print("=" * 80)


def fetch_url(url, retries=10):
    """Stronger exponential backoff with more jitter."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/129.0.0.0 Safari/537.36 "
                                  "(Polite FLAC Size Estimator)"
                }
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            # Stronger backoff with more jitter
            wait = BASE_DELAY * (2 ** attempt) + random.uniform(2.0, 5.0)
            print(f"  ⚠ Attempt {attempt+1}/{retries} failed → waiting {wait:.1f}s")
            print(f"     Error: {e}")
            if attempt < retries - 1:
                time.sleep(wait)
    print(f"  ✗ Gave up after {retries} attempts on {url}")
    return None


def get_all_item_ids():
    """Fetch all item identifiers with reduced page size."""
    item_ids = []
    page = 1
    print(f"\n🔍 Searching collection '{COLLECTION_ID}'...")

    while True:
        url = (
            f"https://archive.org/advancedsearch.php"
            f"?q=collection%3A{COLLECTION_ID}"
            f"&fl[]=identifier"
            f"&rows={ROWS_PER_PAGE}"
            f"&page={page}"
            f"&output=json"
        )
        data = fetch_url(url)
        if not data:
            print("✗ Failed to fetch item list after multiple retries.")
            sys.exit(1)

        docs = data.get("response", {}).get("docs", [])
        if not docs:
            break

        for doc in docs:
            item_ids.append(doc["identifier"])

        total = data["response"]["numFound"]
        print(f"  ✔ Page {page}: fetched {len(docs)} items  "
              f"(total so far: {len(item_ids)} / {total})")

        if len(item_ids) >= total:
            break

        page += 1
        time.sleep(1.2)  # Polite delay between search pages

    return item_ids


def get_flac_size_for_item(item_id):
    """Fetch FLAC count and total size for one item."""
    url = f"https://archive.org/metadata/{item_id}/files"
    data = fetch_url(url)
    if not data:
        return 0, 0

    total_bytes = 0
    flac_count = 0

    files = data.get("result", [])
    if isinstance(files, dict):
        files = [files]

    for f in files:
        if isinstance(f, dict) and f.get("name", "").lower().endswith(".flac"):
            try:
                size = int(f.get("size", 0))
            except (ValueError, TypeError):
                size = 0
            total_bytes += size
            flac_count += 1

    return flac_count, total_bytes


def human_readable(size_bytes):
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.2f} GB"
    elif size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.2f} MB"
    elif size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.2f} KB"
    return f"{size_bytes} bytes"


def main():
    item_ids = get_all_item_ids()
    print(f"\n✔ Found {len(item_ids)} total items in the collection.\n")

    grand_total_bytes = 0
    grand_total_files = 0
    items_with_flac = 0

    print("📂 Fetching FLAC sizes using parallel requests...\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_item = {executor.submit(get_flac_size_for_item, iid): iid 
                         for iid in item_ids}

        for future in as_completed(future_to_item):
            item_id = future_to_item[future]
            try:
                flac_count, item_bytes = future.result()
                if flac_count > 0:
                    items_with_flac += 1
                    grand_total_bytes += item_bytes
                    grand_total_files += flac_count
                    print(f" [{items_with_flac:>4}/{len(item_ids)}] ✔ {item_id} → "
                          f"{flac_count} FLAC files — {human_readable(item_bytes)}")
                else:
                    print(f" [{len(item_ids)-items_with_flac:>4}/{len(item_ids)}] — {item_id} (no FLAC files)")
            except Exception as e:
                print(f" ✗ Error processing {item_id}: {e}")

    # ========================== SAVE REPORT ==========================
    report_path = REPORT_DIR / "complete_list_and_sizes.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"FLAC Size Report for collection '{COLLECTION_ID}' — {timestamp}\n")
        f.write("=" * 85 + "\n\n")
        f.write(f"Total items scanned          : {len(item_ids)}\n")
        f.write(f"Items with FLAC files        : {items_with_flac}\n")
        f.write(f"Items without FLAC files     : {len(item_ids) - items_with_flac}\n")
        f.write(f"Total FLAC files             : {grand_total_files}\n")
        f.write(f"Total FLAC size              : {human_readable(grand_total_bytes)}\n")
        f.write(f"Exact size (bytes)           : {grand_total_bytes:,}\n\n")
        f.write(f"Recommended free space (+5% buffer): "
                f"{human_readable(int(grand_total_bytes * 1.05))}\n")

    print("\n" + "=" * 85)
    print("SUMMARY")
    print("=" * 85)
    print(f"Total FLAC size : {human_readable(grand_total_bytes)}")
    print(f"Report saved to : {report_path}")
    print("=" * 85)


if __name__ == "__main__":
    main()
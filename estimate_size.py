"""
SCRIPT 1: ESTIMATE TOTAL FLAC SIZE (ROBUST VERSION)
====================================================
Fixed for connection timeouts on Archive.org.
"""

import urllib.request
import json
import time
import sys
import random   # ← added for jitter

# ── CONFIG ────────────────────────────────────────────────────────────────────
COLLECTION_ID = "aadamjacobs"
ROWS_PER_PAGE = 500             # Increased → fewer API calls, much more reliable
# ──────────────────────────────────────────────────────────────────────────────


def fetch_url(url, retries=8, initial_delay=5):
    """Fetch URL with strong exponential backoff + jitter."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/129.0.0.0 Safari/537.36 "
                                  "(FLAC size estimator - polite)"
                }
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"  ⚠  Attempt {attempt + 1}/{retries} failed for {url}")
            print(f"     Error: {e}")
            if attempt < retries - 1:
                # Exponential backoff + small random jitter
                wait = initial_delay * (2 ** attempt) + random.uniform(0.5, 2.0)
                print(f"     Waiting {wait:.1f} seconds before next try...")
                time.sleep(wait)
    print(f"  ✗ Gave up after {retries} attempts.")
    return None


def get_all_item_ids(collection_id):
    item_ids = []
    page = 1

    print(f"\n🔍 Searching for all items in collection '{collection_id}'...")

    while True:
        url = (
            f"https://archive.org/advancedsearch.php"
            f"?q=collection%3A{collection_id}"
            f"&fl[]=identifier"
            f"&rows={ROWS_PER_PAGE}"
            f"&page={page}"
            f"&output=json"
        )

        data = fetch_url(url)
        if not data:
            print("  ✗ Failed to fetch item list after retries.")
            print("    Tip: Check your internet and try running the script again.")
            sys.exit(1)

        docs = data.get("response", {}).get("docs", [])
        if not docs:
            break

        for doc in docs:
            item_ids.append(doc["identifier"])

        total_found = data["response"]["numFound"]
        print(f"  ✔ Page {page}: fetched {len(docs)} items "
              f"({len(item_ids)} of {total_found} total)")

        if len(item_ids) >= total_found:
            break
        page += 1
        time.sleep(1.5)  # Be very polite between pages

    return item_ids


def get_flac_size_for_item(item_id):
    url = f"https://archive.org/metadata/{item_id}/files"
    data = fetch_url(url)

    if not data:
        return 0, []

    flac_files = []
    result = data.get("result", [])

    if isinstance(result, dict):
        result = [result]

    for f in result:
        if isinstance(f, dict) and f.get("name", "").lower().endswith(".flac"):
            try:
                size = int(f.get("size", 0))
            except (ValueError, TypeError):
                size = 0
            flac_files.append((f["name"], size))

    total = sum(s for _, s in flac_files)
    return total, flac_files


def human_readable(size_bytes):
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.2f} GB"
    elif size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.2f} MB"
    elif size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.2f} KB"
    return f"{size_bytes} bytes"


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  FLAC SIZE ESTIMATOR — archive.org collection (ROBUST VERSION)")
    print(f"  Collection: {COLLECTION_ID}")
    print("=" * 70)

    item_ids = get_all_item_ids(COLLECTION_ID)

    if not item_ids:
        print("\n✗ No items found. Check the collection ID.")
        sys.exit(1)

    print(f"\n✔ Found {len(item_ids)} items in the collection.\n")

    print("📂 Scanning each item for FLAC files...\n")

    grand_total_bytes = 0
    grand_total_files = 0
    items_with_flac = 0
    items_without_flac = []

    for i, item_id in enumerate(item_ids, start=1):
        item_bytes, flac_files = get_flac_size_for_item(item_id)

        if flac_files:
            items_with_flac += 1
            grand_total_bytes += item_bytes
            grand_total_files += len(flac_files)
            print(f"  [{i:>3}/{len(item_ids)}] ✔ {item_id}")
            print(f"         {len(flac_files)} FLAC file(s) — {human_readable(item_bytes)}")
        else:
            items_without_flac.append(item_id)
            print(f"  [{i:>3}/{len(item_ids)}] — {item_id} (no FLAC files)")

        time.sleep(0.75)   # Polite delay between items

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Total items scanned   : {len(item_ids)}")
    print(f"  Items with FLAC files : {items_with_flac}")
    print(f"  Items without FLAC    : {len(items_without_flac)}")
    print(f"  Total FLAC files      : {grand_total_files}")
    print(f"  Total FLAC size       : {human_readable(grand_total_bytes)}")
    print(f"  (Exact bytes)         : {grand_total_bytes:,} bytes")
    print("=" * 70)
    print("\n💡 TIP: Make sure your USB drive has at least")
    print(f"   {human_readable(int(grand_total_bytes * 1.05))} free")
    print("   (includes a 5% safety buffer)\n")


if __name__ == "__main__":
    main()
"""
FIND ARTIST WAV FILES - Fuzzy Matching Version
==============================================
Outputs a clean list with header lines commented out.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import re

# ========================== LOAD PATHS FROM .env ==========================
load_dotenv()

DIAGNOSE_SOURCE = os.getenv("DIAGNOSE_SOURCE")
ARTIST_LIST     = os.getenv("ARTIST_LIST")
ARTIST_REPORTS  = os.getenv("ARTIST_REPORTS")

# Fallbacks
if not DIAGNOSE_SOURCE:
    DIAGNOSE_SOURCE = r"E:\aadamjacobs\Originals\WAV"
if not ARTIST_LIST:
    ARTIST_LIST = r"C:\Users\patty\miniconda3\Scripts\music-download\artists_to_find.txt"
if not ARTIST_REPORTS:
    ARTIST_REPORTS = r"C:\Users\patty\miniconda3\Scripts\music-download\Reports"

print("Fuzzy Artist Search Configuration:")
print(f"   DIAGNOSE_SOURCE = {DIAGNOSE_SOURCE}")
print(f"   ARTIST_LIST     = {ARTIST_LIST}")
print(f"   ARTIST_REPORTS  = {ARTIST_REPORTS}")
print("-" * 80)

Path(ARTIST_REPORTS).mkdir(parents=True, exist_ok=True)

# ========================== LOAD ARTIST SEARCH LIST ==========================
with open(ARTIST_LIST, "r", encoding="utf-8") as f:
    artists = [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]

print(f"Loaded {len(artists)} artists for fuzzy matching.\n")

# Prepare regex patterns for fuzzy/concatenated matching
patterns = []
for artist in artists:
    patterns.append(re.compile(re.escape(artist), re.IGNORECASE))
    patterns.append(re.compile(re.escape(artist.replace(" ", "")), re.IGNORECASE))

# ========================== RECURSIVE SEARCH ==========================
source_root = Path(DIAGNOSE_SOURCE)
matching_files = []

print("Scanning for matching .wav files...")

for wav_file in tqdm(list(source_root.rglob("*.wav")), desc="Scanning WAV files"):
    filename = wav_file.name.lower()
    filename_no_ext = Path(filename).stem.lower()
    
    for pattern in patterns:
        if pattern.search(filename) or pattern.search(filename_no_ext):
            matching_files.append(str(wav_file))
            break

# Remove duplicates while preserving order
matching_files = list(dict.fromkeys(matching_files))

# ========================== SAVE RESULTS ==========================
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

report_txt = Path(ARTIST_REPORTS) / f"artist_files_fuzzy_{timestamp}.txt"
report_csv = Path(ARTIST_REPORTS) / f"artist_files_fuzzy_{timestamp}.csv"

# Text report with header lines commented out
with open(report_txt, "w", encoding="utf-8") as f:
    f.write(f"# Fuzzy Artist Match Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"# Search artists: {', '.join(artists)}\n")
    f.write(f"# Total matching files found: {len(matching_files)}\n")
    f.write("#" + "=" * 88 + "\n\n")
    
    # Actual file list (no comments)
    for path in sorted(matching_files):
        f.write(f"{path}\n")

# CSV report (unchanged - clean for spreadsheets)
with open(report_csv, "w", encoding="utf-8", newline="") as f:
    f.write("full_path,filename\n")
    for path in sorted(matching_files):
        filename = Path(path).name
        f.write(f'"{path}","{filename}"\n')

print("\n" + "=" * 90)
print("FUZZY SEARCH COMPLETE")
print("=" * 90)
print(f"Total matching .wav files: {len(matching_files)}")
print(f"Text report: {report_txt.name}  (headers are commented out)")
print(f"CSV report:  {report_csv.name}")
print(f"Saved to: {ARTIST_REPORTS}")

if len(matching_files) == 0:
    print("\nNo matches found. Try adding more variations to artists_to_find.txt")
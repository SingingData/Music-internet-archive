"""
BATCH AUDIO CLEANER - Option B
==============================
Reads a list of files from CLEANING_LIST and processes the corresponding WAV files.

Features:
- Reads paths from .env file
- Searches recursively in DIAGNOSE_SOURCE for the files
- Applies gentle gain reduction on files that are too loud
- Saves cleaned versions to CLEANED_1 folder (preserving subfolder structure)
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from pydub import AudioSegment

# ========================== LOAD PATHS FROM .ENV ==========================
load_dotenv()

CLEANING_LIST   = os.getenv("CLEANING_LIST")
DIAGNOSE_SOURCE = os.getenv("DIAGNOSE_SOURCE")
CLEANED_1       = os.getenv("CLEANED_1")

# Fallbacks if .env is missing or incomplete
if not CLEANING_LIST:
    CLEANING_LIST = r"C:\Users\patty\miniconda3\Scripts\music-download\Lists\Cleaning_List.txt"
if not DIAGNOSE_SOURCE:
    DIAGNOSE_SOURCE = r"E:\aadamjacobs\Originals\WAV"
if not CLEANED_1:
    CLEANED_1 = r"E:\aadamjacobs\Transformed\Cleaned_1"

print("Batch Audio Cleaner Configuration:")
print(f"   CLEANING_LIST   = {CLEANING_LIST}")
print(f"   DIAGNOSE_SOURCE = {DIAGNOSE_SOURCE}  (recursive search)")
print(f"   CLEANED_1       = {CLEANED_1}")
print("-" * 70)

# Create output folder
Path(CLEANED_1).mkdir(parents=True, exist_ok=True)

# Timestamp for this run
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = Path(CLEANED_1) / f"cleaning_log_{timestamp}.txt"


def find_wav_file(filename: str, source_root: Path):
    """Recursively search for a WAV file by stem name (case-insensitive)."""
    stem = Path(filename).stem.lower()
    for ext in [".wav", ".WAV"]:
        for found_file in source_root.rglob(f"*{ext}"):
            if found_file.stem.lower() == stem:
                return found_file
    return None


def clean_audio(input_path: str, output_path: str):
    """Apply gentle normalization and light processing."""
    try:
        audio = AudioSegment.from_file(input_path, format="wav")
        
        # Gentle gain reduction if the file is too hot (peak > -3 dBFS)
        if audio.max_dBFS > -3.0:
            gain_reduction = -4.0  # reduce by 4 dB to give headroom
            audio = audio.apply_gain(gain_reduction)
            action = f"Reduced gain by {gain_reduction} dB"
        else:
            action = "No gain reduction needed (already good headroom)"

        # Optional: Very light compression (can be adjusted)
        # audio = audio.compress_dynamic_range(threshold=-18, ratio=2.0, attack=5, release=50)

        # Export
        audio.export(output_path, format="wav")
        return True, action, round(audio.max_dBFS, 2)

    except Exception as e:
        return False, f"Error: {str(e)}", None


def main():
    print("=" * 80)
    print("BATCH AUDIO CLEANER")
    print("=" * 80)

    if not os.path.exists(CLEANING_LIST):
        print(f"Error: Cleaning list not found -> {CLEANING_LIST}")
        return

    # Read list of files to clean
    with open(CLEANING_LIST, "r", encoding="utf-8") as f:
        file_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"Loaded {len(file_list)} files for cleaning.\n")

    source_root = Path(DIAGNOSE_SOURCE)
    cleaned_root = Path(CLEANED_1)

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"Batch Cleaning Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("=" * 80 + "\n\n")

        for filename in tqdm(file_list, desc="Cleaning files"):
            wav_file = find_wav_file(filename, source_root)

            if not wav_file or not wav_file.exists():
                msg = f"NOT FOUND   {filename}"
                print(msg)
                log.write(msg + "\n")
                continue

            # Build output path (preserve folder structure)
            relative = wav_file.relative_to(source_root)
            output_file = cleaned_root / relative

            output_file.parent.mkdir(parents=True, exist_ok=True)

            success, action, new_peak = clean_audio(str(wav_file), str(output_file))

            if success:
                msg = f"OK   {filename}  ->  {action}  (new peak: {new_peak} dBFS)"
                print(msg)
                log.write(msg + "\n")
            else:
                msg = f"FAILED   {filename}  ->  {action}"
                print(msg)
                log.write(msg + "\n")

    print("\n" + "=" * 80)
    print("Batch cleaning finished!")
    print(f"Log saved to: {log_file.name}")
    print(f"Cleaned files saved in: {CLEANED_1}")
    print("=" * 80)


if __name__ == "__main__":
    main()
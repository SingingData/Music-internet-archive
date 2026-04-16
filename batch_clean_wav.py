"""
BATCH AUDIO CLEANER - Skip Existing Files in CLEANED_1 and CLEANED_2
===================================================================
Now skips files that already exist in CLEANED_1 or CLEANED_2 (preserving folder structure).
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from pydub import AudioSegment

# ========================== LOAD PATHS FROM .env ==========================
load_dotenv()

CLEANING_LIST     = os.getenv("CLEANING_LIST")
DIAGNOSE_SOURCE   = os.getenv("DIAGNOSE_SOURCE")
CLEANED_1         = os.getenv("CLEANED_1")
CLEANED_2         = os.getenv("CLEANED_2")          # New: Second cleaned folder
TRANSFORM_CONFIG  = os.getenv("TRANSFORM_CONFIG")

# Fallbacks / Validation
if not CLEANING_LIST:
    raise ValueError("CLEANING_LIST is not set in .env")
if not DIAGNOSE_SOURCE:
    raise ValueError("DIAGNOSE_SOURCE is not set in .env")
if not CLEANED_1:
    raise ValueError("CLEANED_1 is not set in .env")
if not TRANSFORM_CONFIG:
    raise ValueError("TRANSFORM_CONFIG is not set in .env")

# Optional CLEANED_2 (won't break if missing)
if not CLEANED_2:
    CLEANED_2 = None
    print("Note: CLEANED_2 not set in .env - only checking CLEANED_1 for existing files.")

print("Batch Audio Cleaner Configuration:")
print(f"   CLEANING_LIST    = {CLEANING_LIST}")
print(f"   DIAGNOSE_SOURCE  = {DIAGNOSE_SOURCE}")
print(f"   CLEANED_1        = {CLEANED_1}")
print(f"   CLEANED_2        = {CLEANED_2 or 'Not configured'}")
print(f"   TRANSFORM_CONFIG = {TRANSFORM_CONFIG}")
print("-" * 90)

# ========================== LOAD AUDIO CONFIG FROM TRANSFORM_CONFIG ==========================
config_path = Path(TRANSFORM_CONFIG)
if not config_path.exists():
    raise FileNotFoundError(f"transform_configuration.txt not found at:\n{TRANSFORM_CONFIG}")

with open(config_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = [x.strip() for x in line.split("=", 1)]
            if key in ["GAIN_REDUCTION_DB", "HARSH_CUT_DB", "GUITAR_DRUM_CUT_DB",
                       "WARMTH_BOOST_DB", "VOCAL_BOOST_DB", "HIGH_NOTE_CUT_DB",
                       "SNARE_BODY_BOOST_DB"]:
                globals()[key] = float(value)
            elif key in ["HIGH_PASS_FREQ", "HARSH_CUT_FREQ", "GUITAR_DRUM_CUT_FREQ",
                         "WARMTH_BOOST_FREQ", "VOCAL_BOOST_FREQ", "HIGH_NOTE_CUT_FREQ",
                         "SNARE_BODY_BOOST_FREQ"]:
                globals()[key] = int(value)

print("Audio Transform Settings loaded:")
print(f"   GAIN_REDUCTION_DB   = {GAIN_REDUCTION_DB} dB")
print(f"   SNARE_BODY_BOOST    = {SNARE_BODY_BOOST_DB} dB @ {SNARE_BODY_BOOST_FREQ} Hz")
print(f"   VOCAL_BOOST         = {VOCAL_BOOST_DB} dB @ {VOCAL_BOOST_FREQ} Hz")
print("-" * 90)

Path(CLEANED_1).mkdir(parents=True, exist_ok=True)
if CLEANED_2:
    Path(CLEANED_2).mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = Path(CLEANED_1) / f"cleaning_log_{timestamp}.txt"


def find_wav_file(filename: str, source_root: Path):
    stem = Path(filename).stem.lower()
    for ext in [".wav", ".WAV"]:
        for found_file in source_root.rglob(f"*{ext}"):
            if found_file.stem.lower() == stem:
                return found_file
    return None


def is_already_processed(relative_path: Path):
    """Check if file already exists in CLEANED_1 or CLEANED_2"""
    # Check CLEANED_1
    if (Path(CLEANED_1) / relative_path).exists():
        return True
    # Check CLEANED_2 if configured
    if CLEANED_2 and (Path(CLEANED_2) / relative_path).exists():
        return True
    return False


def clean_audio(input_path: str, output_path: str):
    try:
        audio = AudioSegment.from_file(input_path, format="wav")
        original_peak = audio.max_dBFS

        if original_peak > -3.0:
            audio = audio.apply_gain(GAIN_REDUCTION_DB)

        audio = audio.high_pass_filter(HIGH_PASS_FREQ)

        if HARSH_CUT_DB < 0:
            audio = audio.low_pass_filter(HARSH_CUT_FREQ)

        if GUITAR_DRUM_CUT_DB < 0:
            audio = audio.low_pass_filter(GUITAR_DRUM_CUT_FREQ)

        if SNARE_BODY_BOOST_DB > 0:
            audio = audio.apply_gain(SNARE_BODY_BOOST_DB * 0.7)

        if WARMTH_BOOST_DB > 0:
            audio = audio.apply_gain(WARMTH_BOOST_DB * 0.65)

        if VOCAL_BOOST_DB > 0:
            audio = audio.apply_gain(VOCAL_BOOST_DB * 0.7)

        if HIGH_NOTE_CUT_DB < 0:
            audio = audio.low_pass_filter(HIGH_NOTE_CUT_FREQ)

        audio.export(output_path, format="wav")
        return True, "Processed successfully", round(audio.max_dBFS, 2)

    except Exception as e:
        return False, f"Error: {str(e)}", None


def main():
    print("=" * 90)
    print("BATCH AUDIO CLEANER - Skip Existing + Snare/Vocal Improvements")
    print("=" * 90)

    if not os.path.exists(CLEANING_LIST):
        print(f"Error: Cleaning list not found -> {CLEANING_LIST}")
        return

    with open(CLEANING_LIST, "r", encoding="utf-8") as f:
        file_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"Loaded {len(file_list)} files for cleaning.\n")

    source_root = Path(DIAGNOSE_SOURCE)
    cleaned_root1 = Path(CLEANED_1)
    cleaned_root2 = Path(CLEANED_2) if CLEANED_2 else None

    skipped = 0
    processed = 0

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"Batch Cleaning Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("=" * 90 + "\n\n")

        for filename in tqdm(file_list, desc="Processing files"):
            wav_file = find_wav_file(filename, source_root)

            if not wav_file or not wav_file.exists():
                msg = f"NOT FOUND   {filename}"
                print(msg)
                log.write(msg + "\n")
                continue

            relative = wav_file.relative_to(source_root)

            # NEW: Skip if already exists in CLEANED_1 or CLEANED_2
            if is_already_processed(relative):
                skipped += 1
                msg = f"SKIPPED (already exists)   {filename}"
                print(msg)
                log.write(msg + "\n")
                continue

            # Process the file
            output_file = cleaned_root1 / relative
            output_file.parent.mkdir(parents=True, exist_ok=True)

            success, action, new_peak = clean_audio(str(wav_file), str(output_file))

            if success:
                processed += 1
                msg = f"OK   {filename}  →  {action}  → New peak: {new_peak} dBFS"
                print(msg)
                log.write(msg + "\n")
            else:
                msg = f"FAILED   {filename}  →  {action}"
                print(msg)
                log.write(msg + "\n")

    print("\n" + "=" * 90)
    print("Batch cleaning finished!")
    print(f"Processed : {processed}")
    print(f"Skipped   : {skipped} (already existed in CLEANED_1 or CLEANED_2)")
    print(f"Log saved to: {log_file.name}")
    print(f"Cleaned files saved in: {CLEANED_1}")
    if CLEANED_2:
        print(f"Also checking: {CLEANED_2}")
    print("=" * 90)


if __name__ == "__main__":
    main()
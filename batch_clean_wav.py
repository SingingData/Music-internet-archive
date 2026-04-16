"""
BATCH AUDIO CLEANER - Transform Config Location ONLY from .env
==============================================================
TRANSFORM_CONFIG is now strictly read from .env only.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from pydub import AudioSegment

# ========================== LOAD PATHS FROM .env ONLY ==========================
load_dotenv()

CLEANING_LIST     = os.getenv("CLEANING_LIST")
DIAGNOSE_SOURCE   = os.getenv("DIAGNOSE_SOURCE")
CLEANED_1         = os.getenv("CLEANED_1")
TRANSFORM_CONFIG  = os.getenv("TRANSFORM_CONFIG")

# Required path validation
if not CLEANING_LIST:
    raise ValueError("CLEANING_LIST is not set in .env")
if not DIAGNOSE_SOURCE:
    raise ValueError("DIAGNOSE_SOURCE is not set in .env")
if not CLEANED_1:
    raise ValueError("CLEANED_1 is not set in .env")
if not TRANSFORM_CONFIG:
    raise ValueError("TRANSFORM_CONFIG is not set in .env file. Please add it.")

print("Batch Audio Cleaner Configuration (from .env):")
print(f"   CLEANING_LIST    = {CLEANING_LIST}")
print(f"   DIAGNOSE_SOURCE  = {DIAGNOSE_SOURCE}")
print(f"   CLEANED_1        = {CLEANED_1}")
print(f"   TRANSFORM_CONFIG = {TRANSFORM_CONFIG}")
print("-" * 90)

# ========================== LOAD AUDIO CONFIG FROM TRANSFORM_CONFIG ==========================
config_path = Path(TRANSFORM_CONFIG)

if not config_path.exists():
    raise FileNotFoundError(f"transform_configuration.txt not found at the location specified in .env:\n"
                            f"{TRANSFORM_CONFIG}\n\n"
                            f"Please create the file at that exact path.")

# Load all transform settings
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

print("Audio Transform Settings loaded successfully:")
print(f"   GAIN_REDUCTION_DB   = {GAIN_REDUCTION_DB} dB")
print(f"   HIGH_PASS_FREQ      = {HIGH_PASS_FREQ} Hz")
print(f"   HARSH_CUT           = {HARSH_CUT_DB} dB @ {HARSH_CUT_FREQ} Hz")
print(f"   GUITAR_DRUM_CUT     = {GUITAR_DRUM_CUT_DB} dB @ {GUITAR_DRUM_CUT_FREQ} Hz")
print(f"   SNARE_BODY_BOOST    = {SNARE_BODY_BOOST_DB} dB @ {SNARE_BODY_BOOST_FREQ} Hz")
print(f"   WARMTH_BOOST        = {WARMTH_BOOST_DB} dB @ {WARMTH_BOOST_FREQ} Hz")
print(f"   VOCAL_BOOST         = {VOCAL_BOOST_DB} dB @ {VOCAL_BOOST_FREQ} Hz")
print(f"   HIGH_NOTE_CUT       = {HIGH_NOTE_CUT_DB} dB @ {HIGH_NOTE_CUT_FREQ} Hz")
print("-" * 90)

Path(CLEANED_1).mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = Path(CLEANED_1) / f"cleaning_log_{timestamp}.txt"


def find_wav_file(filename: str, source_root: Path):
    stem = Path(filename).stem.lower()
    for ext in [".wav", ".WAV"]:
        for found_file in source_root.rglob(f"*{ext}"):
            if found_file.stem.lower() == stem:
                return found_file
    return None


def clean_audio(input_path: str, output_path: str):
    try:
        audio = AudioSegment.from_file(input_path, format="wav")
        original_peak = audio.max_dBFS

        # 1. Gain reduction for headroom
        if original_peak > -3.0:
            audio = audio.apply_gain(GAIN_REDUCTION_DB)

        # 2. High-pass filter (rumble removal)
        audio = audio.high_pass_filter(HIGH_PASS_FREQ)

        # 3. Broad harshness cut
        if HARSH_CUT_DB < 0:
            audio = audio.low_pass_filter(HARSH_CUT_FREQ)

        # 4. Guitar & drum tinny high-note cut
        if GUITAR_DRUM_CUT_DB < 0:
            audio = audio.low_pass_filter(GUITAR_DRUM_CUT_FREQ)

        # 5. Snare drum body boost
        if SNARE_BODY_BOOST_DB > 0:
            audio = audio.apply_gain(SNARE_BODY_BOOST_DB * 0.7)

        # 6. Warmth boost for overall thin mix
        if WARMTH_BOOST_DB > 0:
            audio = audio.apply_gain(WARMTH_BOOST_DB * 0.65)

        # 7. Vocal presence boost
        if VOCAL_BOOST_DB > 0:
            audio = audio.apply_gain(VOCAL_BOOST_DB * 0.7)

        # 8. Final tinny high-note cut
        if HIGH_NOTE_CUT_DB < 0:
            audio = audio.low_pass_filter(HIGH_NOTE_CUT_FREQ)

        audio.export(output_path, format="wav")

        return True, "Full processing applied", round(audio.max_dBFS, 2)

    except Exception as e:
        return False, f"Error: {str(e)}", None


def main():
    print("=" * 90)
    print("BATCH AUDIO CLEANER - Snare Body + Stronger Vocal Boost")
    print("=" * 90)

    if not os.path.exists(CLEANING_LIST):
        print(f"Error: Cleaning list not found -> {CLEANING_LIST}")
        return

    with open(CLEANING_LIST, "r", encoding="utf-8") as f:
        file_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"Loaded {len(file_list)} files for cleaning.\n")

    source_root = Path(DIAGNOSE_SOURCE)
    cleaned_root = Path(CLEANED_1)

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"Batch Cleaning Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("=" * 90 + "\n\n")

        for filename in tqdm(file_list, desc="Cleaning files"):
            wav_file = find_wav_file(filename, source_root)

            if not wav_file or not wav_file.exists():
                msg = f"NOT FOUND   {filename}"
                print(msg)
                log.write(msg + "\n")
                continue

            relative = wav_file.relative_to(source_root)
            output_file = cleaned_root / relative
            output_file.parent.mkdir(parents=True, exist_ok=True)

            success, action, new_peak = clean_audio(str(wav_file), str(output_file))

            if success:
                msg = f"OK   {filename}  →  {action}  → New peak: {new_peak} dBFS"
                print(msg)
                log.write(msg + "\n")
            else:
                msg = f"FAILED   {filename}  →  {action}"
                print(msg)
                log.write(msg + "\n")

    print("\nBatch cleaning finished!")
    print(f"Log saved to: {log_file.name}")
    print(f"Cleaned files saved in: {CLEANED_1}")


if __name__ == "__main__":
    main()
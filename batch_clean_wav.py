"""
BATCH AUDIO CLEANER - Vocal Boost + Tinny Highs Fix
===================================================
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from pydub import AudioSegment

# ========================== LOAD FROM .env ==========================
load_dotenv()

CLEANING_LIST         = os.getenv("CLEANING_LIST")
DIAGNOSE_SOURCE       = os.getenv("DIAGNOSE_SOURCE")
CLEANED_1             = os.getenv("CLEANED_1")

GAIN_REDUCTION_DB     = float(os.getenv("GAIN_REDUCTION_DB", "-5.0"))
HIGH_PASS_FREQ        = int(os.getenv("HIGH_PASS_FREQ", "100"))
HARSH_CUT_DB          = float(os.getenv("HARSH_CUT_DB", "-4.5"))
HARSH_CUT_FREQ        = int(os.getenv("HARSH_CUT_FREQ", "5200"))
WARMTH_BOOST_DB       = float(os.getenv("WARMTH_BOOST_DB", "4.0"))
WARMTH_BOOST_FREQ     = int(os.getenv("WARMTH_BOOST_FREQ", "300"))
VOCAL_BOOST_DB        = float(os.getenv("VOCAL_BOOST_DB", "3.0"))      # New: Vocal presence
VOCAL_BOOST_FREQ      = int(os.getenv("VOCAL_BOOST_FREQ", "2500"))    # New: Vocal range center
HIGH_NOTE_CUT_DB      = float(os.getenv("HIGH_NOTE_CUT_DB", "-3.0"))  # New: Tinny highs
HIGH_NOTE_CUT_FREQ    = int(os.getenv("HIGH_NOTE_CUT_FREQ", "7500"))

# Fallback paths
if not CLEANING_LIST:
    CLEANING_LIST = r"C:\Users\patty\miniconda3\Scripts\music-download\Lists\Cleaning_List.txt"
if not DIAGNOSE_SOURCE:
    DIAGNOSE_SOURCE = r"E:\aadamjacobs\Originals\WAV"
if not CLEANED_1:
    CLEANED_1 = r"E:\aadamjacobs\Transformed\Cleaned_1"

print("Batch Audio Cleaner Configuration:")
print(f"   GAIN_REDUCTION_DB = {GAIN_REDUCTION_DB} dB")
print(f"   HIGH_PASS_FREQ    = {HIGH_PASS_FREQ} Hz")
print(f"   HARSH_CUT         = {HARSH_CUT_DB} dB @ {HARSH_CUT_FREQ} Hz")
print(f"   WARMTH_BOOST      = {WARMTH_BOOST_DB} dB @ {WARMTH_BOOST_FREQ} Hz")
print(f"   VOCAL_BOOST       = {VOCAL_BOOST_DB} dB @ {VOCAL_BOOST_FREQ} Hz")
print(f"   HIGH_NOTE_CUT     = {HIGH_NOTE_CUT_DB} dB @ {HIGH_NOTE_CUT_FREQ} Hz")
print("-" * 85)

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

        # 1. Gentle overall gain reduction for headroom
        if original_peak > -3.0:
            audio = audio.apply_gain(GAIN_REDUCTION_DB)

        # 2. High-Pass Filter - Remove rumble
        audio = audio.high_pass_filter(HIGH_PASS_FREQ)

        # 3. Harshness cut (cymbals)
        if HARSH_CUT_DB < 0:
            audio = audio.low_pass_filter(HARSH_CUT_FREQ)

        # 4. Warmth boost for thin mix
        if WARMTH_BOOST_DB > 0:
            audio = audio.apply_gain(WARMTH_BOOST_DB * 0.6)

        # 5. Vocal presence boost (mid-range)
        if VOCAL_BOOST_DB > 0:
            audio = audio.apply_gain(VOCAL_BOOST_DB * 0.7)

        # 6. Tinny high notes cut (for distorted highs)
        if HIGH_NOTE_CUT_DB < 0:
            audio = audio.low_pass_filter(HIGH_NOTE_CUT_FREQ)

        audio.export(output_path, format="wav")

        return True, "Full processing applied (Gain + HPF + EQs)", round(audio.max_dBFS, 2)

    except Exception as e:
        return False, f"Error: {str(e)}", None


def main():
    print("=" * 85)
    print("BATCH AUDIO CLEANER - Vocal Boost + Tinny Highs Fix")
    print("=" * 85)

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
        log.write("=" * 85 + "\n\n")

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
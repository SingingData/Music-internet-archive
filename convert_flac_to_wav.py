"""
FLAC to WAV Converter
=====================
Converts all FLAC files from a source folder (and all subfolders) to WAV.
Uses .env file for easy configuration.
"""

import os
from dotenv import load_dotenv
import argparse
from pathlib import Path
from tqdm import tqdm

# ========================== LOAD PATHS FROM .env ==========================
load_dotenv()

# Get paths from .env
FLAC_INPUT_ROOT = os.getenv("FLAC_INPUT_ROOT")
WAV_OUTPUT_ROOT = os.getenv("WAV_OUTPUT_ROOT")

# Optional: Fallbacks if .env is missing
if not FLAC_INPUT_ROOT:
    FLAC_INPUT_ROOT = r"E:\aadamjacobs\Originals\FLAC"
if not WAV_OUTPUT_ROOT:
    WAV_OUTPUT_ROOT = r"E:\aadamjacobs\Originals\WAV"

print(f"Configuration:")
print(f"   FLAC_INPUT_ROOT = {FLAC_INPUT_ROOT}")
print(f"   WAV_OUTPUT_ROOT = {WAV_OUTPUT_ROOT}")
print("-" * 60)
# =====================================================================

try:
    from pydub import AudioSegment
except ImportError:
    print("❌ pydub is not installed.")
    print("   Run: pip install pydub")
    exit(1)


def convert_flac_to_wav(input_root: str, output_root: str, overwrite: bool = False):
    input_path = Path(input_root)
    output_path = Path(output_root)

    if not input_path.exists() or not input_path.is_dir():
        raise NotADirectoryError(f"Input root does not exist or is not a directory: {input_root}")

    output_path.mkdir(parents=True, exist_ok=True)

    # Find all FLAC files recursively
    flac_files = list(input_path.rglob("*.flac"))
    print(f"Found {len(flac_files)} FLAC files to convert.\n")

    for flac_file in tqdm(flac_files, desc="Converting FLAC → WAV"):
        # Build output path (preserve folder structure)
        relative_path = flac_file.relative_to(input_path)
        wav_file = output_path / relative_path.with_suffix(".wav")

        # Skip if file already exists and overwrite is False
        if wav_file.exists() and not overwrite:
            continue

        try:
            # Create output subfolder if needed
            wav_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert
            audio = AudioSegment.from_file(str(flac_file), format="flac")
            audio.export(str(wav_file), format="wav")

        except Exception as e:
            print(f"\n✗ Failed to convert {flac_file.name}: {e}")

    print("\n✅ Conversion complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert FLAC files to WAV")
    parser.add_argument("-i", "--input", type=str, default=FLAC_INPUT_ROOT,
                        help="Root folder containing FLAC files")
    parser.add_argument("-o", "--output", type=str, default=WAV_OUTPUT_ROOT,
                        help="Root folder where WAV files will be saved")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing WAV files")

    args = parser.parse_args()

    try:
        convert_flac_to_wav(args.input, args.output, args.overwrite)
    except Exception as e:
        print(f"\n❌ Error: {e}")
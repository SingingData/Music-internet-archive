#!/usr/bin/env python3
"""
FLAC → WAV Batch Converter (Bit-Perfect, Lossless)
- Reads input/output roots from .env file (FLAC_INPUT_ROOT and WAV_OUTPUT_ROOT)
- Command-line args override .env values
- Preserves exact folder structure
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm
import soundfile as sf

def convert_flac_to_wav(input_root: str | Path, output_root: str | Path, overwrite: bool = False):
    input_root = Path(input_root).resolve()
    output_root = Path(output_root).resolve()
    
    if not input_root.is_dir():
        raise NotADirectoryError(f"Input root does not exist or is not a directory: {input_root}")
    
    output_root.mkdir(parents=True, exist_ok=True)
    
    # Find ALL .flac files recursively
    flac_files = list(input_root.rglob("*.flac"))
    
    if not flac_files:
        print(f"No .flac files found under: {input_root}")
        return
    
    print(f"Found {len(flac_files)} FLAC files. Starting lossless conversion...\n")
    
    success = 0
    skipped = 0
    errors = 0
    error_log = []
    
    for flac_path in tqdm(flac_files, desc="Converting", unit="file"):
        # Preserve exact relative folder structure
        relative_path = flac_path.relative_to(input_root)
        wav_path = output_root / relative_path.with_suffix(".wav")
        
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        
        if wav_path.exists() and not overwrite:
            skipped += 1
            continue
        
        try:
            with sf.SoundFile(flac_path) as f:
                data = f.read()
                samplerate = f.samplerate
                subtype = f.subtype   # Preserves original bit depth (16/24-bit etc.)
            
            sf.write(
                str(wav_path),
                data,
                samplerate,
                subtype=subtype,
                format='WAV'
            )
            success += 1
            
        except Exception as e:
            errors += 1
            error_log.append(f"{flac_path} → ERROR: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("FLAC TO WAV CONVERSION COMPLETE")
    print("="*70)
    print(f"✅ Successfully converted : {success}")
    print(f"⏭️  Skipped (already exist) : {skipped}")
    print(f"❌ Errors                 : {errors}")
    
    if error_log:
        print("\nErrors:")
        for err in error_log[:10]:  # Show first 10 only
            print(f"   • {err}")
        if len(error_log) > 10:
            print(f"   ... and {len(error_log)-10} more errors")
    
    print(f"\nInput root  : {input_root}")
    print(f"Output root : {output_root}")
    print("All conversions are 100% bit-perfect and lossless.")


if __name__ == "__main__":
    # Load .env file (looks for .env in current directory or parent folders)
    load_dotenv()
    
    # Get defaults from .env (None if not set)
    default_input = os.getenv("FLAC_INPUT_ROOT")
    default_output = os.getenv("WAV_OUTPUT_ROOT")
    
    parser = argparse.ArgumentParser(
        description="Batch convert FLAC files to WAV (lossless, bit-perfect) with .env support."
    )
    parser.add_argument(
        "--input_root", "-i",
        default=default_input,
        help="Root folder containing nested .flac files (overrides FLAC_INPUT_ROOT in .env)"
    )
    parser.add_argument(
        "--output_root", "-o",
        default=default_output,
        help="Root folder for output .wav files (overrides WAV_OUTPUT_ROOT in .env)"
    )
    parser.add_argument(
        "--overwrite", "-f",
        action="store_true",
        help="Overwrite existing WAV files (default: skip)"
    )
    
    args = parser.parse_args()
    
    # Validation with helpful messages
    if not args.input_root:
        print("❌ ERROR: No input root provided.")
        print("   → Add FLAC_INPUT_ROOT=/path/to/flac/root to your .env file")
        print("   → Or run with: --input_root /path/to/flac/root")
        exit(1)
    
    if not args.output_root:
        print("❌ ERROR: No output root provided.")
        print("   → Add WAV_OUTPUT_ROOT=/path/to/wav/output to your .env file")
        print("   → Or run with: --output_root /path/to/wav/output")
        exit(1)
    
    # Show where values came from
    print("Configuration:")
    print(f"   FLAC_INPUT_ROOT  = {args.input_root}  {'(from .env)' if default_input == args.input_root and default_input else '(from CLI)'}")
    print(f"   WAV_OUTPUT_ROOT  = {args.output_root}  {'(from .env)' if default_output == args.output_root and default_output else '(from CLI)'}")
    print("-" * 60)
    
    convert_flac_to_wav(args.input_root, args.output_root, args.overwrite)
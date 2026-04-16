"""
AUDIO DIAGNOSIS SCRIPT - Recursive Search
=========================================
Now searches recursively through all subfolders in DIAGNOSE_SOURCE.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import csv
from tqdm import tqdm
from pydub import AudioSegment

# ========================== LOAD PATHS FROM .env ==========================
load_dotenv()

DIAGNOSE_LIST   = os.getenv("DIAGNOSE_LIST")
DIAGNOSE_SOURCE = os.getenv("DIAGNOSE_SOURCE")
DIAGNOSE_OUTPUT = os.getenv("DIAGNOSE_OUTPUT")

# Fallbacks
if not DIAGNOSE_LIST:
    DIAGNOSE_LIST = r"C:\Users\patty\miniconda3\Scripts\music-download\Diagnose_List.txt"
if not DIAGNOSE_SOURCE:
    DIAGNOSE_SOURCE = r"E:\aadamjacobs\Originals\WAV"
if not DIAGNOSE_OUTPUT:
    DIAGNOSE_OUTPUT = r"C:\Users\patty\miniconda3\Scripts\music-download\Reports"

print("Configuration:")
print(f"   DIAGNOSE_LIST   = {DIAGNOSE_LIST}")
print(f"   DIAGNOSE_SOURCE = {DIAGNOSE_SOURCE}  (recursive search)")
print(f"   DIAGNOSE_OUTPUT = {DIAGNOSE_OUTPUT}")
print("-" * 60)

Path(DIAGNOSE_OUTPUT).mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_csv = Path(DIAGNOSE_OUTPUT) / f"Diagnosis_Report_{timestamp}.csv"
report_txt = Path(DIAGNOSE_OUTPUT) / f"Diagnosis_Summary_{timestamp}.txt"


def find_wav_file(filename: str, source_root: Path):
    """Search recursively for a WAV file by stem name."""
    stem = Path(filename).stem.lower()
    for ext in [".wav", ".WAV"]:
        for found_file in source_root.rglob(f"*{ext}"):
            if found_file.stem.lower() == stem:
                return found_file
    return None


def analyze_wav(file_path: str):
    try:
        audio = AudioSegment.from_file(file_path, format="wav")
        return {
            "filename": Path(file_path).name,
            "full_path": str(file_path),
            "exists": True,
            "duration_seconds": round(len(audio) / 1000, 3),
            "sample_rate": audio.frame_rate,
            "channels": audio.channels,
            "bit_depth": audio.sample_width * 8,
            "file_size_mb": round(Path(file_path).stat().st_size / (1024 * 1024), 3),
            "peak_dBFS": round(audio.max_dBFS, 2),
            "rms_dBFS": round(audio.rms / 32768 * 100, 2) if audio.rms else -60,
            "error": ""
        }
    except Exception as e:
        return {
            "filename": Path(file_path).name,
            "full_path": str(file_path),
            "exists": False,
            "duration_seconds": "",
            "sample_rate": "",
            "channels": "",
            "bit_depth": "",
            "file_size_mb": "",
            "peak_dBFS": "",
            "rms_dBFS": "",
            "error": str(e)
        }


def main():
    print("=" * 80)
    print("AUDIO DIAGNOSIS TOOL - Recursive Search")
    print("=" * 80)

    if not os.path.exists(DIAGNOSE_LIST):
        print(f"Error: List file not found -> {DIAGNOSE_LIST}")
        return

    with open(DIAGNOSE_LIST, "r", encoding="utf-8") as f:
        file_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"Loaded {len(file_list)} files to diagnose.\n")

    fieldnames = [
        "filename", "full_path", "exists", "duration_seconds", "sample_rate",
        "channels", "bit_depth", "file_size_mb", "peak_dBFS", "rms_dBFS", "error"
    ]

    results = []
    missing_files = 0
    source_root = Path(DIAGNOSE_SOURCE)

    for filename in tqdm(file_list, desc="Searching & Diagnosing"):
        wav_file = find_wav_file(filename, source_root)

        if wav_file and wav_file.exists():
            result = analyze_wav(str(wav_file))
            results.append(result)
        else:
            missing_files += 1
            results.append({
                "filename": filename,
                "full_path": "NOT FOUND",
                "exists": False,
                "duration_seconds": "",
                "sample_rate": "",
                "channels": "",
                "bit_depth": "",
                "file_size_mb": "",
                "peak_dBFS": "",
                "rms_dBFS": "",
                "error": "File not found in DIAGNOSE_SOURCE or any subfolder"
            })

    # Write CSV report
    with open(report_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    # Write summary
    with open(report_txt, "w", encoding="utf-8") as f:
        f.write(f"Audio Diagnosis Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total files in list : {len(file_list)}\n")
        f.write(f"Files found         : {len([r for r in results if r.get('exists')])}\n")
        f.write(f"Files missing       : {missing_files}\n\n")

        for r in results:
            if r.get("exists"):
                f.write(f"OK   {r['filename']}\n")
                f.write(f"     Duration : {r['duration_seconds']}s | "
                        f"Channels : {r['channels']} | "
                        f"Sample Rate : {r['sample_rate']} Hz\n")
                f.write(f"     Peak     : {r['peak_dBFS']} dBFS | "
                        f"RMS : {r['rms_dBFS']} dBFS\n\n")
            else:
                f.write(f"NOT FOUND   {r['filename']} -> {r.get('error')}\n\n")

    print("\nDiagnosis complete!")
    print(f"   CSV Report  -> {report_csv.name}")
    print(f"   Summary     -> {report_txt.name}")
    print(f"   Total files diagnosed: {len(results)}")


if __name__ == "__main__":
    main()
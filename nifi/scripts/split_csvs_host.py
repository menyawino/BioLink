#!/usr/bin/env python3
"""Split BHS and EHVol CSV files into smaller chunks for NiFi processing."""
import csv
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SOURCE_DIR = os.path.join(PROJECT_ROOT, "db")
OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "data-input")
CHUNK_SIZE = 25  # rows per chunk

def split_csv(filepath, chunk_size=CHUNK_SIZE):
    """Split a CSV file into chunks, preserving the header."""
    basename = os.path.splitext(os.path.basename(filepath))[0]
    
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        
        chunk_num = 0
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) >= chunk_size:
                chunk_num += 1
                outpath = os.path.join(OUTPUT_DIR, f"{basename}_chunk_{chunk_num:04d}.csv")
                with open(outpath, "w", newline="", encoding="utf-8") as out:
                    writer = csv.writer(out)
                    writer.writerow(header)
                    writer.writerows(rows)
                rows = []
        
        # Write remaining rows
        if rows:
            chunk_num += 1
            outpath = os.path.join(OUTPUT_DIR, f"{basename}_chunk_{chunk_num:04d}.csv")
            with open(outpath, "w", newline="", encoding="utf-8") as out:
                writer = csv.writer(out)
                writer.writerow(header)
                writer.writerows(rows)
    
    return chunk_num

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Clear any existing chunks
for f in os.listdir(OUTPUT_DIR):
    if f.endswith(".csv"):
        os.remove(os.path.join(OUTPUT_DIR, f))

# Process both datasets
for csv_file in ["BHS_Full.csv", "EHVol_Full.csv"]:
    path = os.path.join(SOURCE_DIR, csv_file)
    if os.path.exists(path):
        chunks = split_csv(path)
        print(f"Split {csv_file} into {chunks} chunks of {CHUNK_SIZE} rows each")
    else:
        print(f"WARNING: {path} not found")

# List resulting files
files = sorted(os.listdir(OUTPUT_DIR))
print(f"\nTotal chunk files: {len(files)}")
for f in files[:5]:
    size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
    print(f"  {f} ({size:,} bytes)")
if len(files) > 10:
    print(f"  ... ({len(files)-5} more files)")

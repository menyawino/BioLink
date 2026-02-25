#!/usr/bin/env python3
"""
stage_nifi_chunks.py — Split source CSVs into 500-row chunks
for NiFi GetFile ingestion.

Usage:
    python3 scripts/stage_nifi_chunks.py

Clears any existing chunks from nifi/data-input/ first to prevent
duplicate ingestion on re-runs (NiFi uses ON CONFLICT DO NOTHING).

Host-mount: ./nifi/data-input → /opt/nifi/data-input inside the NiFi container.
NiFi GetFile processors are configured to read from /opt/nifi/data-input.
"""
import csv
import os
import glob
import sys

CHUNK_SIZE = 500
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "nifi", "data-input")

SOURCES = [
    (os.path.join(BASE, "db", "BHS_Full.csv"),  "BHS_Full"),
    (os.path.join(BASE, "db", "EHVol_Full.csv"), "EHVol_Full"),
]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Clear existing chunks to avoid duplicates
    removed = 0
    for f in glob.glob(os.path.join(OUT_DIR, "*.csv")):
        os.remove(f)
        removed += 1
    if removed:
        print(f"Removed {removed} existing chunk files from {OUT_DIR}")

    total_chunks = 0
    total_rows = 0

    for src_path, prefix in SOURCES:
        if not os.path.exists(src_path):
            print(f"WARNING: {src_path} not found, skipping", file=sys.stderr)
            continue

        print(f"\nProcessing {os.path.basename(src_path)} ...")
        with open(src_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            chunk_num = 0
            rows = []
            for row in reader:
                rows.append(row)
                if len(rows) == CHUNK_SIZE:
                    chunk_num += 1
                    _write_chunk(OUT_DIR, prefix, chunk_num, header, rows)
                    total_rows += len(rows)
                    rows = []
            if rows:
                chunk_num += 1
                _write_chunk(OUT_DIR, prefix, chunk_num, header, rows)
                total_rows += len(rows)
        total_chunks += chunk_num

    print(f"\n{total_chunks} chunk files staged in {OUT_DIR} ({total_rows} total data rows)")
    print("NiFi GetFile processors will consume these automatically.")

def _write_chunk(out_dir, prefix, chunk_num, header, rows):
    path = os.path.join(out_dir, f"{prefix}_chunk_{chunk_num:03d}.csv")
    with open(path, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {os.path.basename(path)}  ({len(rows)} rows)")

if __name__ == "__main__":
    main()

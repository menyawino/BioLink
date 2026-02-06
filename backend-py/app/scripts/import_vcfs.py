from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text

from app.database import engine


def _parse_info(info_str: str) -> Dict[str, str]:
    info: Dict[str, str] = {}
    for part in info_str.split(";"):
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            info[key] = value
        else:
            info[part] = "true"
    return info


def _extract_gene(info: Dict[str, str]) -> Optional[str]:
    if "GENE" in info:
        return info["GENE"]
    if "ANN" in info:
        # ANN format is typically: Allele|Annotation|Impact|Gene_Name|...
        ann_entry = info["ANN"].split(",", 1)[0]
        ann_fields = ann_entry.split("|")
        if len(ann_fields) > 3 and ann_fields[3]:
            return ann_fields[3]
    return None


def _parse_vcf_line(line: str) -> Optional[Dict[str, Optional[str]]]:
    if line.startswith("#"):
        return None
    parts = line.strip().split("\t")
    if len(parts) < 8:
        return None

    chrom, pos, variant_id, ref, alt, qual, filt, info_str = parts[:8]
    fmt = parts[8] if len(parts) > 8 else None
    sample = parts[9] if len(parts) > 9 else None

    info = _parse_info(info_str)
    gene = _extract_gene(info)
    genotype = None
    if fmt and sample:
        fmt_keys = fmt.split(":")
        sample_vals = sample.split(":")
        fmt_map = dict(zip(fmt_keys, sample_vals))
        genotype = fmt_map.get("GT")

    return {
        "chrom": chrom,
        "pos": pos,
        "variant_id": None if variant_id == "." else variant_id,
        "ref": ref,
        "alt": alt,
        "gene": gene,
        "genotype": genotype,
        "clinical_significance": info.get("CLNSIG"),
        "condition": info.get("COND") or info.get("DISEASE"),
        "frequency": info.get("AF"),
    }


def _load_vcf(path: Path) -> List[Dict[str, Optional[str]]]:
    variants: List[Dict[str, Optional[str]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            parsed = _parse_vcf_line(line)
            if parsed:
                variants.append(parsed)
    return variants


def _upsert_variants(dna_id: str, vcf_path: Path, variants: List[Dict[str, Optional[str]]], replace: bool) -> Tuple[int, int]:
    inserted = 0
    skipped = 0

    with engine.begin() as conn:
        if replace:
            conn.execute(
                text("DELETE FROM patient_genomic_variants WHERE dna_id = :dna_id"),
                {"dna_id": dna_id}
            )

        for variant in variants:
            params = {
                "dna_id": dna_id,
                "chrom": variant["chrom"],
                "pos": int(variant["pos"]) if variant["pos"] else None,
                "ref": variant["ref"],
                "alt": variant["alt"],
                "variant_id": variant["variant_id"],
                "gene": variant["gene"],
                "genotype": variant["genotype"],
                "clinical_significance": variant["clinical_significance"],
                "condition": variant["condition"],
                "frequency": float(variant["frequency"]) if variant["frequency"] else None,
                "source_vcf": vcf_path.name,
            }

            result = conn.execute(
                text(
                    """
                    INSERT INTO patient_genomic_variants (
                        dna_id, chrom, pos, ref, alt, variant_id, gene, genotype,
                        clinical_significance, condition, frequency, source_vcf
                    ) VALUES (
                        :dna_id, :chrom, :pos, :ref, :alt, :variant_id, :gene, :genotype,
                        :clinical_significance, :condition, :frequency, :source_vcf
                    )
                    ON CONFLICT (dna_id, chrom, pos, ref, alt, genotype) DO NOTHING
                    """
                ),
                params,
            )
            if result.rowcount and result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

    return inserted, skipped


def _patient_exists(dna_id: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT 1 FROM patients WHERE dna_id = :dna_id"),
            {"dna_id": dna_id}
        ).fetchone()
    return bool(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import mock VCFs into patient_genomic_variants by MRN (dna_id).")
    default_vcf_dir = Path(__file__).resolve().parents[2] / "data" / "vcfs"
    parser.add_argument("--vcf-dir", type=Path, default=default_vcf_dir, help="Directory containing VCF files")
    parser.add_argument("--replace", action="store_true", help="Replace existing variants for a patient")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report without inserting")
    args = parser.parse_args()

    vcf_dir = args.vcf_dir
    if not vcf_dir.exists():
        raise SystemExit(f"VCF directory not found: {vcf_dir}")

    vcf_paths = sorted(list(vcf_dir.glob("*.vcf")))
    if not vcf_paths:
        print(f"No VCF files found in {vcf_dir}")
        return 0

    total_inserted = 0
    total_skipped = 0
    for vcf_path in vcf_paths:
        dna_id = vcf_path.stem
        if not _patient_exists(dna_id):
            print(f"Skipping {vcf_path.name}: dna_id '{dna_id}' not found in patients table")
            continue

        variants = _load_vcf(vcf_path)
        if args.dry_run:
            print(f"{vcf_path.name}: {len(variants)} variants parsed (dry-run)")
            continue

        inserted, skipped = _upsert_variants(dna_id, vcf_path, variants, args.replace)
        total_inserted += inserted
        total_skipped += skipped
        print(f"{vcf_path.name}: inserted {inserted}, skipped {skipped}")

    if not args.dry_run:
        print(f"Total inserted: {total_inserted}, total skipped: {total_skipped}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

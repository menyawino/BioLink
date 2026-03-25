#!/usr/bin/env python3
"""
STEP 3: Convert unified_registry.csv into OMOP-style CDM extracts.

Input:
  - outputs/unified_registry.csv
  - outputs/master_schema.csv (optional but recommended; used for omop_domain + vocab hints)

Output directory (default: outputs/omop_cdm):
  - person.(parquet|csv)
  - measurement.(parquet|csv)
  - condition_occurrence.(parquet|csv)
  - observation.(parquet|csv)
  - manifest.json

Notes
-----
This is a pragmatic OMOP bootstrap ETL for registry harmonization. It preserves
source values and emits OMOP-like tables with source concepts so you can later
refine concept mapping (e.g., Usagi/WhiteRabbit + Athena vocabularies).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


TRUTHY = {"1", "true", "yes", "y", "t", "positive"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OMOP-style tables from unified registry")
    parser.add_argument(
        "--unified",
        type=Path,
        default=Path("outputs/unified_registry.csv"),
        help="Path to unified_registry.csv",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("outputs/master_schema.csv"),
        help="Path to master_schema.csv (for omop_domain + standard_vocab)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/omop_cdm"),
        help="Directory where OMOP tables are written",
    )
    parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Preferred output format (falls back to CSV if parquet engine missing)",
    )
    return parser.parse_args()


def _safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _gender_concept_id(value: str) -> int:
    v = str(value).strip().lower()
    if v in {"m", "male"}:
        return 8507
    if v in {"f", "female"}:
        return 8532
    return 0


def _pick_first_existing(columns: List[str], candidates: List[str]) -> Optional[str]:
    cols = set(columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def _infer_person_key(row: pd.Series, key_cols: List[str], row_idx: int) -> str:
    for col in key_cols:
        val = row.get(col)
        if pd.notna(val) and str(val).strip() != "":
            return str(val).strip()
    payload = "|".join([str(row.get(c, "")) for c in sorted(row.index)])
    digest = hashlib.sha1(f"{row_idx}|{payload}".encode("utf-8")).hexdigest()[:16]
    return f"gen_{digest}"


def _read_schema(path: Path, registry_cols: List[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            {
                "master_col": registry_cols,
                "omop_domain": ["observation"] * len(registry_cols),
                "standard_vocab": [""] * len(registry_cols),
                "pii_flag": [False] * len(registry_cols),
            }
        )

    schema = pd.read_csv(path)
    required = {"master_col", "omop_domain", "standard_vocab", "pii_flag"}
    for missing in required - set(schema.columns):
        if missing == "pii_flag":
            schema[missing] = False
        else:
            schema[missing] = ""

    schema = schema[["master_col", "omop_domain", "standard_vocab", "pii_flag"]].copy()
    schema["master_col"] = schema["master_col"].astype(str)
    schema = schema[schema["master_col"].isin(registry_cols)]

    missing_cols = sorted(set(registry_cols) - set(schema["master_col"]))
    if missing_cols:
        pad = pd.DataFrame(
            {
                "master_col": missing_cols,
                "omop_domain": ["observation"] * len(missing_cols),
                "standard_vocab": [""] * len(missing_cols),
                "pii_flag": [False] * len(missing_cols),
            }
        )
        schema = pd.concat([schema, pad], ignore_index=True)

    return schema


def _build_person(unified: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    key_candidates = [
        "participant_id",
        "patient_id",
        "record_id",
        "mrn",
        "subject_id",
    ]
    key_cols = [c for c in key_candidates if c in unified.columns]

    person_source_values: List[str] = []
    for idx, row in unified.iterrows():
        person_source_values.append(_infer_person_key(row, key_cols, idx))

    person_source = pd.Series(person_source_values, index=unified.index, name="person_source_value")
    person_id_map = {v: i + 1 for i, v in enumerate(person_source.unique())}
    person_ids = person_source.map(person_id_map).astype("int64")

    dob_col = _pick_first_existing(
        unified.columns.tolist(),
        ["date_of_birth", "birth_date", "dob"],
    )
    age_col = _pick_first_existing(unified.columns.tolist(), ["age", "age_at_enrollment"])
    gender_col = _pick_first_existing(unified.columns.tolist(), ["gender", "sex"])

    if dob_col:
        dob = _safe_to_datetime(unified[dob_col])
        year_of_birth = dob.dt.year
        month_of_birth = dob.dt.month
        day_of_birth = dob.dt.day
        birth_datetime = dob
    else:
        year_of_birth = pd.Series(np.nan, index=unified.index)
        month_of_birth = pd.Series(np.nan, index=unified.index)
        day_of_birth = pd.Series(np.nan, index=unified.index)
        birth_datetime = pd.Series(pd.NaT, index=unified.index)

        if age_col:
            age_num = pd.to_numeric(unified[age_col], errors="coerce")
            inferred_year = (pd.Timestamp.today().year - age_num).round().astype("Int64")
            year_of_birth = inferred_year

    gender_source = unified[gender_col].astype(str) if gender_col else pd.Series("", index=unified.index)
    gender_concept = gender_source.map(_gender_concept_id).fillna(0).astype("int64")

    person = pd.DataFrame(
        {
            "person_id": person_ids,
            "gender_concept_id": gender_concept,
            "year_of_birth": year_of_birth,
            "month_of_birth": month_of_birth,
            "day_of_birth": day_of_birth,
            "birth_datetime": birth_datetime,
            "race_concept_id": 0,
            "ethnicity_concept_id": 0,
            "person_source_value": person_source,
            "gender_source_value": gender_source,
        }
    )

    person = person.drop_duplicates(subset=["person_id"], keep="first").reset_index(drop=True)
    return person, person_ids


def _to_long_domain(
    unified: pd.DataFrame,
    person_ids: pd.Series,
    schema: pd.DataFrame,
    domain: str,
) -> pd.DataFrame:
    rows: List[Dict] = []

    domain_schema = schema[
        (schema["omop_domain"].astype(str).str.lower() == domain.lower())
        & (~schema["pii_flag"].astype(bool))
    ].copy()

    if domain_schema.empty:
        return pd.DataFrame()

    date_col = _pick_first_existing(unified.columns.tolist(), ["encounter_date", "visit_date", "date", "ecg_date", "echo_date", "mri_date"])

    for _, srow in domain_schema.iterrows():
        col = srow["master_col"]
        if col not in unified.columns:
            continue

        concept_src = str(srow.get("standard_vocab", "") or "").strip()
        series = unified[col]

        num = pd.to_numeric(series, errors="coerce")
        is_numeric = num.notna().mean() > 0.70

        for idx, raw in series.items():
            if pd.isna(raw) or str(raw).strip() == "":
                continue

            person_id = int(person_ids.loc[idx])
            obs_date = pd.NaT
            if date_col:
                obs_date = _safe_to_datetime(pd.Series([unified.at[idx, date_col]])).iloc[0]

            row = {
                "person_id": person_id,
                "source_field": col,
                "source_vocab": concept_src,
                "source_value": str(raw),
                "event_date": obs_date.date().isoformat() if pd.notna(obs_date) else None,
            }

            if domain == "measurement":
                row["value_as_number"] = float(num.loc[idx]) if pd.notna(num.loc[idx]) else np.nan
                row["value_as_string"] = None if pd.notna(num.loc[idx]) else str(raw)
                rows.append(row)
            elif domain == "condition_occurrence":
                raw_s = str(raw).strip().lower()
                if is_numeric:
                    val = pd.to_numeric(pd.Series([raw]), errors="coerce").iloc[0]
                    if pd.isna(val) or float(val) <= 0:
                        continue
                else:
                    if raw_s not in TRUTHY and raw_s not in {"diagnosed", "present", "yes", "y"}:
                        if raw_s in {"0", "false", "no", "n", "negative", "absent"}:
                            continue
                rows.append(row)
            elif domain == "observation":
                rows.append(row)

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    out.insert(0, f"{domain}_id", range(1, len(out) + 1))
    return out


def _write_table(df: pd.DataFrame, base_path: Path, preferred_format: str) -> str:
    base_path.parent.mkdir(parents=True, exist_ok=True)

    if preferred_format == "parquet":
        try:
            df.to_parquet(base_path.with_suffix(".parquet"), index=False)
            return "parquet"
        except Exception:
            df.to_csv(base_path.with_suffix(".csv"), index=False)
            return "csv"

    df.to_csv(base_path.with_suffix(".csv"), index=False)
    return "csv"


def main() -> None:
    args = _parse_args()

    if not args.unified.exists():
        raise FileNotFoundError(f"Unified registry not found: {args.unified}")

    unified = pd.read_csv(args.unified, dtype=str, low_memory=False)
    schema = _read_schema(args.schema, unified.columns.tolist())

    person, person_ids = _build_person(unified)
    measurement = _to_long_domain(unified, person_ids, schema, "measurement")
    condition = _to_long_domain(unified, person_ids, schema, "condition_occurrence")
    observation = _to_long_domain(unified, person_ids, schema, "observation")

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    fmt_person = _write_table(person, out_dir / "person", args.format)
    fmt_meas = _write_table(measurement, out_dir / "measurement", args.format)
    fmt_cond = _write_table(condition, out_dir / "condition_occurrence", args.format)
    fmt_obs = _write_table(observation, out_dir / "observation", args.format)

    manifest = {
        "input_unified": str(args.unified),
        "input_schema": str(args.schema),
        "row_counts": {
            "person": int(len(person)),
            "measurement": int(len(measurement)),
            "condition_occurrence": int(len(condition)),
            "observation": int(len(observation)),
        },
        "formats": {
            "person": fmt_person,
            "measurement": fmt_meas,
            "condition_occurrence": fmt_cond,
            "observation": fmt_obs,
        },
    }

    with (out_dir / "manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[omop_etl] Wrote OMOP extracts to: {out_dir}")
    print(json.dumps(manifest["row_counts"], indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
NiFi processor integration tests — runs inside or outside the NiFi container.

Usage (inside container):
  python3 /tmp/test_nifi.py

Usage (local, with pipeline on path):
    python3 nifi/pipeline/_test_nifi_processors.py
"""
from __future__ import annotations
import sys, os, csv, math, importlib.util, tempfile
from pathlib import Path

# Suppress pandas FutureWarnings and similar noise
import warnings; warnings.filterwarnings("ignore")

SCRIPTS = Path(os.environ.get("BIOLINK_SCRIPTS", Path(__file__).parent))
sys.path.insert(0, str(SCRIPTS))

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
_errors: list[str] = []

def ok(msg: str) -> None:
    print(f"  {PASS} {msg}")

def fail(msg: str) -> None:
    print(f"  {FAIL} {msg}")
    _errors.append(msg)

def section(title: str) -> None:
    print(f"\n{'='*60}\n{title}\n{'='*60}")

# ─────────────────────────────────────────────────────────────────────────────
# 1. two_stage_match.py — core matching logic
# ─────────────────────────────────────────────────────────────────────────────
section("1. two_stage_match — string helpers + candidate generation")

spec = importlib.util.spec_from_file_location("tsm", SCRIPTS / "two_stage_match.py")
tsm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tsm)

cases_snake = [
    ("Heart Rate (BPM)",   "heart_rate_bpm"),
    ("HbA1c",              "hba1c"),
    ("LV EDD",             "lv_edd"),
    ("  Systolic BP  ",    "systolic_bp"),
    ("It's a test!",       "its_a_test"),
]
for raw, expected in cases_snake:
    got = tsm.to_snake(raw)
    if got == expected:
        ok(f"to_snake({raw!r}) = {got!r}")
    else:
        fail(f"to_snake({raw!r}): expected {expected!r}, got {got!r}")

expanded = tsm.expand_name("bmi")
if "body" in expanded or "bmi" in expanded:
    ok(f"expand_name('bmi') = {expanded!r}")
else:
    fail(f"expand_name('bmi') unexpected: {expanded!r}")

cols_a = ["heart_rate", "bmi", "systolic_blood_pressure", "ecg_date", "lvedd"]
cols_b = ["hr",          "body_mass_index", "sbp",                    "ecg_date", "lv_edd"]
candidates = tsm.stage1_candidates(cols_a, cols_b, top_k=3, threshold=0.10)
print(f"\n  stage1_candidates ({len(cols_a)} cols each) → {len(candidates)} candidates:")
for ca, cb, sc in candidates:
    print(f"    {ca:35s} ↔  {cb:25s}  score={sc:.3f}")
if len(candidates) >= 2:
    ok(f"stage1_candidates returned {len(candidates)} pairs (≥2 expected)")
else:
    fail(f"Too few candidates: {len(candidates)}")

# Test full stage2_validate + generate_master_schema API
section("2. two_stage_match — stage2_validate + generate_master_schema API")

import pandas as pd

BHS_COLS   = ["heart_rate", "bmi", "ecg_date", "only_in_bhs"]
EHVOL_COLS = ["heart_rate", "bmi", "ecg_date", "only_in_ehvol"]

# Build tiny DataFrames that mirror real data formats
df_a = pd.DataFrame({
    "heart_rate":  [72, 80, 75],
    "bmi":         [25.1, 28.0, 22.5],
    "ecg_date":    ["2021-01-01", "2021-02-01", "2021-03-01"],
    "only_in_bhs": ["foo", "bar", "baz"],
})
df_b = pd.DataFrame({
    "heart_rate":   [75, 82, 68],
    "bmi":          [26.3, 30.1, 21.0],
    "ecg_date":     ["2021-01-02", "2021-02-02", "2021-03-02"],
    "only_in_ehvol": ["qux", "quux", "corge"],
})

# stage1_candidates with low threshold so exact names pair
candidates_s2 = tsm.stage1_candidates(
    names_a=BHS_COLS, names_b=EHVOL_COLS,
    threshold=0.10, top_k=5,
)
print(f"  Stage 1 candidates: {len(candidates_s2)}")

# stage2_validate — use n_boot=0 and min_final_score=0.0 to force acceptance
try:
    results = tsm.stage2_validate(
        candidates_s2,
        df_a[["heart_rate","bmi","ecg_date","only_in_bhs"]],
        df_b[["heart_rate","bmi","ecg_date","only_in_ehvol"]],
        n_boot=0,
        min_final_score=0.0,
    )
    accepted = [r for r in results if r["verdict"] == "ACCEPTED"]
    print(f"  stage2_validate: {len(results)} results, {len(accepted)} accepted")
    ok(f"stage2_validate returned {len(results)} results")
except Exception as exc:
    fail(f"stage2_validate raised {exc}")
    results, accepted = [], []

with tempfile.TemporaryDirectory() as td:
    master_out   = Path(td) / "master_schema.csv"
    accepted_rows = []
    for col in ("heart_rate", "bmi", "ecg_date"):
        accepted_rows.append({
            "name_a": col,
            "category_a": "vitals",
            "name_b": col,
            "category_b": "vitals",
            "name_score": 1.0,
            "type_a": "numeric",
            "type_b": "numeric",
            "range_score": 1.0,
            "range_ci_low": 0.9,
            "range_ci_high": 1.0,
            "cat_overlap": None,
            "final_score": 1.0,
        })

    try:
        tsm.generate_master_schema(
            accepted_rows,
            output_path=master_out,
            all_cols_a=BHS_COLS,
            all_cols_b=EHVOL_COLS,
        )
        ok("generate_master_schema completed without error")
    except Exception as exc:
        fail(f"generate_master_schema raised {exc}")

    if master_out.exists():
        rows_out = list(csv.DictReader(master_out.open()))
        print(f"  master_schema.csv: {len(rows_out)} rows")

        exact_paired = [r for r in rows_out
                        if r.get("source_a_cols","").strip() == r.get("source_b_cols","").strip()
                        and r.get("source_a_cols","").strip() in ("heart_rate", "bmi", "ecg_date")]
        if len(exact_paired) >= 2:
            ok(f"Exact-name columns paired: {[r['master_col'] for r in exact_paired]}")
        else:
            fail(f"Exact-name pairing: expected ≥2, got {len(exact_paired)}")

        only_bhs   = [r for r in rows_out
                      if r.get("source_a_cols","").strip() == "only_in_bhs"
                      and not r.get("source_b_cols","").strip()]
        only_ehvol = [r for r in rows_out
                      if r.get("source_b_cols","").strip() == "only_in_ehvol"
                      and not r.get("source_a_cols","").strip()]
        ok(f"BHS-only passthrough: {only_bhs[0]['master_col']}") if only_bhs else fail("only_in_bhs missing")
        ok(f"EHVol-only passthrough: {only_ehvol[0]['master_col']}") if only_ehvol else fail("only_in_ehvol missing")
    else:
        fail("master_schema.csv not created")

# ─────────────────────────────────────────────────────────────────────────────
# 3. apply_schema.py — _load_csv, process_dataset, PII drop
# ─────────────────────────────────────────────────────────────────────────────
section("3. apply_schema — _load_csv + process_dataset + PII drop")

spec2 = importlib.util.spec_from_file_location("aps", SCRIPTS / "apply_schema.py")
aps = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(aps)

with tempfile.TemporaryDirectory() as td:
    # Mini BHS CSV
    bhs_path = os.path.join(td, "bhs.csv")
    with open(bhs_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["heart_rate", "bmi",  "full_name", "ecg_date"])
        w.writerow(["72",         "25.1", "Alice",     "2021-01-01"])
        w.writerow(["80",         "28.0", "Bob",       "2021-02-01"])

    df = aps._load_csv(bhs_path)
    if df.shape == (2, 4):
        ok(f"_load_csv: {df.shape[0]} rows × {df.shape[1]} cols")
    else:
        fail(f"_load_csv unexpected shape: {df.shape}")

    # Master schema for the mini BHS
    ehvol_path = os.path.join(td, "ehvol.csv")
    with open(ehvol_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["heart_rate", "bmi"])
        w.writerow(["75",         "26.3"])

    schema_path = os.path.join(td, "master.csv")
    schema_rows = [
        {"master_col": "heart_rate", "source_a_cols": "heart_rate", "source_b_cols": "heart_rate",
         "category": "vitals", "final_score": "1.0", "coalesce_strategy": "mean_value", "pii_flag": "False"},
        {"master_col": "bmi",        "source_a_cols": "bmi",        "source_b_cols": "bmi",
         "category": "vitals", "final_score": "1.0", "coalesce_strategy": "mean_value", "pii_flag": "False"},
        {"master_col": "full_name",  "source_a_cols": "full_name",  "source_b_cols": "",
         "category": "contact", "final_score": "0.0", "coalesce_strategy": "first_non_null", "pii_flag": "True"},
        {"master_col": "ecg_date",   "source_a_cols": "ecg_date",   "source_b_cols": "",
         "category": "ecg", "final_score": "0.0", "coalesce_strategy": "first_non_null", "pii_flag": "False"},
    ]
    with open(schema_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(schema_rows[0].keys()))
        w.writeheader()
        w.writerows(schema_rows)

    out_path = os.path.join(td, "registry.csv")
    prov_path = os.path.join(td, "prov.csv")
    venn_path = os.path.join(td, "column_alignment_venn.png")
    _saved_argv = sys.argv[:]
    sys.argv = [
        "apply_schema.py",
        schema_path, bhs_path, ehvol_path,
        "--output", out_path,
        "--provenance-output", prov_path,
        "--venn-output", venn_path,
        "--drop-empty-cols",
    ]
    try:
        aps.main()
    finally:
        sys.argv = _saved_argv

    if os.path.exists(venn_path):
        ok("Venn chart written to test temp directory")
    else:
        fail("Venn chart was not created in test temp directory")

    with open(out_path) as f:
        registry = list(csv.DictReader(f))
    cols_out = list(registry[0].keys()) if registry else []
    print(f"  Output columns: {cols_out}")
    if "full_name" not in cols_out:
        ok("PII column 'full_name' correctly dropped")
    else:
        fail("PII column 'full_name' still present in output")
    if "heart_rate" in cols_out:
        ok(f"'heart_rate' present in output ({len(registry)} rows)")
    else:
        fail("'heart_rate' missing from output")

# ─────────────────────────────────────────────────────────────────────────────
# 4. BiolinkMasterSchemaProcessor — embedded helper functions (NiFi proc file)
# ─────────────────────────────────────────────────────────────────────────────
section("4. BiolinkMasterSchemaProcessor — embedded helper parity check")

PROC_DIR = Path("/opt/nifi/nifi-python-extensions/extensions")
if not PROC_DIR.exists():
    # Running locally — use source tree
    PROC_DIR = Path(__file__).resolve().parents[1] / "processors"

proc_path = PROC_DIR / "BiolinkMasterSchemaProcessor.py"
if proc_path.exists():
    # Mock nifiapi so the processor module loads outside a NiFi JVM
    import types, sys as _sys

    class _Stub:
        """Accept any constructor args — used to stub NiFi API classes."""
        def __init__(self, *a, **kw): pass

    for _mod in ("nifiapi", "nifiapi.flowfiletransform", "nifiapi.properties"):
        if _mod not in _sys.modules:
            _sys.modules[_mod] = types.ModuleType(_mod)
    _sys.modules["nifiapi.flowfiletransform"].FlowFileTransform = _Stub
    _sys.modules["nifiapi.flowfiletransform"].FlowFileTransformResult = _Stub
    _pd = types.SimpleNamespace(
        PropertyDescriptor=_Stub,
        ExpressionLanguageScope=types.SimpleNamespace(
            NONE=None, FLOWFILE_ATTRIBUTES=None, VARIABLE_REGISTRY=None
        ),
    )
    _sys.modules["nifiapi.properties"] = _pd

    spec3 = importlib.util.spec_from_file_location("bms", proc_path)
    bms = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(bms)

    try:
        assert bms.to_snake("Heart Rate") == "heart_rate"
        ok("BiolinkMasterSchemaProcessor.to_snake() matches nifi/pipeline helper")
    except Exception as exc:
        fail(f"to_snake check: {exc}")

    try:
        assert bms.is_pii_column("full_name")
        assert not bms.is_pii_column("heart_rate")
        ok("BiolinkMasterSchemaProcessor.is_pii_column() correct")
    except Exception as exc:
        fail(f"is_pii_column check: {exc}")
else:
    print(f"  (skipped — {proc_path} not found; run inside NiFi container)")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
section("SUMMARY")
total = len(_errors)
if total == 0:
    print(f"  {PASS}  All tests passed.\n")
    sys.exit(0)
else:
    for e in _errors:
        print(f"  {FAIL}  {e}")
    print(f"\n  {total} test(s) FAILED.")
    sys.exit(1)

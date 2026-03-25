#!/usr/bin/env python3
"""
Generate PostgreSQL DDL and NiFi column-type maps from standardized_columns.csv.

Outputs:
  db/schema_standardized.sql          -- CREATE TABLE, _schema_registry DDL+INSERTs, VIEW
  nifi/processors/bhs_col_map.py      -- BHS column map imported directly by NiFi processor
  nifi/processors/ehvol_col_map.py    -- EHVol column map imported directly by NiFi processor

The _schema_registry table (populated inside schema_standardized.sql) is the
canonical, queryable store of all SDTM / LOINC / SNOMED / ICD-10 / UCUM mappings.
"""

import csv
import io
import os
import pathlib
import re
import pandas as pd

SDTM_DOMAINS = {
    "AE", "CM", "CO", "DM", "DS", "DV", "EG", "EX", "FA", "HO",
    "IE", "LB", "MH", "MI", "PC", "PE", "PP", "PR", "QS", "RELREC",
    "RP", "RS", "SC", "SE", "SG", "SU", "SV", "TA", "TE", "TI",
    "TS", "TV", "VS",
}

SDTM_VAR_RE = re.compile(r"^[A-Z0-9]{1,8}$")
LOINC_RE = re.compile(r"^\d{1,5}-\d$")
SNOMED_RE = re.compile(r"^\d{6,18}$")
ICD10_RE = re.compile(r"^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$")
UCUM_RE = re.compile(r"^[A-Za-z0-9\[\]\(\)\./_%\*\-]+$")
RXNORM_RE = re.compile(r"^\d+$")

LOINC_ALLOWED_DOMAINS = {"DM", "LB", "VS", "EG", "FA", "PC"}
UCUM_ALLOWED_DOMAINS = {"DM", "CM", "LB", "VS", "EG", "FA", "PC", "EX"}
ICD10_ALLOWED_DOMAINS = {"AE", "DS", "HO", "MH"}
RXNORM_ALLOWED_DOMAINS = {"CM", "EX"}


def _clean_term_code(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan" or text.upper() == "NULL":
        return None
    if re.fullmatch(r"\d+\.0+", text):
        return text.split(".")[0]
    return text


def _is_valid_sdtm_domain(value: str | None) -> bool:
    return bool(value and value in SDTM_DOMAINS)


def _is_valid_sdtm_variable(value: str | None) -> bool:
    return bool(value and SDTM_VAR_RE.fullmatch(value))


def _is_valid_loinc(value: str | None) -> bool:
    return bool(value and LOINC_RE.fullmatch(value))


def _is_valid_snomed(value: str | None) -> bool:
    return bool(value and SNOMED_RE.fullmatch(value))


def _is_valid_icd10(value: str | None) -> bool:
    return bool(value and ICD10_RE.fullmatch(value))


def _is_valid_ucum(value: str | None) -> bool:
    return bool(value and UCUM_RE.fullmatch(value))


def _is_valid_rxnorm(value: str | None) -> bool:
    return bool(value and RXNORM_RE.fullmatch(value))


def _normalize_row(row: pd.Series):
    dataset = _clean_term_code(row.get("dataset"))
    original_name = _clean_term_code(row.get("original_name"))
    sql_type = _clean_term_code(row.get("sql_type")) or "TEXT"
    sdtm_domain = _clean_term_code(row.get("sdtm_domain"))
    sdtm_variable = _clean_term_code(row.get("sdtm_variable"))
    loinc_code = _clean_term_code(row.get("loinc_code"))
    snomed_code = _clean_term_code(row.get("snomed_code"))
    icd10_code = _clean_term_code(row.get("icd10_code"))
    ucum_unit = _clean_term_code(row.get("ucum_unit"))
    rxnorm_concept = _clean_term_code(row.get("rxnorm_concept"))

    normalized = {
        "dataset": dataset,
        "original_name": original_name,
        "sql_type": sql_type,
        "sdtm_domain": sdtm_domain,
        "sdtm_variable": sdtm_variable,
        "loinc_code": loinc_code,
        "snomed_code": snomed_code,
        "icd10_code": icd10_code,
        "ucum_unit": ucum_unit,
        "rxnorm_concept": rxnorm_concept,
        "mapping_method": _clean_term_code(row.get("mapping_method")),
        "confidence": _clean_term_code(row.get("confidence")),
    }
    return normalized


def _validate_normalized_row(normalized: dict):
    errors = []
    sdtm_domain = normalized.get("sdtm_domain")
    sdtm_variable = normalized.get("sdtm_variable")
    loinc_code = normalized.get("loinc_code")
    snomed_code = normalized.get("snomed_code")
    icd10_code = normalized.get("icd10_code")
    ucum_unit = normalized.get("ucum_unit")
    rxnorm_concept = normalized.get("rxnorm_concept")

    if sdtm_domain and not _is_valid_sdtm_domain(sdtm_domain):
        errors.append(f"Invalid SDTM domain: {sdtm_domain}")
    if sdtm_variable and not _is_valid_sdtm_variable(sdtm_variable):
        errors.append(f"Invalid SDTM variable: {sdtm_variable}")
    if loinc_code and not _is_valid_loinc(loinc_code):
        if _is_valid_snomed(loinc_code):
            errors.append(f"Invalid LOINC code (looks like SNOMED): {loinc_code}")
        else:
            errors.append(f"Invalid LOINC code: {loinc_code}")
    if snomed_code and not _is_valid_snomed(snomed_code):
        errors.append(f"Invalid SNOMED CT code: {snomed_code}")
    if icd10_code and not _is_valid_icd10(icd10_code):
        errors.append(f"Invalid ICD-10 code: {icd10_code}")
    if ucum_unit and not _is_valid_ucum(ucum_unit):
        errors.append(f"Invalid UCUM unit: {ucum_unit}")
    if rxnorm_concept and not _is_valid_rxnorm(rxnorm_concept):
        errors.append(f"Invalid RxNorm concept: {rxnorm_concept}")

    # Conservative semantic guards (domain/code consistency)
    if (loinc_code or snomed_code or icd10_code or ucum_unit or rxnorm_concept) and not sdtm_domain:
        errors.append("Terminology/code present without SDTM domain")
    if sdtm_domain and loinc_code and sdtm_domain not in LOINC_ALLOWED_DOMAINS:
        errors.append(f"LOINC used with unlikely SDTM domain: {sdtm_domain}")
    if sdtm_domain and ucum_unit and sdtm_domain not in UCUM_ALLOWED_DOMAINS:
        errors.append(f"UCUM used with unlikely SDTM domain: {sdtm_domain}")
    if sdtm_domain and icd10_code and sdtm_domain not in ICD10_ALLOWED_DOMAINS:
        errors.append(f"ICD-10 used with unlikely SDTM domain: {sdtm_domain}")
    if sdtm_domain and rxnorm_concept and sdtm_domain not in RXNORM_ALLOWED_DOMAINS:
        errors.append(f"RxNorm used with unlikely SDTM domain: {sdtm_domain}")
    return errors


def _sanitize_sdtm_variable(value: str | None):
    if not value:
        return None
    upper = value.upper()
    if _is_valid_sdtm_variable(upper):
        return upper
    suffix_match = re.fullmatch(r"([A-Z0-9_]+)_\d+", upper)
    if suffix_match:
        candidate = suffix_match.group(1).replace("_", "")
        if _is_valid_sdtm_variable(candidate):
            return candidate
    candidate = re.sub(r"[^A-Z0-9]", "", upper)
    if _is_valid_sdtm_variable(candidate):
        return candidate
    return None


def _auto_reclassify_and_strip(normalized: dict):
    row = dict(normalized)
    actions = []

    loinc_code = row.get("loinc_code")
    snomed_code = row.get("snomed_code")
    if loinc_code and not _is_valid_loinc(loinc_code):
        if not snomed_code and _is_valid_snomed(loinc_code):
            row["snomed_code"] = loinc_code
            row["loinc_code"] = None
            actions.append(f"moved LOINC->{loinc_code} to SNOMED")
        else:
            row["loinc_code"] = None
            actions.append(f"stripped invalid LOINC {loinc_code}")

    if row.get("snomed_code") and not _is_valid_snomed(row.get("snomed_code")):
        actions.append(f"stripped invalid SNOMED {row['snomed_code']}")
        row["snomed_code"] = None

    if row.get("icd10_code") and not _is_valid_icd10(row.get("icd10_code")):
        actions.append(f"stripped invalid ICD-10 {row['icd10_code']}")
        row["icd10_code"] = None

    if row.get("sdtm_domain") and not _is_valid_sdtm_domain(row.get("sdtm_domain")):
        actions.append(f"stripped invalid SDTM domain {row['sdtm_domain']}")
        row["sdtm_domain"] = None

    old_var = row.get("sdtm_variable")
    if old_var and not _is_valid_sdtm_variable(old_var):
        new_var = _sanitize_sdtm_variable(old_var)
        if new_var:
            row["sdtm_variable"] = new_var
            actions.append(f"reclassified SDTM variable {old_var}->{new_var}")
        else:
            row["sdtm_variable"] = None
            actions.append(f"stripped invalid SDTM variable {old_var}")

    if row.get("ucum_unit") and not _is_valid_ucum(row.get("ucum_unit")):
        actions.append(f"stripped invalid UCUM {row['ucum_unit']}")
        row["ucum_unit"] = None

    if row.get("rxnorm_concept") and not _is_valid_rxnorm(row.get("rxnorm_concept")):
        actions.append(f"stripped invalid RxNorm {row['rxnorm_concept']}")
        row["rxnorm_concept"] = None

    domain = row.get("sdtm_domain")
    if domain:
        if row.get("loinc_code") and domain not in LOINC_ALLOWED_DOMAINS:
            actions.append(f"stripped domain-inconsistent LOINC for {domain}")
            row["loinc_code"] = None
        if row.get("ucum_unit") and domain not in UCUM_ALLOWED_DOMAINS:
            actions.append(f"stripped domain-inconsistent UCUM for {domain}")
            row["ucum_unit"] = None
        if row.get("icd10_code") and domain not in ICD10_ALLOWED_DOMAINS:
            actions.append(f"stripped domain-inconsistent ICD-10 for {domain}")
            row["icd10_code"] = None
        if row.get("rxnorm_concept") and domain not in RXNORM_ALLOWED_DOMAINS:
            actions.append(f"stripped domain-inconsistent RxNorm for {domain}")
            row["rxnorm_concept"] = None
    elif any([
        row.get("loinc_code"),
        row.get("snomed_code"),
        row.get("icd10_code"),
        row.get("ucum_unit"),
        row.get("rxnorm_concept"),
    ]):
        if row.get("loinc_code"):
            actions.append("stripped LOINC without SDTM domain")
            row["loinc_code"] = None
        if row.get("snomed_code"):
            actions.append("stripped SNOMED without SDTM domain")
            row["snomed_code"] = None
        if row.get("icd10_code"):
            actions.append("stripped ICD-10 without SDTM domain")
            row["icd10_code"] = None
        if row.get("ucum_unit"):
            actions.append("stripped UCUM without SDTM domain")
            row["ucum_unit"] = None
        if row.get("rxnorm_concept"):
            actions.append("stripped RxNorm without SDTM domain")
            row["rxnorm_concept"] = None

    return row, actions


def _load_mapping_source() -> pd.DataFrame:
    csv_path = pathlib.Path(CSV_IN)
    if csv_path.exists():
        print(f"Using mapping CSV source: {csv_path}")
        return pd.read_csv(csv_path)

    sql_path = pathlib.Path(SQL_OUT)
    if not sql_path.exists():
        raise FileNotFoundError(
            f"Neither mapping CSV nor fallback SQL source exists. Missing: {csv_path} and {sql_path}"
        )

    print(f"Mapping CSV not found. Falling back to schema SQL source: {sql_path}")
    text = sql_path.read_text(encoding="utf-8")
    matches = re.findall(r"INSERT INTO _schema_registry .*? VALUES \((.*?)\) ON CONFLICT", text)
    rows = []
    for raw_values in matches:
        cols = next(csv.reader(io.StringIO(raw_values), quotechar="'", delimiter=",", escapechar="\\"))
        if len(cols) < 12:
            continue
        rows.append(
            {
                "dataset": cols[0].strip(),
                "original_name": cols[1].strip(),
                "sql_type": cols[3].strip(),
                "sdtm_domain": cols[4].strip(),
                "sdtm_variable": cols[5].strip(),
                "loinc_code": cols[6].strip(),
                "snomed_code": cols[7].strip(),
                "icd10_code": cols[8].strip(),
                "ucum_unit": cols[9].strip(),
                "mapping_method": cols[10].strip(),
                "confidence": cols[11].strip(),
            }
        )
    return pd.DataFrame(rows)

ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_IN       = os.path.join(ROOT, "outputs", "compare_columns", "standardized_columns.csv")
SQL_OUT      = os.path.join(ROOT, "db", "schema_standardized.sql")
NIFI_PROC    = os.path.join(ROOT, "nifi", "processors")

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
_MAX_PG_NAME = 63

def to_snake(name: str) -> str:
    """Convert an arbitrary column label to a safe PostgreSQL identifier."""
    s = str(name).strip()
    # Replace non-alphanumeric with underscore
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    s = s.strip("_").lower()
    # Collapse repeated underscores
    s = re.sub(r"_+", "_", s)
    if not s or s[0].isdigit():
        s = "col_" + s
    return s[:_MAX_PG_NAME]

def pg_type(sql_type: str) -> str:
    """Map standardize_columns.py sql_type → PostgreSQL DDL type."""
    t = str(sql_type).strip().upper()
    if t == "FLOAT":
        return "DOUBLE PRECISION"
    if t == "BOOLEAN":
        return "BOOLEAN"
    if t == "INTEGER":
        return "INTEGER"
    if t == "DATE":
        return "DATE"
    if t.startswith("VARCHAR"):
        return t          # pass through VARCHAR(N)
    return "TEXT"         # TEXT, fallback

def coerce_func(sql_type: str) -> str:
    """Return the name of the coercion function for the NiFi processor."""
    t = str(sql_type).strip().upper()
    if t == "FLOAT":          return "to_float"
    if t == "INTEGER":        return "to_int"
    if t == "BOOLEAN":        return "to_bool"
    if t == "DATE":           return "to_date"
    return "to_str"

# ─────────────────────────────────────────────────────────────
# Load & deduplicate
# ─────────────────────────────────────────────────────────────
raw_df = _load_mapping_source()

normalized_rows = []
post_validation_errors = []
autofix_count = 0
for row_number, (_, row) in enumerate(raw_df.iterrows(), start=2):
    normalized = _normalize_row(row)
    cleaned, actions = _auto_reclassify_and_strip(normalized)
    normalized_rows.append(cleaned)
    autofix_count += len(actions)

    errors = _validate_normalized_row(cleaned)
    if errors:
        dataset = cleaned.get("dataset") or "<missing dataset>"
        original_name = cleaned.get("original_name") or "<missing original_name>"
        joined = "; ".join(errors)
        post_validation_errors.append(f"row {row_number} [{dataset} / {original_name}] -> {joined}")

if post_validation_errors:
    print("ERROR: terminology validation still failed after auto-clean")
    for message in post_validation_errors[:50]:
        print(f"  - {message}")
    if len(post_validation_errors) > 50:
        print(f"  ... and {len(post_validation_errors) - 50} more")
    raise SystemExit(2)

print(f"Auto-clean actions applied: {autofix_count}")

df = pd.DataFrame(normalized_rows)


def _dataset_matches(dataset_value: str | None, target_dataset: str) -> bool:
    if not dataset_value:
        return False
    parts = [part.strip().upper() for part in str(dataset_value).split(";") if part.strip()]
    return target_dataset.upper() in parts

def build_col_defs(sub: pd.DataFrame, table_name: str):
    """Return list of (pg_col_name, orig_name, pg_sql_type, meta_comment) tuples."""
    seen = {}
    cols = []
    for _, row in sub.iterrows():
        orig  = str(row["original_name"])
        stype = str(row["sql_type"]) if pd.notna(row["sql_type"]) else "TEXT"
        sdtm  = str(row["sdtm_variable"]) if pd.notna(row["sdtm_variable"]) else ""
        loinc = str(row["loinc_code"]) if pd.notna(row["loinc_code"]) else ""
        ucum  = str(row["ucum_unit"]) if pd.notna(row["ucum_unit"]) else ""
        domain = str(row["sdtm_domain"]) if pd.notna(row["sdtm_domain"]) else ""

        base = to_snake(orig)
        pg_col = base
        suffix = 2
        while pg_col in seen and seen[pg_col] != orig:
            pg_col = f"{base[:_MAX_PG_NAME - 2]}_{suffix}"
            suffix += 1
        seen[pg_col] = orig

        parts = []
        if sdtm:
            parts.append(f"SDTM {domain}.{sdtm}")
        if loinc:
            parts.append(f"LOINC:{loinc}")
        if ucum:
            parts.append(f"[{ucum}]")
        comment = " | ".join(parts) if parts else ""

        cols.append((pg_col, orig, pg_type(stype), coerce_func(stype), comment))
    return cols

# ─────────────────────────────────────────────────────────────
# Build DDL for each dataset table
# ─────────────────────────────────────────────────────────────
DATASETS = {
    "BHS":   ("bhs_participants",   "Record ID",  "VARCHAR(50)"),
    "EHVol": ("ehvol_participants", "DNA ID",     "VARCHAR(50)"),
}

IDEMPOTENT_KEYS = {
    "BHS": "record_id",
    "EHVol": "dna_id",
}

table_col_defs = {}

for ds, (table, pk_orig, pk_type) in DATASETS.items():
    sub = df[df["dataset"].apply(lambda value: _dataset_matches(value, ds))].copy()
    col_defs = build_col_defs(sub, table)
    table_col_defs[ds] = (table, col_defs)

# ─────────────────────────────────────────────────────────────
# Write schema SQL
# ─────────────────────────────────────────────────────────────
lines = [
    "-- ============================================================",
    "-- BioLink Standardized Schema",
    "-- Auto-generated by pipeline/generate_schema_sql.py",
    "-- Guidelines: CDISC SDTM IG 3.3 | LOINC 2.77 | SNOMED CT |",
    "--             ICD-10 WHO | UCUM | RxNorm",
    "-- ============================================================",
    "",
    "-- ── Schema Registry (single source of truth for ETL column metadata) ──",
    "-- Queryable via SQL; Superset can surface this as its own dataset.",
    "CREATE TABLE IF NOT EXISTS _schema_registry (",
    "    id              SERIAL PRIMARY KEY,",
    "    dataset         TEXT NOT NULL,",
    "    original_name   TEXT NOT NULL,",
    "    pg_col_name     TEXT NOT NULL,",
    "    sql_type        TEXT NOT NULL,",
    "    sdtm_domain     TEXT,",
    "    sdtm_variable   TEXT,",
    "    loinc_code      TEXT,",
    "    snomed_code     TEXT,",
    "    icd10_code      TEXT,",
    "    ucum_unit       TEXT,",
    "    mapping_method  TEXT,",
    "    confidence      TEXT,",
    "    UNIQUE (dataset, original_name)",
    ");",
    "",
]

# Populate registry from the standardized_columns.csv data
lines.append("-- Populate _schema_registry (idempotent upsert)")
for _, row in df.iterrows():
    def _esc(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "NULL"
        text = str(v)
        if not text or text.lower() == "nan":
            return "NULL"
        return "'" + text.replace("'", "''") + "'"
    ds_val   = _esc(row.get("dataset"))
    orig_val = _esc(row.get("original_name"))
    # derive pg_col_name for this row
    base_pg = to_snake(str(row.get("original_name", "")))
    stype   = str(row.get("sql_type", "TEXT")) if str(row.get("sql_type", "")) != "nan" else "TEXT"
    pg_val  = _esc(base_pg)
    st_val  = _esc(stype)
    sd_val  = _esc(row.get("sdtm_domain"))
    sv_val  = _esc(row.get("sdtm_variable"))
    lc_val  = _esc(row.get("loinc_code"))
    sn_val  = _esc(row.get("snomed_code"))
    ic_val  = _esc(row.get("icd10_code"))
    uc_val  = _esc(row.get("ucum_unit"))
    mm_val  = _esc(row.get("mapping_method"))
    cf_val  = _esc(row.get("confidence"))
    lines.append(
        f"INSERT INTO _schema_registry"
        f" (dataset,original_name,pg_col_name,sql_type,sdtm_domain,sdtm_variable,"
        f"loinc_code,snomed_code,icd10_code,ucum_unit,mapping_method,confidence)"
        f" VALUES ({ds_val},{orig_val},{pg_val},{st_val},{sd_val},{sv_val},"
        f"{lc_val},{sn_val},{ic_val},{uc_val},{mm_val},{cf_val})"
        f" ON CONFLICT (dataset,original_name) DO UPDATE SET"
        f" pg_col_name=EXCLUDED.pg_col_name, sql_type=EXCLUDED.sql_type,"
        f" sdtm_domain=EXCLUDED.sdtm_domain, sdtm_variable=EXCLUDED.sdtm_variable,"
        f" loinc_code=EXCLUDED.loinc_code, snomed_code=EXCLUDED.snomed_code,"
        f" icd10_code=EXCLUDED.icd10_code, ucum_unit=EXCLUDED.ucum_unit,"
        f" mapping_method=EXCLUDED.mapping_method, confidence=EXCLUDED.confidence;"
    )
lines.append("")

for ds, (table, col_defs) in table_col_defs.items():
    lines.append(f"-- {'='*60}")
    lines.append(f"-- {ds} full-width standardized table")
    lines.append(f"-- {'='*60}")
    # Drop the old narrow table (created by schema.sql) so the wide schema applies cleanly.
    # CASCADE drops the core_participants view which depends on both tables; it is recreated below.
    lines.append(f"DROP TABLE IF EXISTS {table} CASCADE;")
    lines.append(f"CREATE TABLE IF NOT EXISTS {table} (")
    lines.append(f"    _ingest_id       BIGSERIAL,")
    lines.append(f"    _source_dataset  TEXT DEFAULT '{ds}',")
    lines.append(f"    _ingested_at     TIMESTAMPTZ DEFAULT NOW(),")
    lines.append(f"    _data_quality_score DOUBLE PRECISION,")
    lines.append(f"    _source_raw_json JSONB,")
    lines.append( "    -- ── Standardized columns ──")

    # Group by SDTM domain for readability
    from itertools import groupby
    domain_map = {}
    for (pg_col, orig, pgtype, _, comment) in col_defs:
        domain = comment.split(".")[0].replace("SDTM ", "") if "SDTM" in comment else "SV"
        domain_map.setdefault(domain, []).append((pg_col, orig, pgtype, comment))

    for domain in sorted(domain_map):
        lines.append(f"    -- ── {domain} ──────────────────────────────────")
        for pg_col, orig, pgtype, comment in domain_map[domain]:
            col_line = f"    \"{pg_col}\"  {pgtype}"
            if comment:
                col_line += f",  -- {comment}"
            else:
                col_line += ","
            lines.append(col_line)

    lines.append(f"    CONSTRAINT {table}_pkey PRIMARY KEY (_ingest_id)")
    lines.append(");")
    lines.append(f"CREATE INDEX IF NOT EXISTS {table}_dataset_idx ON {table}(_source_dataset);")
    lines.append(f"CREATE INDEX IF NOT EXISTS {table}_ingest_idx  ON {table}(_ingested_at);")
    key_col = IDEMPOTENT_KEYS.get(ds)
    if key_col:
        lines.append(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {table}_{key_col}_uidx "
            f"ON {table}({key_col}) WHERE {key_col} IS NOT NULL;"
        )
    lines.append("")

# ─────────────────────────────────────────────────────────────
# Core cross-dataset view (shared columns only)
# ─────────────────────────────────────────────────────────────
CORE_VIEW_SQL = """-- ============================================================
-- Core cross-dataset view (common columns from BHS + EHVol)
-- Wide clinical columns live in bhs_participants / ehvol_participants;
-- this view provides a minimal cross-study summary.
-- ============================================================
CREATE OR REPLACE VIEW core_participants AS
SELECT
    _ingest_id::TEXT                 AS participant_id,
    _source_dataset                  AS source_dataset,
    "age_at_enrollment"              AS age,
    "enrollment_date"                AS enrollment_date,
    "hba1c"                          AS hba1c,
    "heart_rate"                     AS heart_rate,
    _data_quality_score              AS data_quality_score,
    _ingested_at                     AS ingested_at
FROM bhs_participants
UNION ALL
SELECT
    _ingest_id::TEXT                 AS participant_id,
    _source_dataset                  AS source_dataset,
    "age"                            AS age,
    "date_of_enrolment"              AS enrollment_date,
    NULL::DOUBLE PRECISION           AS hba1c,
    "heart_rate"                     AS heart_rate,
    _data_quality_score              AS data_quality_score,
    _ingested_at                     AS ingested_at
FROM ehvol_participants;
"""

lines += CORE_VIEW_SQL.strip().splitlines()
lines.append("")
lines.append("")

with open(SQL_OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Written: {SQL_OUT}")

# ─────────────────────────────────────────────────────────────
# Write NiFi column-type maps to nifi/processors/ (Python import, no file mount)
# ─────────────────────────────────────────────────────────────
for ds, (table, col_defs) in table_col_defs.items():
    map_path = os.path.join(NIFI_PROC, f"{ds.lower()}_col_map.py")
    lines2 = [
        f"# Auto-generated — {ds} column map for NiFi BiolinkSchemaStandardizerProcessor",
        f"# Source: pipeline/generate_schema_sql.py  \u2192  standardized_columns.csv",
        f"# Format: {{original_col_name: (pg_col_name, coerce_func_name)}}",
        f"# DO NOT EDIT by hand; re-run pipeline/generate_schema_sql.py instead.",
        f"COLUMN_MAP = {{",
    ]
    for pg_col, orig, pgtype, coerce, comment in col_defs:
        lines2.append(f"    {repr(orig)}: ({repr(pg_col)}, {repr(coerce)}),  # {comment}")
    lines2.append("}")
    with open(map_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines2) + "\n")
    print(f"Written: {map_path}")

print("Done.")

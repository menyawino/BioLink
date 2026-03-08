"""
BioLink Registry Pipeline Processor for Apache NiFi 2.8.0.

Runs the documented script ETL plan inside NiFi:
  1. scripts/apply_schema.py
  2. scripts/omop_etl.py
  3. scripts/omop_quality.py
  4. loads unified registry + OMOP CSV outputs into PostgreSQL

This keeps NiFi as the execution engine while using the same ETL method as the
scripts-based registry pipeline.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, execute_values

from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import ExpressionLanguageScope, PropertyDescriptor


def _count_csv_rows(path: Path) -> tuple[int, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        row_count = sum(1 for _ in reader)
    return row_count, len(header)


def _boolish(values: list[str]) -> bool:
    allowed = {"true", "false", "1", "0", "yes", "no", "y", "n", "checked", "unchecked"}
    cleaned = [value.strip().lower() for value in values if value is not None and str(value).strip() != ""]
    return bool(cleaned) and all(value in allowed for value in cleaned)


def _intish(values: list[str]) -> bool:
    cleaned = [value for value in values if value is not None and str(value).strip() != ""]
    if not cleaned:
        return False
    try:
        for value in cleaned:
            int(str(value).strip())
        return True
    except ValueError:
        return False


def _floatish(values: list[str]) -> bool:
    cleaned = [value for value in values if value is not None and str(value).strip() != ""]
    if not cleaned:
        return False
    try:
        for value in cleaned:
            float(str(value).strip())
        return True
    except ValueError:
        return False


def _dateish(values: list[str]) -> bool:
    cleaned = [value for value in values if value is not None and str(value).strip() != ""]
    if not cleaned:
        return False
    for value in cleaned:
        text = str(value).strip()
        if "T" in text:
            text = text.replace("Z", "+00:00")
        try:
            datetime.fromisoformat(text)
            continue
        except ValueError:
            pass
        try:
            datetime.strptime(text, "%Y-%m-%d")
            continue
        except ValueError:
            return False
    return True


def _infer_sql_type(column_name: str, sample_values: list[str]) -> str:
    name = column_name.lower()
    if name.endswith("_datetime") or name == "birth_datetime":
        return "TIMESTAMPTZ" if _dateish(sample_values) else "TEXT"
    if name.endswith("_date") or name == "event_date":
        return "DATE" if _dateish(sample_values) else "TEXT"
    if _boolish(sample_values):
        return "BOOLEAN"
    if _intish(sample_values):
        return "BIGINT"
    if _floatish(sample_values):
        return "DOUBLE PRECISION"
    return "TEXT"


def _create_or_replace_csv_table(conn, csv_path: Path, table_name: str) -> int:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []

    if not columns:
        raise ValueError(f"CSV '{csv_path}' has no header row")

    sample_by_column: dict[str, list[str]] = {column: [] for column in columns}
    for row in rows[:250]:
        for column in columns:
            sample_by_column[column].append(row.get(column, ""))

    with conn.cursor() as cursor:
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table_name)))
        definitions = [
            sql.SQL("{} {}")
            .format(sql.Identifier(column), sql.SQL(_infer_sql_type(column, sample_by_column[column])))
            for column in columns
        ]
        cursor.execute(
            sql.SQL("CREATE TABLE {} ({})").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(definitions),
            )
        )
        with csv_path.open("r", encoding="utf-8") as copy_handle:
            copy_sql = sql.SQL("COPY {} ({}) FROM STDIN WITH CSV HEADER").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            )
            cursor.copy_expert(copy_sql.as_string(conn), copy_handle)
    conn.commit()
    return len(rows)


def _load_unified_registry(conn, csv_path: Path, table_name: str) -> int:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    with conn.cursor() as cursor:
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table_name)))
        cursor.execute(
            sql.SQL(
                "CREATE TABLE {} ("
                "id BIGSERIAL PRIMARY KEY, "
                "cohort TEXT NOT NULL, "
                "clinical_data JSONB NOT NULL, "
                "loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                ")"
            ).format(sql.Identifier(table_name))
        )
        payload = [
            (
                row.get("cohort", ""),
                Json({key: value for key, value in row.items() if key != "cohort"}),
            )
            for row in rows
        ]
        if payload:
            execute_values(
                cursor,
                sql.SQL("INSERT INTO {} (cohort, clinical_data) VALUES %s").format(sql.Identifier(table_name)).as_string(conn),
                payload,
            )
    conn.commit()
    return len(rows)


def _store_run_manifest(conn, manifest: dict) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS registry_etl_runs (
                run_id BIGSERIAL PRIMARY KEY,
                finished_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                manifest JSONB NOT NULL
            )
            """
        )
        cursor.execute(
            "INSERT INTO registry_etl_runs (manifest) VALUES (%s)",
            (Json(manifest),),
        )
    conn.commit()


class BiolinkRegistryPipelineProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "1.0.0"
        description = (
            "Runs the script-aligned BioLink registry pipeline inside NiFi, writes the "
            "unified registry, OMOP CSVs, quality artifacts, and loads the resulting "
            "datasets into PostgreSQL."
        )
        tags = ["biolink", "etl", "registry", "omop", "postgres", "scripted"]

    REPOSITORY_ROOT = PropertyDescriptor(
        name="Repository Root",
        description="Mounted repository root containing scripts/, db/, and outputs/.",
        required=True,
        default_value="/opt/nifi/biolink_repo",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    SCHEMA_RELATIVE_PATH = PropertyDescriptor(
        name="Schema Relative Path",
        description="Path to master_schema.csv relative to the repository root.",
        required=True,
        default_value="outputs/master_schema.csv",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    UNIFIED_RELATIVE_PATH = PropertyDescriptor(
        name="Unified Output Relative Path",
        description="Path to unified_registry.csv relative to the repository root.",
        required=True,
        default_value="outputs/unified_registry.csv",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    OMOP_OUTPUT_DIR = PropertyDescriptor(
        name="OMOP Output Relative Directory",
        description="OMOP output directory relative to the repository root.",
        required=True,
        default_value="outputs/omop_cdm",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    REPORT_HTML_PATH = PropertyDescriptor(
        name="Quality Report Relative Path",
        description="HTML quality report path relative to the repository root.",
        required=True,
        default_value="outputs/data_quality_report.html",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    CHARACTERIZATION_PATH = PropertyDescriptor(
        name="Characterization Relative Path",
        description="Characterization CSV path relative to the repository root.",
        required=True,
        default_value="outputs/cohort_characterization.csv",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    LOAD_TO_POSTGRES = PropertyDescriptor(
        name="Load To PostgreSQL",
        description="When true, load the unified registry snapshot and OMOP CSVs into PostgreSQL.",
        required=False,
        default_value="true",
        allowable_values=["true", "false"],
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    DB_HOST = PropertyDescriptor(
        name="Database Host",
        description="PostgreSQL host.",
        required=True,
        default_value="postgres",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    DB_PORT = PropertyDescriptor(
        name="Database Port",
        description="PostgreSQL port.",
        required=True,
        default_value="5432",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    DB_NAME = PropertyDescriptor(
        name="Database Name",
        description="PostgreSQL database name.",
        required=True,
        default_value="biolink",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    DB_USER = PropertyDescriptor(
        name="Database User",
        description="PostgreSQL user.",
        required=True,
        default_value="biolink",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    DB_PASSWORD = PropertyDescriptor(
        name="Database Password",
        description="PostgreSQL password.",
        required=True,
        default_value="biolink_secret",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    UNIFIED_TABLE_NAME = PropertyDescriptor(
        name="Unified Registry Table",
        description="Table used to store the wide unified registry snapshot as JSONB per patient.",
        required=True,
        default_value="unified_registry",
        expression_language_scope=ExpressionLanguageScope.VARIABLE_REGISTRY,
    )
    property_descriptors = [
        REPOSITORY_ROOT,
        SCHEMA_RELATIVE_PATH,
        UNIFIED_RELATIVE_PATH,
        OMOP_OUTPUT_DIR,
        REPORT_HTML_PATH,
        CHARACTERIZATION_PATH,
        LOAD_TO_POSTGRES,
        DB_HOST,
        DB_PORT,
        DB_NAME,
        DB_USER,
        DB_PASSWORD,
        UNIFIED_TABLE_NAME,
    ]

    def getPropertyDescriptors(self):
        return self.property_descriptors

    def _run_script(self, repo_root: Path, command: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            command,
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )

    def transform(self, context, flowfile):
        repo_root = Path(context.getProperty(self.REPOSITORY_ROOT).getValue())
        schema_path = repo_root / context.getProperty(self.SCHEMA_RELATIVE_PATH).getValue()
        unified_path = repo_root / context.getProperty(self.UNIFIED_RELATIVE_PATH).getValue()
        omop_dir = repo_root / context.getProperty(self.OMOP_OUTPUT_DIR).getValue()
        report_html = repo_root / context.getProperty(self.REPORT_HTML_PATH).getValue()
        characterization_csv = repo_root / context.getProperty(self.CHARACTERIZATION_PATH).getValue()
        load_to_postgres = (context.getProperty(self.LOAD_TO_POSTGRES).getValue() or "true").strip().lower() == "true"
        unified_table = context.getProperty(self.UNIFIED_TABLE_NAME).getValue() or "unified_registry"

        if not repo_root.is_dir():
            message = f"BiolinkRegistryPipelineProcessor: repository root not found at '{repo_root}'"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": message}),
                attributes={"biolink.error": message},
            )
        if not schema_path.is_file():
            message = f"BiolinkRegistryPipelineProcessor: master schema not found at '{schema_path}'"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": message}),
                attributes={"biolink.error": message},
            )

        apply_script = repo_root / "scripts" / "apply_schema.py"
        omop_script = repo_root / "scripts" / "omop_etl.py"
        quality_script = repo_root / "scripts" / "omop_quality.py"

        try:
            self._run_script(
                repo_root,
                [
                    "python3",
                    str(apply_script),
                    str(schema_path),
                    str(repo_root / "db" / "BHS_Full.csv"),
                    str(repo_root / "db" / "EHVol_Full.csv"),
                    "--output",
                    str(unified_path),
                ],
            )
            self._run_script(
                repo_root,
                [
                    "python3",
                    str(omop_script),
                    "--unified",
                    str(unified_path),
                    "--schema",
                    str(schema_path),
                    "--output-dir",
                    str(omop_dir),
                    "--format",
                    "csv",
                ],
            )
            self._run_script(
                repo_root,
                [
                    "python3",
                    str(quality_script),
                    "--input-dir",
                    str(omop_dir),
                    "--report-html",
                    str(report_html),
                    "--characterization-csv",
                    str(characterization_csv),
                ],
            )
        except subprocess.CalledProcessError as exc:
            message = exc.stderr or exc.stdout or str(exc)
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": message}),
                attributes={"biolink.error": message[:2000]},
            )

        unified_rows, unified_cols = _count_csv_rows(unified_path)
        manifest_path = omop_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
        summary = {
            "master_schema_path": str(schema_path),
            "unified_registry_path": str(unified_path),
            "unified_registry_rows": unified_rows,
            "unified_registry_columns": unified_cols,
            "omop_output_dir": str(omop_dir),
            "quality_report_path": str(report_html),
            "characterization_path": str(characterization_csv),
            "omop_manifest": manifest,
        }

        if load_to_postgres:
            conn = psycopg2.connect(
                host=context.getProperty(self.DB_HOST).getValue(),
                port=int(context.getProperty(self.DB_PORT).getValue() or "5432"),
                dbname=context.getProperty(self.DB_NAME).getValue(),
                user=context.getProperty(self.DB_USER).getValue(),
                password=context.getProperty(self.DB_PASSWORD).getValue(),
            )
            try:
                summary["postgres_unified_rows"] = _load_unified_registry(conn, unified_path, unified_table)
                omop_tables = {
                    "person": omop_dir / "person.csv",
                    "measurement": omop_dir / "measurement.csv",
                    "condition_occurrence": omop_dir / "condition_occurrence.csv",
                    "observation": omop_dir / "observation.csv",
                }
                loaded_tables = {}
                for table_name, csv_path in omop_tables.items():
                    if csv_path.is_file():
                        loaded_tables[table_name] = _create_or_replace_csv_table(conn, csv_path, f"omop_{table_name}")
                summary["postgres_omop_tables"] = loaded_tables
                _store_run_manifest(conn, summary)
            finally:
                conn.close()

        now_iso = datetime.now(timezone.utc).isoformat()
        return FlowFileTransformResult(
            relationship="success",
            contents=json.dumps(summary, indent=2).encode("utf-8"),
            attributes={
                "biolink.registry.rows": str(unified_rows),
                "biolink.registry.columns": str(unified_cols),
                "biolink.registry.completed_at": now_iso,
                "mime.type": "application/json",
            },
        )
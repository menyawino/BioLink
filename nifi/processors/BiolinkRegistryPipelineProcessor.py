"""BioLink Registry Pipeline Processor for Apache NiFi 2.8.0.

Runs the replacement db/test pipeline inside NiFi and loads the current unified
registry snapshot plus cohort comparability artifacts into PostgreSQL.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import ExpressionLanguageScope, PropertyDescriptor


_PG_IDENTIFIER_LIMIT = 63


def _count_csv_rows(path: Path) -> tuple[int, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        row_count = sum(1 for _ in reader)
    return row_count, len(header)


def _parse_requested_datasets(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []

    normalized: list[str] = []
    for part in str(raw_value).split(","):
        dataset = part.strip().lower()
        if dataset in {"bhs", "ehvol"} and dataset not in normalized:
            normalized.append(dataset)
    return normalized


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


def _safe_pg_identifier(name: str, used_names: set[str]) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z_]+", "_", str(name).strip()).strip("_").lower()
    if not normalized:
        normalized = "column"
    if normalized[0].isdigit():
        normalized = f"col_{normalized}"

    candidate = normalized[:_PG_IDENTIFIER_LIMIT]
    if candidate not in used_names and len(normalized) <= _PG_IDENTIFIER_LIMIT:
        used_names.add(candidate)
        return candidate

    digest = hashlib.sha1(str(name).encode("utf-8")).hexdigest()[:8]
    stem_limit = _PG_IDENTIFIER_LIMIT - len(digest) - 1
    candidate = f"{normalized[:stem_limit].rstrip('_')}_{digest}"
    counter = 1
    while candidate in used_names:
        suffix = f"_{digest}{counter}"
        stem_limit = _PG_IDENTIFIER_LIMIT - len(suffix)
        candidate = f"{normalized[:stem_limit].rstrip('_')}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def _create_or_replace_csv_table(conn, csv_path: Path, table_name: str, sql_module) -> int:
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
        cursor.execute(sql_module.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql_module.Identifier(table_name)))
        definitions = [
            sql_module.SQL("{} {}")
            .format(sql_module.Identifier(column), sql_module.SQL(_infer_sql_type(column, sample_by_column[column])))
            for column in columns
        ]
        cursor.execute(
            sql_module.SQL("CREATE TABLE {} ({})").format(
                sql_module.Identifier(table_name),
                sql_module.SQL(", ").join(definitions),
            )
        )
        with csv_path.open("r", encoding="utf-8") as copy_handle:
            copy_sql = sql_module.SQL("COPY {} ({}) FROM STDIN WITH CSV HEADER").format(
                sql_module.Identifier(table_name),
                sql_module.SQL(", ").join(sql_module.Identifier(column) for column in columns),
            )
            cursor.copy_expert(copy_sql.as_string(conn), copy_handle)
    conn.commit()
    return len(rows)


def _load_unified_registry(conn, csv_path: Path, table_name: str, sql_module, json_cls, execute_values_fn) -> int:
    del json_cls

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []

    if not columns:
        raise ValueError(f"CSV '{csv_path}' has no header row")

    used_names: set[str] = set()
    column_map = {column: _safe_pg_identifier(column, used_names) for column in columns}
    payload = [tuple((row.get(column) or "").strip() or None for column in columns) for row in rows]

    with conn.cursor() as cursor:
        cursor.execute(sql_module.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql_module.Identifier(table_name)))
        cursor.execute(
            sql_module.SQL("CREATE TABLE {} ({})").format(
                sql_module.Identifier(table_name),
                sql_module.SQL(", ").join(
                    sql_module.SQL("{} TEXT").format(sql_module.Identifier(column_map[column]))
                    for column in columns
                ),
            )
        )
        if payload:
            insert_sql = sql_module.SQL("INSERT INTO {} ({}) VALUES %s").format(
                sql_module.Identifier(table_name),
                sql_module.SQL(", ").join(
                    sql_module.Identifier(column_map[column]) for column in columns
                ),
            )
            execute_values_fn(
                cursor,
                insert_sql.as_string(conn),
                payload,
            )
    conn.commit()
    return len(rows)


def _insertable_columns(conn, table_name: str) -> list[str]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        return [(row[0], row[1]) for row in cursor.fetchall() if row[0] != "_ingest_id"]


def _parse_dateish(text: str):
    normalized = text.strip()
    if not normalized:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue

    iso_candidate = normalized.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        return parsed.date()
    except ValueError:
        return None


def _parse_timestampish(text: str):
    normalized = text.strip()
    if not normalized:
        return None

    iso_candidate = normalized.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(normalized, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _clean_cell(value: str | None, data_type: str):
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None

    lowered = text.lower()
    if data_type == "boolean":
        if lowered in {"true", "t", "1", "yes", "y", "on", "checked"}:
            return True
        if lowered in {"false", "f", "0", "no", "n", "off", "unchecked"}:
            return False
        return None

    if data_type == "date":
        return _parse_dateish(text)
    if data_type.startswith("timestamp"):
        return _parse_timestampish(text)
    if data_type in {"smallint", "integer", "bigint"}:
        try:
            return int(text)
        except ValueError:
            return None
    if data_type in {"real", "double precision", "numeric", "decimal"}:
        try:
            return float(text)
        except ValueError:
            return None

    return text


def _load_dataset_participants(
    conn,
    csv_path: Path,
    table_name: str,
    cohort_name: str,
    source_dataset: str,
    sql_module,
    json_cls,
    execute_values_fn,
) -> int:
    columns = _insertable_columns(conn, table_name)
    loaded_at = datetime.now(timezone.utc)
    payload = []
    key_column = next(
        (column for column, _ in columns if column in {"participant_id", "dna_id", "record_id"}),
        None,
    )
    deduped_rows = {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("cohort") or "").strip() != cohort_name:
                continue

            values = []
            for column, data_type in columns:
                if column == "_source_dataset":
                    values.append(source_dataset)
                elif column == "_ingested_at":
                    values.append(loaded_at)
                elif column == "_source_raw_json":
                    values.append(json_cls(row))
                else:
                    values.append(_clean_cell(row.get(column), data_type))

            if key_column:
                key_index = next(i for i, (column, _) in enumerate(columns) if column == key_column)
                key_value = values[key_index]
                if key_value is not None:
                    deduped_rows[key_value] = tuple(values)
                    continue

            payload.append(tuple(values))

    if deduped_rows:
        payload.extend(deduped_rows.values())

    with conn.cursor() as cursor:
        cursor.execute(
            sql_module.SQL("TRUNCATE TABLE {} RESTART IDENTITY").format(
                sql_module.Identifier(table_name)
            )
        )
        if payload:
            insert_sql = sql_module.SQL("INSERT INTO {} ({}) VALUES %s").format(
                sql_module.Identifier(table_name),
                sql_module.SQL(", ").join(
                    sql_module.Identifier(column) for column, _ in columns
                ),
            ).as_string(conn)
            execute_values_fn(cursor, insert_sql, payload, page_size=250)

    conn.commit()
    return len(payload)


def _load_characterization_table(conn, csv_path: Path, sql_module) -> int:
    return _create_or_replace_csv_table(conn, csv_path, "cohort_characterization", sql_module)


def _store_run_manifest(conn, manifest: dict, json_cls) -> None:
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
            (json_cls(manifest),),
        )
    conn.commit()


def _drop_tables(conn, table_names: list[str], sql_module) -> None:
    with conn.cursor() as cursor:
        for table_name in table_names:
            cursor.execute(
                sql_module.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                    sql_module.Identifier(table_name)
                )
            )
    conn.commit()


class BiolinkRegistryPipelineProcessor(FlowFileTransform):
    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "1.0.0"
        description = (
            "Runs the replacement db/test BioLink registry pipeline inside NiFi, writes the "
            "current unified registry and audit artifacts, and loads the resulting datasets "
            "into PostgreSQL."
        )
        tags = ["biolink", "etl", "registry", "postgres", "scripted"]

    REPOSITORY_ROOT = PropertyDescriptor(
        name="Repository Root",
        description="Mounted repository root containing db/test/, db/, and outputs/.",
        required=True,
        default_value="/opt/nifi/biolink_repo",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    UNIFIED_RELATIVE_PATH = PropertyDescriptor(
        name="Unified Output Relative Path",
        description="Path to unified_registry.csv relative to the repository root.",
        required=True,
        default_value="outputs/unified_registry.csv",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    REPORT_HTML_PATH = PropertyDescriptor(
        name="Quality Report Relative Path",
        description="HTML quality report path relative to the repository root.",
        required=True,
        default_value="outputs/data_quality_report.html",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    CHARACTERIZATION_PATH = PropertyDescriptor(
        name="Characterization Relative Path",
        description="Characterization CSV path relative to the repository root.",
        required=True,
        default_value="outputs/cohort_characterization.csv",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    LOAD_TO_POSTGRES = PropertyDescriptor(
        name="Load To PostgreSQL",
        description="When true, load the unified registry snapshot and comparability artifacts into PostgreSQL.",
        required=False,
        default_value="true",
        allowable_values=["true", "false"],
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    DB_HOST = PropertyDescriptor(
        name="Database Host",
        description="PostgreSQL host.",
        required=True,
        default_value="postgres",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    DB_PORT = PropertyDescriptor(
        name="Database Port",
        description="PostgreSQL port.",
        required=True,
        default_value="5432",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    DB_NAME = PropertyDescriptor(
        name="Database Name",
        description="PostgreSQL database name.",
        required=True,
        default_value="biolink",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    DB_USER = PropertyDescriptor(
        name="Database User",
        description="PostgreSQL user.",
        required=True,
        default_value="biolink",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    DB_PASSWORD = PropertyDescriptor(
        name="Database Password",
        description="PostgreSQL password.",
        required=True,
        default_value="biolink_secret",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    UNIFIED_TABLE_NAME = PropertyDescriptor(
        name="Unified Registry Table",
        description="Table used to store the wide unified registry snapshot with one column per harmonized field.",
        required=True,
        default_value="unified_registry",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    TRIGGER_RUN_TOKEN = PropertyDescriptor(
        name="Trigger Run Token",
        description="Backend-provided token used to correlate a specific NiFi RUN_ONCE request with registry_etl_runs entries.",
        required=False,
        default_value="",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    TRIGGER_REQUESTED_DATASETS = PropertyDescriptor(
        name="Triggered Datasets",
        description="Comma-separated requested datasets for the current backend-triggered ETL job.",
        required=False,
        default_value="",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    COMPARABILITY_RELATIVE_PATH = PropertyDescriptor(
        name="Comparability Report Relative Path",
        description="Path to comparability_report.json relative to the repository root.",
        required=True,
        default_value="outputs/comparability_report.json",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )
    property_descriptors = [
        REPOSITORY_ROOT,
        UNIFIED_RELATIVE_PATH,
        COMPARABILITY_RELATIVE_PATH,
        REPORT_HTML_PATH,
        CHARACTERIZATION_PATH,
        LOAD_TO_POSTGRES,
        DB_HOST,
        DB_PORT,
        DB_NAME,
        DB_USER,
        DB_PASSWORD,
        UNIFIED_TABLE_NAME,
        TRIGGER_RUN_TOKEN,
        TRIGGER_REQUESTED_DATASETS,
    ]

    def __init__(self, **kwargs):
        # NiFi passes runtime kwargs (including jvm) to the constructor.
        # FlowFileTransform does not accept them, so initialize without forwarding.
        super().__init__()

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
        unified_path = repo_root / context.getProperty(self.UNIFIED_RELATIVE_PATH).getValue()
        comparability_path = repo_root / context.getProperty(self.COMPARABILITY_RELATIVE_PATH).getValue()
        report_html = repo_root / context.getProperty(self.REPORT_HTML_PATH).getValue()
        characterization_csv = repo_root / context.getProperty(self.CHARACTERIZATION_PATH).getValue()
        load_to_postgres = (context.getProperty(self.LOAD_TO_POSTGRES).getValue() or "true").strip().lower() == "true"
        unified_table = context.getProperty(self.UNIFIED_TABLE_NAME).getValue() or "unified_registry"
        trigger_run_token = (context.getProperty(self.TRIGGER_RUN_TOKEN).getValue() or "").strip() or str(uuid4())
        requested_datasets = _parse_requested_datasets(
            context.getProperty(self.TRIGGER_REQUESTED_DATASETS).getValue()
        )

        if not repo_root.is_dir():
            message = f"BiolinkRegistryPipelineProcessor: repository root not found at '{repo_root}'"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": message}),
                attributes={"biolink.error": message},
            )
        pipeline_runner = repo_root / "db" / "test" / "run_pipeline.py"
        if not pipeline_runner.is_file():
            message = f"BiolinkRegistryPipelineProcessor: replacement pipeline runner not found at '{pipeline_runner}'"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": message}),
                attributes={"biolink.error": message},
            )

        try:
            self._run_script(
                repo_root,
                [
                    "python3",
                    str(pipeline_runner),
                    "--repo-root",
                    str(repo_root),
                    "--unified-output",
                    str(unified_path),
                    "--comparability-output",
                    str(comparability_path),
                    "--report-html",
                    str(report_html),
                    "--characterization-output",
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

        if not unified_path.is_file():
            message = f"BiolinkRegistryPipelineProcessor: replacement pipeline did not create '{unified_path}'"
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": message}),
                attributes={"biolink.error": message},
            )

        unified_rows, unified_cols = _count_csv_rows(unified_path)
        summary = {
            "source": "nifi-processor",
            "pipeline": "db/test",
            "pipeline_runner": str(pipeline_runner),
            "trigger_token": trigger_run_token,
            "requested_datasets": requested_datasets,
            "unified_registry_path": str(unified_path),
            "unified_registry_rows": unified_rows,
            "unified_registry_columns": unified_cols,
            "comparability_path": str(comparability_path),
            "quality_report_path": str(report_html),
            "characterization_path": str(characterization_csv),
        }

        if load_to_postgres:
            try:
                import psycopg2
                from psycopg2 import sql as psy_sql
                from psycopg2.extras import Json as psy_json, execute_values as psy_execute_values
            except Exception as exc:
                message = f"BiolinkRegistryPipelineProcessor: PostgreSQL driver import failed: {exc}"
                return FlowFileTransformResult(
                    relationship="failure",
                    contents=json.dumps({"error": message}),
                    attributes={"biolink.error": message[:2000]},
                )

            conn = psycopg2.connect(
                host=context.getProperty(self.DB_HOST).getValue(),
                port=int(context.getProperty(self.DB_PORT).getValue() or "5432"),
                dbname=context.getProperty(self.DB_NAME).getValue(),
                user=context.getProperty(self.DB_USER).getValue(),
                password=context.getProperty(self.DB_PASSWORD).getValue(),
            )
            try:
                _store_run_manifest(
                    conn,
                    {
                        **summary,
                        "status": "running",
                        "stage": "postgres-load-started",
                        "started_at": datetime.now(timezone.utc).isoformat(),
                    },
                    psy_json,
                )
                try:
                    _drop_tables(
                        conn,
                        [
                            "harmonization_provenance",
                            "harmonization_tiers",
                            "comparability_report",
                            "cohort_characterization",
                        ],
                        psy_sql,
                    )
                    summary["postgres_unified_rows"] = _load_unified_registry(
                        conn,
                        unified_path,
                        unified_table,
                        psy_sql,
                        psy_json,
                        psy_execute_values,
                    )
                    summary["postgres_dataset_rows"] = {
                        "bhs_participants": _load_dataset_participants(
                            conn,
                            unified_path,
                            "bhs_participants",
                            "D1",
                            "bhs",
                            psy_sql,
                            psy_json,
                            psy_execute_values,
                        ),
                        "ehvol_participants": _load_dataset_participants(
                            conn,
                            unified_path,
                            "ehvol_participants",
                            "D2",
                            "ehvol",
                            psy_sql,
                            psy_json,
                            psy_execute_values,
                        ),
                    }
                    comparability_loaded = False
                    if comparability_path.is_file():
                        report_json = json.loads(comparability_path.read_text())
                        with conn.cursor() as cursor:
                            cursor.execute(psy_sql.SQL(
                                "DROP TABLE IF EXISTS {} CASCADE"
                            ).format(psy_sql.Identifier("comparability_report")))
                            cursor.execute(psy_sql.SQL(
                                "CREATE TABLE {} ("
                                "id BIGSERIAL PRIMARY KEY, "
                                "report JSONB NOT NULL, "
                                "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                                ")"
                            ).format(psy_sql.Identifier("comparability_report")))
                            cursor.execute(
                                psy_sql.SQL("INSERT INTO {} (report) VALUES (%s)").format(
                                    psy_sql.Identifier("comparability_report")
                                ).as_string(conn),
                                (psy_json(report_json),),
                            )
                        conn.commit()
                        comparability_loaded = True
                    summary["postgres_comparability_loaded"] = comparability_loaded
                    characterization_loaded = False
                    characterization_rows = 0
                    if characterization_csv.is_file():
                        characterization_rows = _load_characterization_table(
                            conn,
                            characterization_csv,
                            psy_sql,
                        )
                        characterization_loaded = True
                    summary["postgres_characterization_loaded"] = characterization_loaded
                    summary["postgres_characterization_rows"] = characterization_rows
                    _store_run_manifest(
                        conn,
                        {
                            **summary,
                            "status": "succeeded",
                            "stage": "postgres-load-complete",
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                        },
                        psy_json,
                    )
                except Exception as exc:
                    conn.rollback()
                    try:
                        _store_run_manifest(
                            conn,
                            {
                                **summary,
                                "status": "failed",
                                "stage": "postgres-load-failed",
                                "failed_at": datetime.now(timezone.utc).isoformat(),
                                "error": str(exc),
                            },
                            psy_json,
                        )
                    except Exception:
                        pass
                    message = f"BiolinkRegistryPipelineProcessor: PostgreSQL load failed: {exc}"
                    return FlowFileTransformResult(
                        relationship="failure",
                        contents=json.dumps({"error": message}),
                        attributes={"biolink.error": message[:2000]},
                    )
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
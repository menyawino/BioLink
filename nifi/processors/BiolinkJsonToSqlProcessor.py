"""
BioLink JSON-to-SQL Processor for Apache NiFi 2.8.0

Converts validated unified JSON records into PostgreSQL INSERT/UPSERT
SQL statements for a configured target table.
"""

import json
from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, ExpressionLanguageScope


# Columns in the dataset participant tables (order matters for SQL)
UNIFIED_COLUMNS = [
    "participant_id",
    "source_dataset",
    "source_record_id",
    "date_of_birth",
    "age",
    "gender",
    "nationality",
    "enrollment_date",
    "current_city",
    "childhood_city",
    "father_origin_city",
    "mother_origin_city",
    "height_cm",
    "weight_kg",
    "bmi",
    "heart_rate",
    "systolic_bp",
    "diastolic_bp",
    "hba1c",
    "troponin_i",
    "echo_ef",
    "echo_date",
    "has_diabetes",
    "has_hypertension",
    "has_dyslipidemia",
    "has_heart_failure",
    "is_smoker",
    "smoking_pack_years",
    "family_history_cad",
    "family_history_diabetes",
    "consanguineous_parents",
    "source_raw_json",
    "ingested_at",
    "data_quality_score",
]


def _sql_value(val):
    """Convert a Python value to SQL literal."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    # JSON/dict/list -> JSONB literal
    if isinstance(val, (dict, list)):
        s = json.dumps(val).replace("'", "''")
        return f"'{s}'::jsonb"

    # Escape single quotes for strings
    s = str(val).replace("'", "''")
    return f"'{s}'"


class BiolinkJsonToSqlProcessor(FlowFileTransform):
    """
    Converts validated unified JSON records into PostgreSQL
    INSERT … ON CONFLICT UPDATE statements.
    """

    class Java:
        implements = ["org.apache.nifi.python.processor.FlowFileTransform"]

    class ProcessorDetails:
        version = "1.0.0"
        description = (
            "Converts unified BioLink JSON records to PostgreSQL INSERT "
            "statements targeting a configured dataset table. "
            "Supports upsert (ON CONFLICT DO UPDATE)."
        )
        tags = ["biolink", "sql", "postgresql", "etl"]

    TABLE_NAME = PropertyDescriptor(
        name="Table Name",
        description="Target PostgreSQL table name",
        required=True,
        default_value="bhs_participants",
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    UPSERT_MODE = PropertyDescriptor(
        name="Upsert Mode",
        description="Use ON CONFLICT DO UPDATE (upsert) or plain INSERT",
        required=False,
        default_value="true",
        allowable_values=["true", "false"],
        expression_language_scope=ExpressionLanguageScope.FLOWFILE_ATTRIBUTES,
    )

    property_descriptors = [TABLE_NAME, UPSERT_MODE]

    def __init__(self, **kwargs):
        super().__init__()

    def getPropertyDescriptors(self):
        return self.property_descriptors

    def transform(self, context, flowfile):
        table = context.getProperty(self.TABLE_NAME).evaluateAttributeExpressions(flowfile).getValue()
        upsert = context.getProperty(self.UPSERT_MODE).evaluateAttributeExpressions(flowfile).getValue() == "true"

        try:
            raw = json.loads(flowfile.getContentsAsBytes().decode("utf-8"))
        except Exception as e:
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": f"Invalid JSON: {e}"}),
                attributes={"biolink.error": str(e)},
            )

        records = raw if isinstance(raw, list) else [raw]
        if not records:
            return FlowFileTransformResult(
                relationship="failure",
                contents=json.dumps({"error": "No records found in input JSON"}),
                attributes={"biolink.error": "No records found in input JSON"},
            )

        output = self._build_bulk_sql(records, table, upsert) + ";\n"

        return FlowFileTransformResult(
            relationship="success",
            contents=output,
            attributes={
                "biolink.sql.statement_count": "1",
                "biolink.sql.record_count": str(len(records)),
                "biolink.sql.table": table,
                "mime.type": "text/plain",
            },
        )

    def _build_bulk_sql(self, records, table, upsert):
        cols = []
        for col in UNIFIED_COLUMNS:
            if col.startswith("_"):
                continue
            cols.append(col)

        col_list = ", ".join(cols)

        # Build upsert suffix once
        conflict_suffix = ""
        if upsert:
            update_pairs = []
            for col in cols:
                if col == "participant_id":
                    continue
                update_pairs.append(f"{col} = EXCLUDED.{col}")
            conflict_suffix = f" ON CONFLICT (participant_id) DO UPDATE SET {', '.join(update_pairs)}"

        # Build ONE INSERT statement for ALL records in this FlowFile.
        # Chunking is handled upstream by splitting CSV files.
        row_values = []
        for record in records:
            vals = [_sql_value(record.get(col)) for col in cols]
            row_values.append(f"({', '.join(vals)})")

        val_list = ",\n".join(row_values)
        return f"INSERT INTO {table} ({col_list}) VALUES\n{val_list}{conflict_suffix}"

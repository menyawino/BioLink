import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("biolink.superset_init")


EMBEDDED_GUEST_PERMISSIONS = (
    ("can_read", "CurrentUserRestApi"),
    ("can_read", "Dashboard"),
)
LAYOUT_CONTAINER_TYPES = {"GRID", "ROW", "COLUMN", "TAB", "TABS"}
VERIFICATION_DASHBOARD_ID_HINT = os.getenv("SUPERSET_VERIFICATION_DASHBOARD_ID", "").strip()
VERIFICATION_DASHBOARD_TITLE = (
    os.getenv("SUPERSET_VERIFICATION_DASHBOARD_TITLE", "BioLink Verification Dashboard").strip()
    or "BioLink Verification Dashboard"
)
VERIFICATION_DASHBOARD_SLUG = (
    os.getenv("SUPERSET_VERIFICATION_DASHBOARD_SLUG", "biolink-verification-dashboard").strip()
    or "biolink-verification-dashboard"
)
OVERVIEW_DASHBOARD_TITLE = "BioLink Cohort Overview"
OVERVIEW_DASHBOARD_SLUG = "biolink-cohort-overview"
WORKFLOW_DASHBOARD_TITLE = "BioLink Workflow Coverage"
WORKFLOW_DASHBOARD_SLUG = "biolink-workflow-coverage"
PIE_VIZ_TYPE = "pie"
BIG_NUMBER_VIZ_TYPE = "big_number_total"
SUPERSET_DATABASE_NAME = os.getenv("SUPERSET_DATABASE_NAME", "BioLink PostgreSQL")
SUPERSET_DATABASE_SCHEMA = os.getenv("SUPERSET_DATABASE_SCHEMA", "public")
LEGACY_PIPELINE_DATASET_TABLES = (
    "_schema_registry",
    "harmonization_tiers",
    "harmonization_provenance",
)
NON_PUBLIC_DATASET_TABLES = ()
VERIFICATION_DATASET_TABLES = (
    "unified_registry",
    "bhs_participants",
    "ehvol_participants",
    "comparability_report",
    "cohort_characterization",
)


def _pie_chart_params(groupby: str) -> dict[str, Any]:
    return {
        "groupby": [groupby],
        "metric": "count",
        "row_limit": 1000,
        "showLegend": True,
        "legendType": "scroll",
        "donut": False,
        "innerRadius": 30,
        "outerRadius": 70,
        "labelType": "key",
        "colorScheme": "supersetColors",
    }


def _big_number_params(subheader: str) -> dict[str, Any]:
    return {
        "metric": "count",
        "y_axis_format": "SMART_NUMBER",
        "subheader": subheader,
        "header_font_size": 0.4,
    }


VERIFICATION_CHART_SPECS = (
    {
        "slice_name": "BioLink Verification Total Records",
        "table_name": "unified_registry",
        "viz_type": BIG_NUMBER_VIZ_TYPE,
        "params": _big_number_params("Registry records"),
    },
    {
        "slice_name": "BioLink Verification Records by Cohort",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("cohort"),
    },
    {
        "slice_name": "BioLink Verification Records by Source Dataset",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("source_dataset"),
    },
    {
        "slice_name": "BioLink Verification Characterization Rows",
        "table_name": "cohort_characterization",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("dataset_source"),
    },
)
OVERVIEW_CHART_SPECS = (
    {
        "slice_name": "BioLink Overview Total Records",
        "table_name": "unified_registry",
        "viz_type": BIG_NUMBER_VIZ_TYPE,
        "params": _big_number_params("Total participants"),
    },
    {
        "slice_name": "BioLink Overview Records by Cohort",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("cohort"),
    },
    {
        "slice_name": "BioLink Overview Records by Source Dataset",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("source_dataset"),
    },
    {
        "slice_name": "BioLink Overview Gender Distribution",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("gender"),
    },
    {
        "slice_name": "BioLink Overview Hypertension Status",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("hypertension_diagnosis"),
    },
    {
        "slice_name": "BioLink Overview Diabetes Status",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("diabetes_diagnosis"),
    },
    {
        "slice_name": "BioLink Overview Hyperlipidemia Status",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("hyperlipidemia_diagnosis"),
    },
    {
        "slice_name": "BioLink Overview Angina Symptoms",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("angina_symptom"),
    },
)
WORKFLOW_CHART_SPECS = (
    {
        "slice_name": "BioLink Workflow Consent Obtained",
        "table_name": "unified_registry",
        "viz_type": BIG_NUMBER_VIZ_TYPE,
        "params": _big_number_params("Registry records"),
    },
    {
        "slice_name": "BioLink Workflow ECG Agreement",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("agree_ecg_ecg"),
    },
    {
        "slice_name": "BioLink Workflow TTE Agreement",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("agree_undergo_tte_admin"),
    },
    {
        "slice_name": "BioLink Workflow CT Agreement",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("agree_ct_ct"),
    },
    {
        "slice_name": "BioLink Workflow Carotid Duplex Agreement",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("agree_undergo_carotid_duplex_vascular"),
    },
    {
        "slice_name": "BioLink Workflow Cardiac MRI Availability",
        "table_name": "unified_registry",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("cardiac_mri_mri"),
    },
    {
        "slice_name": "BioLink Workflow Characterization Rows",
        "table_name": "cohort_characterization",
        "viz_type": PIE_VIZ_TYPE,
        "params": _pie_chart_params("dataset_source"),
    },
)
SEEDED_DASHBOARD_SPECS = (
    {
        "title": VERIFICATION_DASHBOARD_TITLE,
        "slug": VERIFICATION_DASHBOARD_SLUG,
        "id_hint": VERIFICATION_DASHBOARD_ID_HINT,
        "layout_key": "verification",
        "chart_specs": VERIFICATION_CHART_SPECS,
    },
    {
        "title": OVERVIEW_DASHBOARD_TITLE,
        "slug": OVERVIEW_DASHBOARD_SLUG,
        "id_hint": "",
        "layout_key": "overview",
        "chart_specs": OVERVIEW_CHART_SPECS,
    },
    {
        "title": WORKFLOW_DASHBOARD_TITLE,
        "slug": WORKFLOW_DASHBOARD_SLUG,
        "id_hint": "",
        "layout_key": "workflow",
        "chart_specs": WORKFLOW_CHART_SPECS,
    },
)


def _database_uri() -> str:
    host = os.getenv("BIOLINK_PG_HOST", "postgres")
    port = os.getenv("BIOLINK_PG_PORT", "5432")
    database = os.getenv("BIOLINK_PG_DB", "biolink")
    user = os.getenv("BIOLINK_PG_USER", "biolink")
    password = os.getenv("BIOLINK_PG_PASSWORD", "biolink_secret")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def _normalize_identifier(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_sqlalchemy_uri(value: str | None) -> str:
    return _normalize_identifier(value).replace("+psycopg2", "")


def _ensure_biolink_database(db: Any) -> Any:
    from superset.commands.database.create import CreateDatabaseCommand
    from superset.models.core import Database

    target_name = _normalize_identifier(SUPERSET_DATABASE_NAME)
    target_uri = _normalize_sqlalchemy_uri(_database_uri())

    existing_databases = db.session.query(Database).all()
    for database in existing_databases:
        if _normalize_identifier(database.database_name) == target_name:
            return database

    for database in existing_databases:
        if _normalize_sqlalchemy_uri(database.sqlalchemy_uri_decrypted) == target_uri:
            return database

    created = CreateDatabaseCommand(
        {
            "database_name": SUPERSET_DATABASE_NAME,
            "sqlalchemy_uri": _database_uri(),
            "expose_in_sqllab": True,
            "allow_ctas": False,
            "allow_dml": False,
            "allow_cvas": False,
        }
    ).run()
    logger.info("Created Superset database %s", SUPERSET_DATABASE_NAME)
    return created


def _ensure_dataset(
    db: Any,
    database: Any,
    owner_id: int,
    schema: str,
    table_name: str,
) -> Any:
    from superset.commands.dataset.create import CreateDatasetCommand
    from superset.connectors.sqla.models import SqlaTable

    dataset = (
        db.session.query(SqlaTable)
        .filter(SqlaTable.database_id == database.id)
        .filter(SqlaTable.schema == schema)
        .filter(SqlaTable.table_name == table_name)
        .first()
    )
    if dataset is None:
        try:
            dataset = CreateDatasetCommand(
                {
                    "database": database.id,
                    "schema": schema,
                    "table_name": table_name,
                    "owners": [owner_id],
                }
            ).run()
            logger.info("Created Superset dataset %s.%s", schema, table_name)
            return dataset
        except Exception as exc:
            logger.warning("Could not create Superset dataset %s.%s: %s", schema, table_name, exc)
            return None

    metadata_result = dataset.fetch_metadata()
    if metadata_result.added or metadata_result.removed or metadata_result.modified:
        logger.info(
            "Refreshed Superset dataset %s.%s (added=%s removed=%s modified=%s)",
            schema,
            table_name,
            len(metadata_result.added),
            len(metadata_result.removed),
            len(metadata_result.modified),
        )
    return dataset


def _sync_chart(
    db: Any,
    admin_user: Any,
    dataset: Any,
    slice_name: str,
    viz_type: str,
    params: dict[str, Any],
) -> tuple[Any, bool]:
    from flask import g
    from superset.commands.chart.create import CreateChartCommand
    from superset.models.slice import Slice

    serialized_params = json.dumps(params)
    chart = (
        db.session.query(Slice)
        .filter(Slice.slice_name == slice_name)
        .order_by(Slice.id.asc())
        .first()
    )
    if chart is None:
        g.user = admin_user
        chart = CreateChartCommand(
            {
                "slice_name": slice_name,
                "viz_type": viz_type,
                "params": serialized_params,
                "datasource_id": dataset.id,
                "datasource_type": "table",
                "owners": [admin_user.id],
            }
        ).run()
        logger.info("Created verification chart %s (id=%s)", slice_name, chart.id)
        return chart, True

    updated = False
    desired_owners = {admin_user.id}
    current_owners = {owner.id for owner in chart.owners}
    if chart.viz_type != viz_type:
        chart.viz_type = viz_type
        updated = True
    if chart.params != serialized_params:
        chart.params = serialized_params
        updated = True
    if chart.datasource_type != "table" or chart.datasource_id != dataset.id:
        chart.datasource_type = "table"
        chart.datasource_id = dataset.id
        updated = True
    if current_owners != desired_owners:
        chart.owners = [admin_user]
        updated = True

    if updated:
        chart.slice_name = slice_name
        chart.last_saved_by = admin_user
        chart.last_saved_at = datetime.now()
        logger.info("Updated verification chart %s (id=%s)", slice_name, chart.id)

    return chart, updated


def _dashboard_position(charts: list[Any], layout_key: str) -> dict[str, Any]:
    position = {
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {
            "type": "GRID",
            "id": "GRID_ID",
            "children": [],
            "parents": ["ROOT_ID"],
        },
    }

    charts_per_row = 2
    for row_index in range(0, len(charts), charts_per_row):
        row_charts = charts[row_index : row_index + charts_per_row]
        row_id = f"ROW-{layout_key}-{(row_index // charts_per_row) + 1}"
        position["GRID_ID"]["children"].append(row_id)
        position[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": [],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
        }

        width = 12 // max(len(row_charts), 1)
        for chart in row_charts:
            component_id = f"CHART-{layout_key}-{chart.id}"
            position[row_id]["children"].append(component_id)
            meta = {
                "chartId": chart.id,
                "height": 45,
                "sliceName": chart.slice_name,
                "width": width,
            }
            chart_uuid = getattr(chart, "uuid", None)
            if chart_uuid:
                meta["uuid"] = str(chart_uuid)
            position[component_id] = {
                "type": "CHART",
                "id": component_id,
                "children": [],
                "meta": meta,
                "parents": ["ROOT_ID", "GRID_ID", row_id],
            }

    return position


def _dashboard_id_hint(raw_hint: str) -> int | None:
    if raw_hint.isdigit():
        return int(raw_hint)
    return None


def _ensure_dashboard(
    db: Any,
    admin_user: Any,
    *,
    title: str,
    slug: str,
    id_hint: str,
) -> tuple[Any, bool]:
    from superset.models.dashboard import Dashboard

    dashboard = None

    if slug:
        dashboard = (
            db.session.query(Dashboard)
            .filter(Dashboard.slug == slug)
            .order_by(Dashboard.id.asc())
            .first()
        )

    dashboard_id_hint = _dashboard_id_hint(id_hint)
    if dashboard is None and dashboard_id_hint is not None:
        dashboard = db.session.query(Dashboard).get(dashboard_id_hint)

    if dashboard is None and title:
        dashboard = (
            db.session.query(Dashboard)
            .filter(Dashboard.dashboard_title == title)
            .order_by(Dashboard.id.asc())
            .first()
        )

    if dashboard is None:
        dashboard = Dashboard(
            dashboard_title=title,
            slug=slug,
            position_json=json.dumps(_empty_dashboard_position()),
            json_metadata="{}",
            published=True,
        )
        dashboard.owners = [admin_user]
        db.session.add(dashboard)
        db.session.flush()
        logger.info(
            "Created Superset dashboard %s (slug=%s id=%s)",
            dashboard.dashboard_title,
            dashboard.slug,
            dashboard.id,
        )
        return dashboard, True

    updated = False
    desired_owners = {admin_user.id}
    current_owners = {owner.id for owner in dashboard.owners}

    if dashboard.dashboard_title != title:
        dashboard.dashboard_title = title
        updated = True
    if dashboard.slug != slug:
        dashboard.slug = slug
        updated = True
    if current_owners != desired_owners:
        dashboard.owners = [admin_user]
        updated = True
    if not dashboard.position_json:
        dashboard.position_json = json.dumps(_empty_dashboard_position())
        updated = True
    if not dashboard.json_metadata:
        dashboard.json_metadata = "{}"
        updated = True
    if not dashboard.published:
        dashboard.published = True
        updated = True

    return dashboard, updated


def _prune_legacy_pipeline_assets(db: Any, database: Any) -> None:
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.slice import Slice

    legacy_datasets = (
        db.session.query(SqlaTable)
        .filter(SqlaTable.database_id == database.id)
        .filter(SqlaTable.schema == SUPERSET_DATABASE_SCHEMA)
        .filter(SqlaTable.table_name.in_(LEGACY_PIPELINE_DATASET_TABLES + NON_PUBLIC_DATASET_TABLES))
        .all()
    )
    if not legacy_datasets:
        logger.info("No legacy pipeline datasets found in Superset metadata")
        return

    legacy_dataset_ids = {dataset.id for dataset in legacy_datasets}
    legacy_charts = (
        db.session.query(Slice)
        .filter(Slice.datasource_type == "table")
        .filter(Slice.datasource_id.in_(legacy_dataset_ids))
        .all()
    )

    removed_chart_names: list[str] = []
    for chart in legacy_charts:
        removed_chart_names.append(chart.slice_name)
        db.session.delete(chart)

    removed_dataset_names: list[str] = []
    for dataset in legacy_datasets:
        removed_dataset_names.append(dataset.table_name)
        db.session.delete(dataset)

    db.session.commit()
    logger.info(
        "Pruned Superset datasets outside the public analytics surface: datasets=%s charts=%s",
        ", ".join(sorted(removed_dataset_names)) or "none",
        ", ".join(sorted(removed_chart_names)) or "none",
    )


def _seed_dashboards(app: Any, db: Any) -> None:
    try:
        from flask import g

        admin_username = os.getenv("SUPERSET_ADMIN_USER", "admin")
        admin_user = app.appbuilder.sm.find_user(username=admin_username)
        if admin_user is None:
            logger.warning(
                "Superset init could not find admin user %s; skipping verification chart seed",
                admin_username,
            )
            return

        g.user = admin_user
        database = _ensure_biolink_database(db)
        _prune_legacy_pipeline_assets(db, database)

        dataset_tables = {
            spec["table_name"]
            for dashboard_spec in SEEDED_DASHBOARD_SPECS
            for spec in dashboard_spec["chart_specs"]
        }
        dataset_tables.update(VERIFICATION_DATASET_TABLES)

        datasets = {
            table_name: _ensure_dataset(
                db,
                database,
                admin_user.id,
                SUPERSET_DATABASE_SCHEMA,
                table_name,
            )
            for table_name in dataset_tables
        }

        for dashboard_spec in SEEDED_DASHBOARD_SPECS:
            dashboard, dashboard_updated = _ensure_dashboard(
                db,
                admin_user,
                title=dashboard_spec["title"],
                slug=dashboard_spec["slug"],
                id_hint=dashboard_spec["id_hint"],
            )

            charts: list[Any] = []
            dashboard_changed = dashboard_updated
            for spec in dashboard_spec["chart_specs"]:
                dataset = datasets.get(spec["table_name"])
                if dataset is None:
                    logger.warning(
                        "Skipping chart %s: dataset table %s is not available",
                        spec["slice_name"],
                        spec["table_name"],
                    )
                    continue
                chart, updated = _sync_chart(
                    db,
                    admin_user,
                    dataset,
                    spec["slice_name"],
                    spec["viz_type"],
                    spec["params"],
                )
                charts.append(chart)
                dashboard_changed = dashboard_changed or updated

            target_chart_ids = [chart.id for chart in charts]
            current_chart_ids = [chart.id for chart in dashboard.slices or []]
            target_position = _dashboard_position(charts, dashboard_spec["layout_key"])
            current_position = json.loads(dashboard.position_json or "{}")

            if current_chart_ids != target_chart_ids:
                dashboard.slices = charts
                dashboard_changed = True
            if current_position != target_position:
                dashboard.position_json = json.dumps(target_position)
                dashboard_changed = True
            if not dashboard.published:
                dashboard.published = True
                dashboard_changed = True

            db.session.commit()
            if dashboard_changed:
                logger.info(
                    "Seeded Superset dashboard %s (slug=%s id=%s) with charts %s",
                    dashboard.dashboard_title,
                    dashboard.slug,
                    dashboard.id,
                    ", ".join(str(chart_id) for chart_id in target_chart_ids),
                )
            else:
                logger.info(
                    "Superset dashboard %s (slug=%s id=%s) already matched the seeded chart set",
                    dashboard.dashboard_title,
                    dashboard.slug,
                    dashboard.id,
                )
    except Exception as exc:
        db.session.rollback()
        logger.warning("Superset init could not seed dashboards: %s", exc)


def _empty_dashboard_position() -> dict[str, Any]:
    return {
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": []},
    }


def _filter_removed_children(position: dict[str, Any], removed_ids: set[str]) -> None:
    for component in position.values():
        if not isinstance(component, dict):
            continue
        children = component.get("children")
        if isinstance(children, list):
            component["children"] = [child for child in children if child not in removed_ids]


def _remove_orphaned_chart_components(
    position: dict[str, Any],
    valid_chart_ids: set[int],
) -> tuple[dict[str, Any], list[int]]:
    cleaned_position = json.loads(json.dumps(position))
    removed_component_ids: set[str] = set()
    removed_chart_ids: list[int] = []

    for component_id, component in list(cleaned_position.items()):
        if not isinstance(component, dict):
            continue
        if component.get("type") != "CHART":
            continue

        chart_id = component.get("meta", {}).get("chartId")
        if isinstance(chart_id, str) and chart_id.isdigit():
            chart_id = int(chart_id)

        if isinstance(chart_id, int) and chart_id in valid_chart_ids:
            continue

        removed_component_ids.add(component_id)
        if isinstance(chart_id, int):
            removed_chart_ids.append(chart_id)
        cleaned_position.pop(component_id, None)

    if not removed_component_ids:
        return position, []

    _filter_removed_children(cleaned_position, removed_component_ids)

    while True:
        empty_layout_ids = {
            component_id
            for component_id, component in cleaned_position.items()
            if isinstance(component, dict)
            if component_id != "ROOT_ID"
            and component.get("type") in LAYOUT_CONTAINER_TYPES
            and not component.get("children")
        }
        if not empty_layout_ids:
            break
        for component_id in empty_layout_ids:
            cleaned_position.pop(component_id, None)
        _filter_removed_children(cleaned_position, empty_layout_ids)

    root = cleaned_position.get("ROOT_ID")
    if not isinstance(root, dict) or not root.get("children"):
        cleaned_position = _empty_dashboard_position()

    return cleaned_position, removed_chart_ids


def _ensure_embedded_guest_permissions(app: Any, db: Any) -> None:
    try:
        security_manager = app.appbuilder.sm
        guest_role_name = app.config.get("GUEST_ROLE_NAME", "Public")
        guest_role = security_manager.find_role(guest_role_name)

        if guest_role is None:
            logger.warning(
                "Superset guest role %s not found; skipping embedded permission bootstrap",
                guest_role_name,
            )
            return

        granted_permissions: list[str] = []
        for permission_name, view_name in EMBEDDED_GUEST_PERMISSIONS:
            permission_view = security_manager.find_permission_view_menu(
                permission_name,
                view_name,
            )
            if permission_view is None:
                permission_view = security_manager.add_permission_view_menu(
                    permission_name,
                    view_name,
                )

            if permission_view not in guest_role.permissions:
                security_manager.add_permission_role(guest_role, permission_view)
                granted_permissions.append(f"{permission_name}::{view_name}")

        if granted_permissions:
            db.session.commit()
            logger.info(
                "Granted embedded guest permissions to %s: %s",
                guest_role_name,
                ", ".join(granted_permissions),
            )
        else:
            logger.info(
                "Embedded guest permissions already present for role %s",
                guest_role_name,
            )
    except Exception as exc:
        logger.warning("Superset init could not bootstrap embedded guest permissions: %s", exc)


def _cleanup_orphaned_dashboard_layouts(db: Any) -> None:
    try:
        from superset.models.dashboard import Dashboard

        cleaned_dashboards: list[tuple[int, str, list[int]]] = []
        dashboards = db.session.query(Dashboard).all()
        for dashboard in dashboards:
            if not dashboard.position_json:
                continue

            try:
                position = json.loads(dashboard.position_json)
            except json.JSONDecodeError:
                logger.warning(
                    "Skipping dashboard %s due to invalid position_json",
                    dashboard.id,
                )
                continue

            valid_chart_ids = {chart.id for chart in dashboard.slices or []}
            cleaned_position, removed_chart_ids = _remove_orphaned_chart_components(
                position,
                valid_chart_ids,
            )
            if not removed_chart_ids:
                continue

            dashboard.position_json = json.dumps(cleaned_position)
            cleaned_dashboards.append(
                (dashboard.id, dashboard.dashboard_title or "Untitled dashboard", removed_chart_ids)
            )

        if cleaned_dashboards:
            db.session.commit()
            for dashboard_id, title, removed_chart_ids in cleaned_dashboards:
                logger.info(
                    "Removed orphaned chart references from dashboard %s (%s): %s",
                    dashboard_id,
                    title,
                    ", ".join(str(chart_id) for chart_id in removed_chart_ids),
                )
        else:
            logger.info("No orphaned dashboard chart components detected")
    except Exception as exc:
        logger.warning("Superset init could not clean orphaned dashboard components: %s", exc)


def _run_superset_bootstrap() -> None:
    try:
        from superset.app import create_app
        from superset.extensions import db

        app = create_app()
        with app.app_context():
            _ensure_embedded_guest_permissions(app, db)
            _cleanup_orphaned_dashboard_layouts(db)
            _seed_dashboards(app, db)
    except Exception as exc:
        logger.warning("Superset init bootstrap failed: %s", exc)


def _ensure_pipeline_tables_in_pg() -> None:
    try:
        engine = create_engine(_database_uri(), pool_pre_ping=True)
        with engine.begin() as conn:
            comp_exists = conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'comparability_report')")
            ).scalar()
            if not comp_exists:
                comp_candidates = [
                    Path("/app/outputs/comparability_report.json"),
                    Path("/app/db/test/data/processed/comparability_report.json"),
                    Path("outputs/comparability_report.json"),
                    Path("db/test/data/processed/comparability_report.json"),
                ]
                for path in comp_candidates:
                    if path.exists():
                        report_data = json.loads(path.read_text(encoding="utf-8"))
                        conn.execute(
                            text("CREATE TABLE IF NOT EXISTS public.comparability_report (id BIGSERIAL PRIMARY KEY, report JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
                        )
                        conn.execute(
                            text("INSERT INTO public.comparability_report (report) VALUES (:report)"),
                            {"report": json.dumps(report_data)},
                        )
                        logger.info("Loaded comparability_report table into PostgreSQL from %s", path)
                        break

            char_exists = conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'cohort_characterization')")
            ).scalar()
            if not char_exists:
                char_candidates = [
                    Path("/app/outputs/cohort_characterization.csv"),
                    Path("/app/db/test/data/processed/cohort_characterization.csv"),
                    Path("outputs/cohort_characterization.csv"),
                    Path("db/test/data/processed/cohort_characterization.csv"),
                ]
                for path in char_candidates:
                    if path.exists():
                        with path.open(encoding="utf-8") as f:
                            reader = csv.DictReader(f)
                            rows = list(reader)
                            cols = reader.fieldnames or []
                        if cols:
                            col_names = ", ".join(['"' + c.replace('"', '""') + '"' for c in cols])
                            col_params = ", ".join([":" + c for c in cols])
                            col_defs = ", ".join(['"' + c.replace('"', '""') + '" TEXT' for c in cols])
                            conn.execute(text(f"CREATE TABLE IF NOT EXISTS public.cohort_characterization ({col_defs})"))
                            insert_stmt = text(f"INSERT INTO public.cohort_characterization ({col_names}) VALUES ({col_params})")
                            for row in rows:
                                conn.execute(insert_stmt, row)
                            logger.info("Loaded cohort_characterization table into PostgreSQL from %s", path)
                        break
        engine.dispose()
    except Exception as exc:
        logger.warning("Failed to auto-provision pipeline tables in PostgreSQL: %s", exc)


def main() -> None:
    upload_folder = Path(os.getenv("SUPERSET_UPLOAD_FOLDER", "/tmp/superset_uploads"))
    upload_folder.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured Superset upload folder exists at %s", upload_folder)

    _ensure_pipeline_tables_in_pg()
    _run_superset_bootstrap()

    try:
        engine = create_engine(_database_uri(), pool_pre_ping=True)
        with engine.connect() as conn:
            ehvol_count = conn.execute(text("SELECT COUNT(*) FROM public.ehvol_participants")).scalar()
            registry_count = conn.execute(text("SELECT COUNT(*) FROM public.unified_registry")).scalar()
        engine.dispose()
        logger.info(
            "BioLink source database reachable from Superset init: ehvol_participants=%s unified_registry=%s",
            ehvol_count,
            registry_count,
        )
        logger.info(
            "Superset datasets and verification charts are provisioned during init for the active BioLink pipeline tables."
        )
    except Exception as exc:
        logger.warning("Superset init preflight could not verify BioLink source DB: %s", exc)


if __name__ == "__main__":
    main()

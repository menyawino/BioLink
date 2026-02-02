from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings
from app.services.superset_client import SupersetClient
import aiohttp

router = APIRouter()


class SupersetProgrammaticRequest(BaseModel):
    chart_title: str = "Gender Distribution"
    dashboard_title: str = "Programmatic Dashboard"
    viz_type: str = "bar"
    group_by: str = "gender"
    metric: str = "count"
    table_name: str | None = None
    schema: str | None = None
    create_dashboard: bool = True


class SupersetDashboardEmbedRequest(BaseModel):
    dashboard_id: int


@router.post("/programmatic")
async def create_programmatic_chart(req: SupersetProgrammaticRequest):
    client = SupersetClient.from_settings()

    table_name = req.table_name or settings.superset_default_table
    schema = req.schema or settings.superset_default_schema
    if not table_name:
        raise HTTPException(status_code=400, detail="Missing table_name and no default configured")

    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        try:
            tokens = await client.bootstrap()
            access_token = tokens["access_token"]
            csrf_token = tokens["csrf_token"]

            database_id = await client.get_or_create_database(
                session,
                access_token,
                csrf_token,
                settings.superset_database_name,
                settings.superset_database_uri,
            )

            dataset_id = await client.get_or_create_dataset(
                session,
                access_token,
                csrf_token,
                database_id,
                schema,
                table_name,
            )

            params = {
                "groupby": [req.group_by],
                "metrics": [req.metric],
                "row_limit": 1000,
                "show_legend": True,
                "color_scheme": "supersetColors"
            }

            chart_id = await client.create_chart(
                session,
                access_token,
                csrf_token,
                dataset_id,
                req.chart_title,
                req.viz_type,
                params,
            )

            dashboard_id = await client.create_dashboard(
                session,
                access_token,
                csrf_token,
                req.dashboard_title,
            )
            try:
                await client.add_chart_to_dashboard(
                    session,
                    access_token,
                    csrf_token,
                    dashboard_id,
                    chart_id,
                )
            except Exception:
                # If chart attachment fails, still return an embeddable dashboard token.
                pass

            resources = [{"type": "dashboard", "id": str(dashboard_id)}]
            guest_token = await client.create_guest_token(
                session,
                access_token,
                csrf_token,
                resources,
            )

            return {
                "success": True,
                "data": {
                    "chart_id": chart_id,
                    "dashboard_id": dashboard_id,
                    "guest_token": guest_token,
                    "superset_domain": settings.superset_public_url,
                }
            }
        except Exception as exc:
            import traceback
            traceback_str = traceback.format_exc()
            print("Superset programmatic error:\n", traceback_str)
            raise HTTPException(status_code=500, detail=str(exc))


@router.post("/embed/dashboard")
async def create_dashboard_embed(req: SupersetDashboardEmbedRequest):
    client = SupersetClient.from_settings()

    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
        try:
            tokens = await client.bootstrap()
            access_token = tokens["access_token"]
            csrf_token = tokens["csrf_token"]

            resources = [{"type": "dashboard", "id": str(req.dashboard_id)}]
            guest_token = await client.create_guest_token(
                session,
                access_token,
                csrf_token,
                resources,
            )

            return {
                "success": True,
                "data": {
                    "dashboard_id": req.dashboard_id,
                    "guest_token": guest_token,
                    "superset_domain": settings.superset_public_url,
                }
            }
        except Exception as exc:
            import traceback
            traceback_str = traceback.format_exc()
            print("Superset dashboard embed error:\n", traceback_str)
            raise HTTPException(status_code=500, detail=str(exc))

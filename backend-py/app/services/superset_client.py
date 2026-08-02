from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json
from urllib.parse import quote
import aiohttp
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def _dashboard_api_path(dashboard_id_or_slug: str | int, suffix: str = "") -> str:
    dashboard_ref = str(dashboard_id_or_slug).strip()
    if not dashboard_ref:
        raise ValueError("dashboard_id_or_slug must not be empty")
    return f"/api/v1/dashboard/{quote(dashboard_ref, safe='')}{suffix}"


@dataclass
class SupersetClient:
    base_url: str
    username: str
    password: str
    _csrf_cookie: str | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_settings(cls) -> "SupersetClient":
        return cls(
            base_url=settings.superset_url.rstrip("/"),
            username=settings.superset_admin_user,
            password=settings.superset_admin_password,
        )

    async def _login(self, session: aiohttp.ClientSession) -> str:
        payload = {
            "username": self.username,
            "password": self.password,
            "provider": "db",
            "refresh": True,
        }
        async with session.post(
            f"{self.base_url}/api/v1/security/login", json=payload
        ) as resp:
            data = await resp.json()
            logger.info("Superset login response type=%s", type(data))
            logger.info(
                "Superset login response keys=%s",
                list(data.keys()) if isinstance(data, dict) else str(data)[:200],
            )
            access_token = data.get("access_token") if isinstance(data, dict) else None
            if not access_token:
                raise RuntimeError(f"Superset login failed: {data}")
            return access_token

    async def _csrf(self, session: aiohttp.ClientSession, access_token: str) -> str:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with session.get(
            f"{self.base_url}/api/v1/security/csrf_token/", headers=headers
        ) as resp:
            data = await resp.json()
            logger.info("Superset csrf response type=%s", type(data))
            logger.info(
                "Superset csrf response keys=%s",
                list(data.keys()) if isinstance(data, dict) else str(data)[:200],
            )
            # Debug cookies present in session after csrf call
            try:
                cookies = session.cookie_jar.filter_cookies(self.base_url)
                logger.info(
                    "Superset session cookies after csrf: %s",
                    {k: v.value for k, v in cookies.items()},
                )
                if "session" in cookies:
                    self._csrf_cookie = f"session={cookies['session'].value}"
            except Exception:
                logger.exception("Failed to read session cookies")

            if isinstance(data, dict):
                result = data.get("result")
                if isinstance(result, dict):
                    return result.get("csrf_token") or data.get("csrf_token")
                if isinstance(result, str):
                    return result
                return data.get("csrf_token")
            return None

    async def _request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        path: str,
        access_token: str,
        csrf_token: str | None = None,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        if csrf_token:
            headers.update({"X-CSRFToken": csrf_token})
        # Ensure cookies are explicitly included in headers (helps when redirects or domain differences occur)
        try:
            if self._csrf_cookie:
                headers["Cookie"] = self._csrf_cookie
                logger.info(
                    "Superset request will include csrf cookie: %s", self._csrf_cookie
                )
            else:
                cookies = session.cookie_jar.filter_cookies(self.base_url)
                if cookies:
                    cookie_header = "; ".join(
                        f"{k}={v.value}" for k, v in cookies.items()
                    )
                    headers.setdefault("Cookie", cookie_header)
                    logger.info(
                        "Superset request will include cookies: %s", cookie_header
                    )
        except Exception:
            logger.exception("Failed to build cookie header for Superset request")

        # Sanitize Authorization header for logging
        log_headers = {
            k: ("REDACTED" if k.lower() == "authorization" else v)
            for k, v in headers.items()
        }
        logger.info(
            "Superset request: %s %s headers=%s body=%s",
            method,
            path,
            log_headers,
            json_body,
        )

        # Ensure Referer is provided to satisfy CSRF checks
        headers.setdefault("Referer", f"{self.base_url}/")
        # X-Requested-With is often required by servers to identify AJAX requests for CSRF checks
        headers.setdefault("X-Requested-With", "XMLHttpRequest")
        async with session.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            json=json_body,
            params=params,
        ) as resp:
            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                logger.error("Failed parsing Superset response as JSON: %s", text[:400])
                data = text
            if resp.status >= 400:
                raise RuntimeError(f"Superset API error {resp.status}: {data}")
            return data

    @staticmethod
    def _extract_id(payload: dict) -> int | None:
        if isinstance(payload, dict):
            if isinstance(payload.get("id"), int):
                return payload["id"]
            if isinstance(payload.get("result"), dict) and isinstance(
                payload["result"].get("id"), int
            ):
                return payload["result"]["id"]
        return None

    @staticmethod
    def _extract_result_dict(payload: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        result = payload.get("result")
        if isinstance(result, dict):
            return result
        return None

    @staticmethod
    def _normalize_identifier(value: Any) -> str:
        return str(value or "").strip().lower()

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.isdigit():
                return int(stripped)
        return None

    @classmethod
    def _dataset_database_id(cls, item: dict[str, Any]) -> int | None:
        raw_database = item.get("database")
        if isinstance(raw_database, dict):
            for key in ("id", "value", "database_id"):
                database_id = cls._coerce_int(raw_database.get(key))
                if database_id is not None:
                    return database_id

        database_id = cls._coerce_int(raw_database)
        if database_id is not None:
            return database_id

        return cls._coerce_int(item.get("database_id"))

    async def _list_resource(
        self, session: aiohttp.ClientSession, access_token: str, resource: str
    ) -> list[dict]:
        params = {"q": "(page:0,page_size:200)"}
        data = await self._request(
            session, "GET", f"/api/v1/{resource}/", access_token, params=params
        )
        return data.get("result") or []

    async def list_datasets(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
    ) -> list[dict]:
        return await self._list_resource(session, access_token, "dataset")

    async def get_or_create_database(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        name: str,
        uri: str,
    ) -> int:
        existing = await self._list_resource(session, access_token, "database")
        for item in existing:
            if item.get("database_name") == name:
                return int(item["id"])

        payload = {
            "database_name": name,
            "sqlalchemy_uri": uri,
            "expose_in_sqllab": True,
            "allow_ctas": False,
            "allow_dml": False,
            "allow_cvas": False,
        }
        created = await self._request(
            session,
            "POST",
            "/api/v1/database/",
            access_token,
            csrf_token,
            json_body=payload,
        )
        db_id = self._extract_id(created)
        if db_id is None:
            raise RuntimeError(f"Failed to create Superset database: {created}")
        return db_id

    async def get_or_create_dataset(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        database_id: int,
        schema: str,
        table_name: str,
    ) -> int:
        normalized_schema = self._normalize_identifier(schema)
        normalized_table_name = self._normalize_identifier(table_name)
        existing = await self.list_datasets(session, access_token)
        for item in existing:
            existing_database_id = self._dataset_database_id(item)
            if existing_database_id is not None and existing_database_id != database_id:
                continue
            if self._normalize_identifier(item.get("table_name")) != normalized_table_name:
                continue
            if self._normalize_identifier(item.get("schema")) != normalized_schema:
                continue

            dataset_id = self._coerce_int(item.get("id"))
            if dataset_id is not None:
                return dataset_id

        payload = {"database": database_id, "schema": schema, "table_name": table_name}
        created = await self._request(
            session,
            "POST",
            "/api/v1/dataset/",
            access_token,
            csrf_token,
            json_body=payload,
        )
        dataset_id = self._extract_id(created)
        if dataset_id is None:
            raise RuntimeError(f"Failed to create Superset dataset: {created}")
        return dataset_id

    async def refresh_dataset(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        dataset_id: int,
    ) -> dict:
        return await self._request(
            session,
            "PUT",
            f"/api/v1/dataset/{dataset_id}/refresh",
            access_token,
            csrf_token,
        )

    async def delete_dataset(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        dataset_id: int,
    ) -> None:
        await self._request(
            session,
            "DELETE",
            f"/api/v1/dataset/{dataset_id}",
            access_token,
            csrf_token,
        )

    async def create_chart(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        dataset_id: int,
        slice_name: str,
        viz_type: str,
        params: dict[str, Any],
    ) -> int:
        payload = {
            "slice_name": slice_name,
            "viz_type": viz_type,
            "params": json.dumps(params),
            "datasource_id": dataset_id,
            "datasource_type": "table",
        }
        created = await self._request(
            session,
            "POST",
            "/api/v1/chart/",
            access_token,
            csrf_token,
            json_body=payload,
        )
        chart_id = self._extract_id(created)
        if chart_id is None:
            raise RuntimeError(f"Failed to create Superset chart: {created}")
        return chart_id

    async def create_dashboard(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        title: str,
    ) -> int:
        payload = {"dashboard_title": title, "published": True}
        created = await self._request(
            session,
            "POST",
            "/api/v1/dashboard/",
            access_token,
            csrf_token,
            json_body=payload,
        )
        dashboard_id = self._extract_id(created)
        if dashboard_id is None:
            raise RuntimeError(f"Failed to create Superset dashboard: {created}")
        return dashboard_id

    async def get_or_create_dashboard(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        title_or_slug: str | int,
    ) -> int | str:
        ref_str = str(title_or_slug).strip()
        dashboards = await self._list_resource(session, access_token, "dashboard")
        for d in dashboards:
            if str(d.get("id")) == ref_str or d.get("slug") == ref_str or d.get("dashboard_title") == ref_str:
                return int(d["id"])

        payload = {
            "dashboard_title": ref_str.replace("-", " ").replace("_", " ").title(),
            "slug": ref_str if not ref_str.isdigit() else None,
            "published": True,
        }
        try:
            created = await self._request(
                session,
                "POST",
                "/api/v1/dashboard/",
                access_token,
                csrf_token,
                json_body=payload,
            )
            dashboard_id = self._extract_id(created)
            if dashboard_id is None:
                raise RuntimeError(f"Failed to create Superset dashboard: {created}")
            return dashboard_id
        except RuntimeError as exc:
            if "slug" in str(exc).lower() or "must be unique" in str(exc).lower():
                logger.info("Dashboard slug '%s' already exists; returning reference", ref_str)
                return ref_str
            raise

    async def get_dashboard(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        dashboard_id_or_slug: str | int,
    ) -> dict[str, Any]:
        dashboard = await self._request(
            session,
            "GET",
            _dashboard_api_path(dashboard_id_or_slug),
            access_token,
        )
        result = self._extract_result_dict(dashboard)
        if not isinstance(result, dict):
            raise RuntimeError(f"Failed to load dashboard details: {dashboard}")
        return result

    async def get_dashboard_embed_uuid(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        dashboard_id_or_slug: str | int,
    ) -> str:
        dashboard_id = await self.get_or_create_dashboard(
            session, access_token, csrf_token, dashboard_id_or_slug
        )
        embedded = await self.ensure_embedded_dashboard(
            session,
            access_token,
            csrf_token,
            dashboard_id,
            settings.superset_embedded_allowed_domains_list,
        )
        embedded_uuid = str(embedded.get("uuid") or "").strip()
        if not embedded_uuid:
            raise RuntimeError(
                f"Dashboard {dashboard_id_or_slug} does not expose an embedded dashboard UUID"
            )
        return embedded_uuid

    async def get_embedded_dashboard(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        dashboard_id_or_slug: str | int,
    ) -> dict[str, Any] | None:
        try:
            embedded = await self._request(
                session,
                "GET",
                _dashboard_api_path(dashboard_id_or_slug, "/embedded"),
                access_token,
            )
        except RuntimeError as exc:
            if "Superset API error 404" in str(exc):
                return None
            raise

        result = self._extract_result_dict(embedded)
        if not isinstance(result, dict):
            raise RuntimeError(
                f"Failed to load embedded dashboard config for {dashboard_id_or_slug}: {embedded}"
            )
        return result

    async def ensure_embedded_dashboard(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        dashboard_id_or_slug: str | int,
        allowed_domains: list[str],
    ) -> dict[str, Any]:
        existing = await self.get_embedded_dashboard(
            session,
            access_token,
            dashboard_id_or_slug,
        )
        if existing is not None:
            existing_domains = [
                str(domain).strip() for domain in existing.get("allowed_domains", [])
            ]
            if existing_domains == allowed_domains:
                return existing

            updated = await self._request(
                session,
                "PUT",
                _dashboard_api_path(dashboard_id_or_slug, "/embedded"),
                access_token,
                csrf_token,
                json_body={"allowed_domains": allowed_domains},
            )
            result = self._extract_result_dict(updated)
            if not isinstance(result, dict):
                raise RuntimeError(
                    f"Failed to update embedded dashboard config for {dashboard_id_or_slug}: {updated}"
                )
            return result

        created = await self._request(
            session,
            "POST",
            _dashboard_api_path(dashboard_id_or_slug, "/embedded"),
            access_token,
            csrf_token,
            json_body={"allowed_domains": allowed_domains},
        )
        result = self._extract_result_dict(created)
        if not isinstance(result, dict):
            raise RuntimeError(
                f"Failed to create embedded dashboard config for {dashboard_id_or_slug}: {created}"
            )
        return result

    async def add_chart_to_dashboard(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        dashboard_id: int,
        chart_id: int,
    ) -> None:
        result = await self.get_dashboard(session, access_token, dashboard_id)

        chart_key = f"CHART-{chart_id}"
        position = {
            "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
            "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["ROW_ID"]},
            "ROW_ID": {
                "type": "ROW",
                "id": "ROW_ID",
                "children": [chart_key],
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
            },
            chart_key: {
                "type": "CHART",
                "id": chart_key,
                "children": [],
                "meta": {"chartId": chart_id, "height": 50, "width": 4},
            },
        }

        json_metadata = result.get("json_metadata")
        if isinstance(json_metadata, dict):
            json_metadata = json.dumps(json_metadata)
        if not json_metadata:
            json_metadata = "{}"

        payload = {
            "dashboard_title": result.get("dashboard_title")
            or result.get("dashboard_title"),
            "slug": result.get("slug"),
            "position_json": json.dumps(position),
            "json_metadata": json_metadata,
            "published": result.get("published", True),
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        await self._request(
            session,
            "PUT",
            f"/api/v1/dashboard/{dashboard_id}",
            access_token,
            csrf_token,
            json_body=payload,
        )

    async def create_guest_token(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        csrf_token: str,
        resources: list[dict[str, Any]],
    ) -> str:
        payload = {
            "user": {
                "username": "embed_user",
                "first_name": "Embed",
                "last_name": "User",
            },
            "resources": resources,
            "rls": [],
        }
        created = await self._request(
            session,
            "POST",
            "/api/v1/security/guest_token",
            access_token,
            csrf_token,
            json_body=payload,
        )
        token = created.get("token") or created.get("result", {}).get("token")
        if not token:
            raise RuntimeError(f"Failed to create Superset guest token: {created}")
        return token

    async def bootstrap(self) -> dict[str, str]:
        async with aiohttp.ClientSession() as session:
            access_token = await self._login(session)
            csrf_token = await self._csrf(session, access_token)
            return {"access_token": access_token, "csrf_token": csrf_token}

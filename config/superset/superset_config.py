import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def _parse_origin_list(*env_var_names: str) -> list[str]:
    origins: list[str] = []
    for env_var_name in env_var_names:
        raw_value = os.getenv(env_var_name, "")
        for entry in raw_value.split(","):
            origin = entry.strip().rstrip("/")
            if origin and origin not in origins:
                origins.append(origin)
    return origins


def _env_bool(env_var_name: str, default: bool) -> bool:
    raw_value = os.getenv(env_var_name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _apply_metadata_schema(database_uri: str, metadata_schema: str) -> str:
    if not database_uri or not metadata_schema:
        return database_uri

    parts = urlsplit(database_uri)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    options = query.get("options", "").strip()
    search_path_option = f"-csearch_path={metadata_schema}"

    if search_path_option not in options.split():
        query["options"] = f"{options} {search_path_option}".strip()

    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


EMBED_ALLOWED_ORIGINS = _parse_origin_list(
    "SUPERSET_EMBEDDED_ALLOWED_DOMAINS",
    "CORS_ALLOWED_ORIGINS",
) or [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

SUPERSET_METADATA_SCHEMA = os.getenv("SUPERSET_METADATA_SCHEMA", "superset_meta").strip()
SQLALCHEMY_DATABASE_URI = _apply_metadata_schema(
    os.getenv(
        "SUPERSET_METADATA_DATABASE_URI",
        "postgresql+psycopg2://biolink:biolink_secret@postgres:5432/biolink",
    ),
    SUPERSET_METADATA_SCHEMA,
)
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

# Enable embedded dashboards/charts via guest tokens
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True
}

# Enable CSV upload UI/handlers in Superset
FEATURE_FLAGS.update({
    "CSV_UPLOAD": True,
})

# Basic security settings for local/dev
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "biolink-superset-secret")
TALISMAN_ENABLED = _env_bool("SUPERSET_TALISMAN_ENABLED", True)
WTF_CSRF_ENABLED = True
ENABLE_PROXY_FIX = True
ENABLE_CORS = True

TALISMAN_CONFIG = {
    "content_security_policy": {
        "base-uri": ["'self'"],
        "default-src": ["'self'"],
        "img-src": ["'self'", "blob:", "data:", "https:"],
        "worker-src": ["'self'", "blob:"],
        "connect-src": ["'self'", "https:", "http:", "ws:", "wss:"],
        "object-src": ["'none'"],
        "style-src": ["'self'", "'unsafe-inline'", "https:"],
        "font-src": ["'self'", "data:", "https:"],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        "frame-ancestors": ["'self'", *EMBED_ALLOWED_ORIGINS],
    },
    "force_https": False,
    "frame_options": None,
    "session_cookie_secure": False,
}
TALISMAN_DEV_CONFIG = TALISMAN_CONFIG

# Keep Superset's own CORS allowlist aligned with the embed-domain settings.
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": EMBED_ALLOWED_ORIGINS,
}

# Avoid Flask-Limiter's in-memory fallback in containerized runs.
RATELIMIT_STORAGE_URI = os.getenv(
    "SUPERSET_RATELIMIT_STORAGE_URI",
    "redis://redis:6379/1",
)

# Branding
APP_NAME = "BioLink Visualize"
APP_ICON = "/static/assets/images/custom_logo_v2.png"
APP_ICON_WIDTH = 69
APP_ICON_HEIGHT = 24
APP_FAVICON = "/static/assets/images/custom_img_favicon.png"

# Theme (Ant Design v5 tokens)
ENABLE_UI_THEME_ADMINISTRATION = False
THEME_DEFAULT = {
    "token": {
        "colorPrimary": "#00a2dd",
        "colorInfo": "#00a2dd",
        "colorSuccess": "#34d399",
        "colorWarning": "#efb01b",
        "colorError": "#e9322b",
        "colorTextBase": "#030213",
        "colorTextSecondary": "#717182",
        "colorBgBase": "#ffffff",
        "colorBgLayout": "#ffffff",
        "colorBgContainer": "#ffffff",
        "colorBorder": "rgba(0, 0, 0, 0.1)",
        "borderRadius": 10,
        "fontFamily": "ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif",
    },
    "echartsOptionsOverrides": {
        "color": ["#00a2dd", "#efb01b", "#e9322b", "#6b7280", "#34d399"],
        "textStyle": {
            "color": "#030213",
            "fontFamily": "ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif",
        },
        "legend": {
            "textStyle": {
                "color": "#030213",
            }
        },
    },
}

THEME_DARK = {
    "algorithm": "dark",
    "token": {
        "colorPrimary": "#00a2dd",
        "colorInfo": "#00a2dd",
        "colorSuccess": "#34d399",
        "colorWarning": "#efb01b",
        "colorError": "#e9322b",
        "fontFamily": "ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif",
    },
}

# File upload settings
UPLOAD_FOLDER = os.getenv("SUPERSET_UPLOAD_FOLDER", "/tmp/superset_uploads")
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception:
    # best-effort directory creation; container may handle this
    pass

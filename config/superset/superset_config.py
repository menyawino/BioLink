import os

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
TALISMAN_ENABLED = False
WTF_CSRF_ENABLED = True
ENABLE_PROXY_FIX = True

# Allow embedding from local frontend origins
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
}

# Branding
APP_NAME = "BioLink Visualize"
APP_ICON = "/static/assets/images/custom_logo.png"
APP_ICON_WIDTH = 32
APP_ICON_HEIGHT = 32
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

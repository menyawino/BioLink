import os

# Enable embedded dashboards/charts via guest tokens
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True
}

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

from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    port: int = 3001
    host: str = "0.0.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    log_json_format: bool = False
    cors_allowed_origins: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:3000"
    )

    # Database
    database_url: str = "postgresql://biolink:biolink_secret@localhost:5432/biolink"

    # Mistral API & Ollama LLM provider
    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"
    ollama_orchestrator_model: str = "qwen2.5:14b"
    ollama_data_model: str = "qwen2.5:14b"
    ollama_medical_model: str = "qwen2.5:14b"
    ollama_coding_model: str = "qwen2.5:14b"
    sql_agent_default_limit: int = 200
    llm_max_retries: int = 2
    llm_retry_backoff_s: float = 0.4
    llm_retry_jitter_s: float = 0.2
    orchestrator_llm_timeout_s: float = 120.0
    data_llm_timeout_s: float = 120.0
    medical_llm_timeout_s: float = 120.0

    # RAG / pgvector
    rag_pg_url: str = (
        "postgresql://biolink:biolink_secret@localhost:5433/biolink_vector"
    )
    rag_embedding_model: str = "nomic-embed-text"
    rag_embedding_dim: int = 768
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 5

    # Superset (programmatic charts + embed)
    superset_url: str = "http://localhost:8088"
    superset_public_url: str = "http://localhost:8088"
    superset_admin_user: str = "admin"
    superset_admin_password: str = "admin"
    superset_admin_email: str = "admin@biolink.local"
    superset_admin_firstname: str = "Bio"
    superset_admin_lastname: str = "Link"
    superset_database_name: str = "BioLink PostgreSQL"
    superset_legacy_database_names: str = "BioLink"
    superset_database_uri: str = (
        "postgresql://biolink:biolink_secret@localhost:5432/biolink"
    )
    superset_default_schema: str = "public"
    superset_default_table: str = "unified_registry"
    superset_default_dashboard_ref: str = "biolink-verification-dashboard"
    superset_embedded_allowed_domains: str = ""

    # NiFi ETL API
    etl_service_url: str = "https://nifi:8443/nifi-api"

    # Auth / JWT
    secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Accept legacy postgres:// and ensure a psycopg2 driver is specified for SQLAlchemy
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql://", 1)
        if value.startswith("postgresql://") and "+" not in value.split("://", 1)[0]:
            value = value.replace("postgresql://", "postgresql+psycopg2://", 1)
        return value

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        origins: list[str] = []
        for raw_origin in str(self.cors_allowed_origins).split(","):
            origin = raw_origin.strip().rstrip("/")
            if origin and origin not in origins:
                origins.append(origin)
        return origins

    @staticmethod
    def _normalize_origin(value: str) -> str:
        raw_value = value.strip().rstrip("/")
        if not raw_value:
            return ""

        parsed = urlparse(raw_value)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
        return raw_value.lower()

    @classmethod
    def _unique_origins(cls, values: list[str]) -> list[str]:
        origins: list[str] = []
        for raw_value in values:
            origin = cls._normalize_origin(raw_value)
            if origin and origin not in origins:
                origins.append(origin)
        return origins

    @property
    def superset_embedded_allowed_domains_list(self) -> list[str]:
        configured = self._unique_origins(
            str(self.superset_embedded_allowed_domains).split(",")
        )
        if configured:
            return configured
        return self._unique_origins(self.cors_allowed_origins_list)

    @staticmethod
    def _has_localhost_hostname(url: str) -> bool:
        hostname = urlparse(url).hostname
        return hostname in {"localhost", "127.0.0.1"}

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment.lower() not in {"production", "staging"}:
            return self

        if (
            not self.secret_key
            or "change-me-in-production" in self.secret_key
            or "change-in-production" in self.secret_key
            or self.secret_key.startswith("${SECRET_KEY:-")
        ):
            raise ValueError(
                "SECRET_KEY must be set to a strong deployment-specific value when ENVIRONMENT is production or staging"
            )

        if self._has_localhost_hostname(self.superset_public_url):
            raise ValueError(
                "SUPERSET_PUBLIC_URL must point to a public hostname when ENVIRONMENT is production or staging"
            )

        return self

settings = Settings()

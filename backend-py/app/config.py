from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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

    # Database
    database_url: str = "postgresql://biolink:biolink_secret@localhost:5432/biolink"

    # Ollama / LangChain SQL agent
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_orchestrator_model: str = "llama3.2:3b"
    ollama_data_model: str = "llama3.2:3b"
    ollama_medical_model: str = "llama3.2:3b"
    ollama_coding_model: str = "llama3.2:3b"
    sql_agent_default_limit: int = 200
    llm_max_retries: int = 2
    llm_retry_backoff_s: float = 0.4
    llm_retry_jitter_s: float = 0.2
    orchestrator_llm_timeout_s: float = 8.0
    data_llm_timeout_s: float = 20.0
    medical_llm_timeout_s: float = 20.0

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
    superset_database_name: str = "BioLink"
    superset_database_uri: str = (
        "postgresql://biolink:biolink_secret@localhost:5432/biolink"
    )
    superset_default_schema: str = "public"
    superset_default_table: str = "EHVOL"

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

settings = Settings()

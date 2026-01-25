from pydantic_settings import BaseSettings
from pydantic import field_validator, Field, AliasChoices
from typing import Optional

class Settings(BaseSettings):
    # Server
    port: int = 3001
    host: str = "0.0.0.0"
    environment: str = "development"
    
    # Database
    database_url: str = "postgresql://biolink:biolink_secret@localhost:5432/biolink"
    
    # Ollama / LangChain SQL agent
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    sql_agent_default_limit: int = 200

    # SQL Server (EHVol registry)
    sqlserver_host: str = "localhost"
    sqlserver_port: int = 1433
    sqlserver_db: str = "EHVol"
    sqlserver_user: str = "readonly_user"
    sqlserver_password: str = "readonly_password"
    sqlserver_driver: str = "ODBC Driver 18 for SQL Server"
    sqlserver_trust_cert: str = "yes"

    # RAG / pgvector
    rag_pg_url: str = "postgresql://biolink:biolink_secret@localhost:5433/biolink_vector"
    rag_embedding_model: str = "nomic-embed-text"
    rag_embedding_dim: int = 768
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 5

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Accept legacy postgres:// and ensure a psycopg2 driver is specified for SQLAlchemy
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql://", 1)
        if value.startswith("postgresql://") and "+" not in value.split("://", 1)[0]:
            value = value.replace("postgresql://", "postgresql+psycopg2://", 1)
        return value
    
    class Config:
        env_file = (".env", "../.env")
        case_sensitive = False
        extra = "ignore"

settings = Settings()

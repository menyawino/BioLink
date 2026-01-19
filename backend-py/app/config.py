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
    
    # Azure OpenAI (for fallback chat)
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-5-nano"
    azure_api_version: str = "2024-10-21"
    
    # Azure AI Foundry (Agent Framework)
    azure_existing_agent_id: str = Field(default="blnk", validation_alias=AliasChoices("AZURE_EXISTING_AGENT_ID", "AGENT_ID"))
    azure_existing_aiproject_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_EXISTING_AIPROJECT_ENDPOINT", "PROJECT_ENDPOINT")
    )
    azure_existing_aiproject_resource_id: str = ""
    azure_existing_resource_id: str = ""
    azure_subscription_id: str = ""
    azure_env_name: str = "agents-playground-3547"
    azure_location: str = "swedencentral"
    azure_foundry_api_version: str = "v1"
    model_deployment_name: str = Field(default="", validation_alias=AliasChoices("MODEL_DEPLOYMENT_NAME", "AZURE_OPENAI_DEPLOYMENT"))
    azure_agent_responses_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_AGENT_RESPONSES_ENDPOINT", "AZURE_RESPONSES_ENDPOINT")
    )
    azure_agent_responses_api_version: str = Field(
        default="2025-11-15-preview",
        validation_alias=AliasChoices("AZURE_AGENT_RESPONSES_API_VERSION", "AZURE_RESPONSES_API_VERSION")
    )
    azd_allow_non_empty_folder: Optional[str] = None

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

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    project_name: str = "Music Curator API"
    version: str = "3.0.0"
    
    # Internal APIs
    pocketbase_url: str = "http://127.0.0.1:8090" # Used as default if internal env not supplied
    pocketbase_admin_email: str
    pocketbase_admin_password: str
    
    # External APIs
    lm_studio_url: str = "http://localhost:1234/v1" # Overridden by LM_STUDIO_URL env var
    llm_model_name: str = "openai/gpt-oss-20b"
    
    # Internal Paths
    nas_mount_path: str
    ingest_base_path: str
    ingest_dirs: str = "yubal,tidal-dl,adhoc" # Keep as comma separated string for env inject
    media_library_path: str
    
    # Security: Explicit CORS allowlist to prevent unauthorized cross-origin requests
    cors_allowed_origins: str | list[str] = "http://localhost:3000,http://127.0.0.1:3000"

    @field_validator("cors_allowed_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if not v.startswith("["):
                return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()

from pydantic import field_validator
from typing import Union, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str = "Music Curator API"
    version: str = "3.0.0"
    
    # Internal APIs
    pocketbase_url: str = "http://127.0.0.1:8090" # Used as default if internal env not supplied
    cors_origins: Union[str, List[str]] = ["http://localhost:8090", "http://127.0.0.1:8090"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
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
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Union, List
import json

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
    
    cors_allowed_origins: Union[str, List[str]] = ["http://127.0.0.1:8090", "http://localhost:3000"]

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()

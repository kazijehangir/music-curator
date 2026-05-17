from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str = "Music Curator API"
    cors_allowed_origins: str | list[str] = "http://127.0.0.1:8090,http://localhost:3000"

    @model_validator(mode="after")
    def assemble_cors_origins(self):
        if isinstance(self.cors_allowed_origins, str):
            self.cors_allowed_origins = [i.strip() for i in self.cors_allowed_origins.split(",") if i.strip()]
        return self
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
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()

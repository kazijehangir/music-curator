from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str = "Music Curator API"
    version: str = "3.0.0"
    
    # Internal APIs
    pocketbase_url: str = "http://127.0.0.1:8090"
    pocketbase_admin_email: str = "admin@example.com"
    pocketbase_admin_password: str = "changeme123"
    
    # External APIs
    ollama_url: str = "http://10.0.2.100:5000"
    
    # Internal Paths
    nas_mount_path: str = "/mnt/user/main"
    ingest_dirs: list[str] = ["yubal", "tidal-dl", "adhoc"]
    media_library_path: str = "/mnt/user/main/media/Music"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Global settings instance
settings = Settings()

from pydantic import BaseModel, Field
from typing import Optional

class LLMMetadataResponse(BaseModel):
    title: Optional[str] = Field(None, description="The parsed, clean track title. Transliterated to Latin script if needed.")
    artist: Optional[str] = Field(None, description="The parsed, clean artist name. Transliterated to Latin script if needed. Multiple artists separated by comma.")
    album: Optional[str] = Field(None, description="The parsed, clean album name. Transliterated to Latin script if needed.")
    genre: Optional[str] = Field(None, description="The inferred or extracted genre (e.g., Qawwali, Ghazal, Pop, etc).")
    language: Optional[str] = Field(None, description="The ISO 639-3 code for the primary language (e.g., urd, pan, hin, eng).")

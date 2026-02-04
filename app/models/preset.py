from pydantic import BaseModel
from typing import Optional

class LLMPresetCreate(BaseModel):
    name: str
    base_url: str
    model: str
    api_key: Optional[str] = ""

class LLMPresetResponse(LLMPresetCreate):
    id: int

    class Config:
        from_attributes = True

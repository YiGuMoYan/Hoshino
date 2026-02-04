from pydantic import BaseModel, Field
from typing import Optional, List

class AnimeNamingResult(BaseModel):
    anime_title: str
    year: Optional[int] = None
    season: int = 1
    episode: int
    cour: int = 1
    part: Optional[int] = None
    original_name: str = Field(..., description="原始文件名，用于映射回源文件")
    rename_to: str
    confidence: float = Field(..., ge=0, le=1)
    
class BatchNamingResult(BaseModel):
    results: List[AnimeNamingResult]

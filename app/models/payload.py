from pydantic import BaseModel, Field
from typing import List, Optional

class Context(BaseModel):
    media_type: str = Field(default="japanese_tv_anime", description="媒体类型")
    preferred_standard: str = Field(default="jellyfin", description="目标命名标准")
    language: str = Field(default="zh_CN", description="首选语言")

class AnimeCandidates(BaseModel):
    title: Optional[str] = Field(None, description="已知或猜测的动画标题")
    year: Optional[int] = Field(None, description="已知或猜测的发行年份")

class FileNode(BaseModel):
    name: str = Field(..., description="文件名")
    size_mb: float = Field(..., description="文件大小 (MB)")
    rel_path: str = Field(..., description="相对扫描根目录的路径")

class AnimeNamingPayload(BaseModel):
    context: Context
    anime_candidates: AnimeCandidates
    files: List[FileNode]

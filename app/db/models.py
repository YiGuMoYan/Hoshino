from sqlalchemy import Column, String, Integer, Boolean, Text, JSON, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Setting(Base):
    """Key-value settings with metadata for dynamic form generation"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)  # e.g., "app.language"
    value = Column(Text, default="")  # Stored as string
    name = Column(String, nullable=False)  # Display name: "系统语言"
    class_type = Column(String, nullable=False)  # "text", "password", "select", "number", "textarea"
    options = Column(Text)  # JSON string for select options
    category = Column(String, index=True)  # "app", "llm", "tmdb"
    description = Column(Text)  # Help text
    order = Column(Integer, default=0)  # Display order

# Legacy models - will be removed after migration


class LLMConfig(Base):
    __tablename__ = "llm_config"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, default="openai") # openai, ollama...
    api_key = Column(String, default="")
    base_url = Column(String, default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = Column(String, default="qwen-plus")

class LLMPreset(Base):
    __tablename__ = "llm_presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    base_url = Column(String)
    model = Column(String)
    api_key = Column(String) # Optional default key for the preset

class DownloadTask(Base):
    """Download tasks with metadata hints for auto-archiving"""
    __tablename__ = "download_tasks"

    info_hash = Column(String, primary_key=True)  # Torrent Hash
    name = Column(String) # Display Name
    save_path = Column(String) # Save Path
    status = Column(String, default="downloading")  # downloading, organizing, completed, failed
    
    # Metadata Hints (JSON)
    # { "series_name": "Frieren", "season": 2, "episode_offset": 0, "is_collection": False }
    extra_vars = Column(JSON, default={}) 

    error_message = Column(String, nullable=True)
    log = Column(Text, nullable=True) # Execution logs
    seeding_time = Column(Integer, default=-1) # -1: system default, 0: no seed, >0: minutes
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "info_hash": self.info_hash,
            "name": self.name,
            "save_path": self.save_path,
            "status": self.status,
            "extra_vars": self.extra_vars,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "seeding_time": self.seeding_time
        }

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    mikan_id = Column(String, nullable=False, index=True)  # Mikan 番剧 ID
    title = Column(String, nullable=False)  # 番剧标题
    cover_url = Column(String)  # 封面图片 URL
    rss_url = Column(String, nullable=False)  # RSS 订阅链接
    subgroup_id = Column(String)  # 字幕组 ID
    subgroup_name = Column(String)  # 字幕组名称
    
    # Bangumi 元数据（可选）
    bangumi_id = Column(Integer)  # Bangumi 番剧 ID
    bangumi_rating = Column(Float)  # Bangumi 评分
    bangumi_summary = Column(Text)  # 番剧简介
    bangumi_tags = Column(JSON, default=list)  # 标签列表
    
    # 过滤配置
    filter_keywords = Column(JSON, default=list)  # 包含关键词列表
    exclude_keywords = Column(JSON, default=list)  # 排除关键词列表
    filter_resolution = Column(String)  # 分辨率过滤（1080p, 720p, 4K 等）
    filter_regex = Column(String)  # 正则表达式过滤
    
    # 下载配置
    save_path = Column(String)  # 保存路径
    category = Column(String, default="hoshino")  # qBittorrent 分类
    auto_download = Column(Boolean, default=True)  # 是否自动下载
    extra_vars = Column(JSON, default=dict)  # 额外元数据（季号、集数偏移等）
    
    # 状态
    status = Column(String, default="active")  # active/paused/completed
    last_check_at = Column(DateTime)  # 最后检查时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RSSItem(Base):
    __tablename__ = "rss_items"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    
    guid = Column(String, unique=True, nullable=False, index=True)  # RSS 条目唯一标识
    title = Column(String, nullable=False)  # 标题
    magnet_link = Column(String)  # 磁力链接
    torrent_url = Column(String)  # 种子下载链接
    pub_date = Column(DateTime)  # 发布时间
    
    # 下载状态
    downloaded = Column(Boolean, default=False)  # 是否已下载
    download_task_id = Column(String, ForeignKey("download_tasks.info_hash"))  # 关联的下载任务
    renamed = Column(Boolean, default=False)  # 是否已重命名（避免重复扫描）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    subscription = relationship("Subscription", backref="rss_items")
    # download_task relationship is defined in DownloadTask via backref or we can add it here if needed,
    # but DownloadTask is already defined above.
    # Let's add backref to DownloadTask here.
    download_task = relationship("DownloadTask", backref="rss_item")

class LibraryItem(Base):
    """Scanned library items for poster wall"""
    __tablename__ = "library_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    path = Column(String, unique=True, index=True)
    poster_path = Column(String)  # Local image path or TMDB URL
    season_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    year = Column(String)  # Release Year "2023"
    status = Column(String) # "Returning Series", "Ended", etc.
    air_day = Column(Integer) # 0=Monday, 6=Sunday (ISO) or similar. TMDB gives string?
    tmdb_id = Column(Integer)
    bangumi_id = Column(Integer)
    vote_average = Column(Float)
    overview = Column(Text)
    is_subscribed = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "path": self.path,
            "poster_url": self.poster_path, 
            "season_count": self.season_count,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "year": self.year,
            "status": self.status,
            "air_day": self.air_day,
            "vote_average": self.vote_average,
            "overview": self.overview,
            "is_subscribed": self.is_subscribed,
            "bangumi_id": self.bangumi_id
        }

class BangumiEpisode(Base):
    """Cache for Bangumi episode metadata"""
    __tablename__ = "bangumi_episodes"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, index=True)
    sort = Column(Integer, index=True)
    name = Column(String)
    name_cn = Column(String)
    summary = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

class BangumiSubjectMapping(Base):
    """Maps LibraryItem + Season to Bangumi Subject ID"""
    __tablename__ = "bangumi_subject_mapping"
    
    item_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    subject_id = Column(Integer)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models import LLMPreset, Setting, LLMConfig
import os


# 数据库存储路径配置
# 优先使用环境变量，否则回退到项目根目录下的 data 文件夹
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.getenv("HOSHINO_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'hoshino.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed usage
    session = SessionLocal()
    try:
        # 1. Init Settings (Dynamic Key-Value)
        default_settings = [
            # App Category
            {"key": "app.language", "value": "zh_CN", "name": "系统语言", "class_type": "select", "options": '[{"value": "zh_CN", "label": "简体中文 (Chinese)"}, {"value": "en_US", "label": "English"}]', "category": "app", "description": "系统显示的语言", "order": 1},
            {"key": "app.theme", "value": "system", "name": "界面主题", "class_type": "select", "options": '[{"value": "system", "label": "跟随系统"}, {"value": "light", "label": "浅色模式"}, {"value": "dark", "label": "深色模式"}]', "category": "app", "description": "界面颜色主题", "order": 2},
            {"key": "app.target_library_path", "value": "/meida", "name": "目标媒体库路径", "class_type": "text", "options": None, "category": "app", "description": "整理后的动漫文件存放路径 (例如: /data/media/anime)", "order": 4},
            
            # TMDB Category
            {"key": "tmdb.api_key", "value": "", "name": "TMDB API Key", "class_type": "password", "options": None, "category": "tmdb", "description": "The Movie Database API Key", "order": 1},
            {"key": "tmdb.image_base_url", "value": "https://image.tmdb.org/t/p/original", "name": "图片源地址", "class_type": "text", "options": None, "category": "tmdb", "description": "TMDB 图片获取基地址", "order": 2},
            {"key": "tmdb.language", "value": "zh-CN", "name": "TMDB 查询语言", "class_type": "select", "options": '[{"value": "zh-CN", "label": "简体中文"}, {"value": "zh-TW", "label": "繁体中文"}, {"value": "ja-JP", "label": "日本語"}, {"value": "en-US", "label": "English"}]', "category": "tmdb", "description": "TMDB 查询时使用的语言", "order": 3},
            {"key": "tmdb.bearer_token", "value": "", "name": "TMDB Read Access Token", "class_type": "password", "options": None, "category": "tmdb", "description": "TMDB v4 Bearer Token (Recommended for better rate limits)", "order": 0},

             # Downloader Category
            {"key": "downloader.host", "value": "http://qbittorrent:8080", "name": "WebUI 地址", "class_type": "text", "options": None, "category": "downloader", "description": "qBittorrent Web API 地址 (例如 http://qbittorrent:8080)", "order": 1},
            {"key": "downloader.username", "value": "admin", "name": "用户名", "class_type": "text", "options": None, "category": "downloader", "description": "qBittorrent WebUI 用户名", "order": 2},
            {"key": "downloader.password", "value": "", "name": "密码", "class_type": "password", "options": None, "category": "downloader", "description": "qBittorrent WebUI 密码", "order": 3},
            {"key": "downloader.download_path", "value": "/media", "name": "默认下载路径", "class_type": "text", "options": None, "category": "downloader", "description": "qBittorrent 下载保存路径 (推荐 /media)", "order": 4},
            {"key": "downloader.seeding_time", "value": "-1", "name": "默认做种时间 (分钟)", "class_type": "number", "options": None, "category": "downloader", "description": "默认做种时间限制 (-1: 系统默认, 0: 不做种, >0: 分钟)", "order": 5},

            # Mikan Category (RSS)
            {"key": "mikan.check_interval", "value": "30", "name": "RSS 检查间隔 (分钟)", "class_type": "number", "options": None, "category": "mikan", "description": "定时检查 RSS 更新的时间间隔", "order": 1},
            {"key": "mikan.default_resolution", "value": "1080p", "name": "默认分辨率", "class_type": "select", "options": '["1080p", "720p", "4K", "Any"]', "category": "mikan", "description": "订阅时默认选择的分辨率偏好", "order": 2},
            {"key": "mikan.auto_download", "value": "true", "name": "自动下载", "class_type": "select", "options": '["true", "false"]', "category": "mikan", "description": "检测到新剧集时是否自动添加下载任务", "order": 3},

            # Bangumi Category
            {"key": "bangumi.enabled", "value": "false", "name": "启用 Bangumi 集成", "class_type": "select", "options": '["true", "false"]', "category": "bangumi", "description": "从 Bangumi 获取更详细的番剧元数据", "order": 1},
            {"key": "bangumi.api_key", "value": "", "name": "Bangumi Token", "class_type": "password", "options": None, "category": "bangumi", "description": "Bangumi 个人访问令牌 (可选)", "order": 2},
            
            # Legacy LLM keys in Settings (referenced in backup, syncing here just in case)
            {"key": "llm.provider", "value": "openai", "name": "LLM 提供商", "class_type": "select", "options": '[{"value": "openai", "label": "OpenAI Compatible"}, {"value": "ollama", "label": "Ollama"}]', "category": "llm", "description": "选择 LLM 服务提供商", "order": 1},
            {"key": "llm.api_key", "value": "", "name": "API 密钥", "class_type": "password", "options": None, "category": "llm", "description": "LLM API 密钥", "order": 2},
            {"key": "llm.base_url", "value": "https://api.openai.com/v1", "name": "API Base URL", "class_type": "text", "options": None, "category": "llm", "description": "LLM API 端点地址", "order": 3},
            {"key": "llm.model", "value": "gpt-4-turbo", "name": "模型名称", "class_type": "text", "options": None, "category": "llm", "description": "使用的 LLM 模型名称", "order": 4},
        ]

        for setting_data in default_settings:
            # Check by key to avoid duplicates
            if not session.query(Setting).filter_by(key=setting_data["key"]).first():
                setting = Setting(**setting_data)
                session.add(setting)

        # 2. Init LLMConfig
        if not session.query(LLMConfig).first():
            default_llm = LLMConfig(
                provider="openai",
                api_key="",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                model="qwen-plus"
            )
            session.add(default_llm)

        # 3. Init LLMPresets
        presets = [
             {
                "name": "Aliyun DashScope",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen-plus",
                "api_key": ""
            },
            {
                "name": "DeepSeek",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "api_key": ""
            },
             {
                "name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4-turbo",
                "api_key": ""
            }
        ]

        for p_data in presets:
            if not session.query(LLMPreset).filter_by(name=p_data["name"]).first():
                preset = LLMPreset(**p_data)
                session.add(preset)

        session.commit()
    finally:
        session.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

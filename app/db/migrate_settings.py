"""
Migration script to convert old settings to new key-value model
"""
from app.db.session import SessionLocal
from app.db.models import AppSettings, LLMConfig, Setting
import json

def migrate_settings():
    """Migrate existing settings to new key-value format"""
    db = SessionLocal()
    
    try:
        # Check if migration already done
        existing_settings = db.query(Setting).first()
        if existing_settings:
            print("Settings already migrated. Skipping...")
            return
        
        # Get existing data
        app_settings = db.query(AppSettings).first()
        llm_config = db.query(LLMConfig).first()
        
        # Define settings schema
        settings_schema = [
            # App Settings
            {
                "key": "app.language",
                "value": app_settings.language if app_settings else "zh_CN",
                "name": "系统语言",
                "class_type": "select",
                "options": json.dumps([
                    {"value": "zh_CN", "label": "简体中文 (Chinese)"},
                    {"value": "en_US", "label": "English"}
                ]),
                "category": "app",
                "description": "选择系统界面语言",
                "order": 1
            },
            {
                "key": "app.theme",
                "value": app_settings.theme if app_settings else "system",
                "name": "主题模式",
                "class_type": "select",
                "options": json.dumps([
                    {"value": "system", "label": "跟随系统"},
                    {"value": "light", "label": "浅色模式"},
                    {"value": "dark", "label": "深色模式"}
                ]),
                "category": "app",
                "description": "选择界面主题",
                "order": 2
            },
            {
                "key": "app.target_library_path",
                "value": "",
                "name": "目标媒体库路径",
                "class_type": "text",
                "options": None,
                "category": "app",
                "description": "整理后的动漫文件将移动到此目录",
                "order": 3
            },
            {
                "key": "tmdb.api_key",
                "value": app_settings.tmdb_api_key if app_settings else "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlOTRhZjQ0NWI1NWVkNjNjODIwMjIwOWEyMWIwODU4ZiIsIm5iZiI6MTczOTI0ODU5Ni4yNjEsInN1YiI6IjY3YWFkM2Q0ZGQ5YjdkMmVhYWIwOGE4ZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Wbjfu8U_xhyHtQFNCwV_M3qYuseA7r7kvdl_OARTypQ",
                "name": "TMDB API 密钥",
                "class_type": "password",
                "options": None,
                "category": "tmdb",
                "description": "用于搜索动漫元数据。在 https://www.themoviedb.org/settings/api 获取",
                "order": 1
            },
            # LLM Settings
            {
                "key": "llm.provider",
                "value": llm_config.provider if llm_config else "openai",
                "name": "LLM 提供商",
                "class_type": "select",
                "options": json.dumps([
                    {"value": "openai", "label": "OpenAI Compatible"},
                    {"value": "ollama", "label": "Ollama"}
                ]),
                "category": "llm",
                "description": "选择 LLM 服务提供商",
                "order": 1
            },
            {
                "key": "llm.api_key",
                "value": llm_config.api_key if llm_config else "",
                "name": "API 密钥",
                "class_type": "password",
                "options": None,
                "category": "llm",
                "description": "LLM API 密钥",
                "order": 2
            },
            {
                "key": "llm.base_url",
                "value": llm_config.base_url if llm_config else "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "name": "API Base URL",
                "class_type": "text",
                "options": None,
                "category": "llm",
                "description": "LLM API 端点地址",
                "order": 3
            },
            {
                "key": "llm.model",
                "value": llm_config.model if llm_config else "qwen-plus",
                "name": "模型名称",
                "class_type": "text",
                "options": None,
                "category": "llm",
                "description": "使用的 LLM 模型名称",
                "order": 4
            }
        ]
        
        # Create new settings
        for setting_data in settings_schema:
            setting = Setting(**setting_data)
            db.add(setting)
        
        db.commit()
        print(f"✓ Successfully migrated {len(settings_schema)} settings to new format")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_settings()

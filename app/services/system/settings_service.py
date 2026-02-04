"""
Settings service for type-safe access to key-value settings
"""
from typing import Optional, List, Dict, Any
from app.db.session import SessionLocal
from app.db.models import Setting
import json

class SettingsService:
    """Service for accessing and managing settings"""
    
    @staticmethod
    def get_setting(key: str, default: str = "") -> str:
        """Get a single setting value by key"""
        with SessionLocal() as db:
            setting = db.query(Setting).filter(Setting.key == key).first()
            return setting.value if setting else default
    
    @staticmethod
    def set_setting(key: str, value: str) -> bool:
        """Update a setting value"""
        with SessionLocal() as db:
            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = value
                db.commit()
                return True
            return False
    
    @staticmethod
    def get_settings_by_category(category: str) -> List[Dict[str, Any]]:
        """Get all settings for a category"""
        with SessionLocal() as db:
            settings = db.query(Setting).filter(
                Setting.category == category
            ).order_by(Setting.order).all()
            
            return [
                {
                    "id": s.id,
                    "key": s.key,
                    "value": s.value,
                    "name": s.name,
                    "class_type": s.class_type,
                    "options": json.loads(s.options) if s.options else None,
                    "category": s.category,
                    "description": s.description,
                    "order": s.order
                }
                for s in settings
            ]
    
    @staticmethod
    def get_all_settings() -> Dict[str, List[Dict[str, Any]]]:
        """Get all settings grouped by category"""
        with SessionLocal() as db:
            settings = db.query(Setting).order_by(Setting.category, Setting.order).all()
            
            # Group by category
            grouped = {}
            for s in settings:
                if s.category not in grouped:
                    grouped[s.category] = []
                
                grouped[s.category].append({
                    "id": s.id,
                    "key": s.key,
                    "value": s.value,
                    "name": s.name,
                    "class_type": s.class_type,
                    "options": json.loads(s.options) if s.options else None,
                    "category": s.category,
                    "description": s.description,
                    "order": s.order
                })
            
            return grouped
    
    @staticmethod
    def batch_update(updates: Dict[str, str]) -> bool:
        """Batch update multiple settings"""
        with SessionLocal() as db:
            try:
                for key, value in updates.items():
                    setting = db.query(Setting).filter(Setting.key == key).first()
                    if setting:
                        setting.value = value
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                print(f"Batch update failed: {e}")
                return False

    @staticmethod
    def initialize_defaults():
        """Initialize default settings if not exists"""
        defaults = [
            # Mikan Settings
            {
                "key": "mikan.check_interval",
                "value": "30",
                "name": "RSS 检查间隔 (分钟)",
                "class_type": "number",
                "category": "mikan",
                "description": "定时检查 RSS 更新的时间间隔",
                "order": 1
            },
            # Removed mikan.default_resolution as per user request

            {
                "key": "mikan.auto_download",
                "value": "true",
                "name": "自动下载",
                "class_type": "select",
                "options": json.dumps(["true", "false"]),
                "category": "mikan",
                "description": "检测到新剧集时是否自动添加下载任务",
                "order": 3
            },
            
            # Bangumi Settings
            {
                "key": "bangumi.enabled",
                "value": "false",
                "name": "启用 Bangumi 集成",
                "class_type": "select",
                "options": json.dumps(["true", "false"]),
                "category": "bangumi",
                "description": "从 Bangumi 获取更详细的番剧元数据 (简介、评分、标签)",
                "order": 1
            },
            {
                "key": "bangumi.api_key",
                "value": "",
                "name": "API Key",
                "class_type": "password",
                "category": "bangumi",
                "description": "Bangumi 个人访问令牌 (Access Token)，部分接口需要",
                "order": 2
            },
            
            # App Defaults (Ensure they exist)
            {
                "key": "app.language",
                "value": "zh_CN",
                "name": "系统语言",
                "class_type": "select",
                "options": json.dumps(["zh_CN", "en_US"]),
                "category": "app",
                "description": "Web 界面语言",
                "order": 1
            },
            {
                "key": "app.theme",
                "value": "system",
                "name": "主题模式",
                "class_type": "select",
                "options": json.dumps(["system", "light", "dark"]),
                "category": "app",
                "description": "界面颜色主题",
                "order": 2
            },
            {
                "key": "app.target_library_path",
                "value": "/downloads/anime",
                "name": "番剧库路径",
                "class_type": "text",
                "category": "app",
                "description": "默认的番剧归档根目录",
                "order": 3
            },
            
            # Notification Settings - Email
            {
                "key": "notification.email.enabled",
                "value": "false",
                "name": "启用邮件通知",
                "class_type": "select",
                "options": json.dumps(["true", "false"]),
                "category": "notification",
                "description": "是否开启邮件通知功能 (总开关)",
                "order": 1
            },
            {
                "key": "notification.email.smtp_host",
                "value": "",
                "name": "SMTP 服务器",
                "class_type": "text",
                "category": "notification",
                "description": "邮件服务器地址 (例如 smtp.gmail.com)",
                "order": 2
            },
            {
                "key": "notification.email.smtp_port",
                "value": "587",
                "name": "SMTP 端口",
                "class_type": "number",
                "category": "notification",
                "description": "邮件服务器端口 (通常 587 或 465)",
                "order": 3
            },
            {
                "key": "notification.email.smtp_user",
                "value": "",
                "name": "SMTP 用户名",
                "class_type": "text",
                "category": "notification",
                "description": "登录邮箱的账号",
                "order": 4
            },
            {
                "key": "notification.email.smtp_pass",
                "value": "",
                "name": "SMTP 密码",
                "class_type": "password",
                "category": "notification",
                "description": "邮箱密码或应用专用密码",
                "order": 5
            },
            {
                "key": "notification.email.sender_name",
                "value": "Hoshino Bot",
                "name": "发送者名称",
                "class_type": "text",
                "category": "notification",
                "description": "邮件中显示的发送者名字",
                "order": 6
            },
            {
                "key": "notification.email.receivers",
                "value": "",
                "name": "接收邮箱",
                "class_type": "text",
                "category": "notification",
                "description": "接收通知的邮箱地址 (多个用逗号分隔)",
                "order": 7
            },
            
            # Notification Feature Switches
            {
                "key": "notification.enable_subscription_update",
                "value": "true",
                "name": "通知：番剧订阅更新",
                "class_type": "select",
                "options": json.dumps(["true", "false"]),
                "category": "notification",
                "description": "当检测到新剧集并添加下载时发送通知",
                "order": 10
            },
            {
                "key": "notification.enable_download_complete",
                "value": "false",
                "name": "通知：下载任务完成",
                "class_type": "select",
                "options": json.dumps(["true", "false"]),
                "category": "notification",
                "description": "仅当下载任务完成（未归档）时发送通知",
                "order": 11
            },
            {
                "key": "notification.enable_archive_complete",
                "value": "true",
                "name": "通知：归档任务完成",
                "class_type": "select",
                "options": json.dumps(["true", "false"]),
                "category": "notification",
                "description": "当番剧自动归档整理完成后发送通知",
                "order": 12
            },
            {
                "key": "notification.enable_manual_rename",
                "value": "true",
                "name": "通知：需手动重命名",
                "class_type": "select",
                "options": json.dumps(["true", "false"]),
                "category": "notification",
                "description": "当自动重命名失败或需要人工干预时发送通知",
                "order": 13
            },
        ]
        
        with SessionLocal() as db:
            for item in defaults:
                existing = db.query(Setting).filter(Setting.key == item['key']).first()
                if not existing:
                    new_setting = Setting(
                        key=item['key'],
                        value=item['value'],
                        name=item['name'],
                        class_type=item['class_type'],
                        options=item.get('options'),
                        category=item['category'],
                        description=item.get('description'),
                        order=item['order']
                    )
                    db.add(new_setting)
            db.commit()


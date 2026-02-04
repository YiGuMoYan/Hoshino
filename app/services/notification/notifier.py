from app.services.system.settings_service import SettingsService
from app.services.notification.email_service import EmailService
from loguru import logger

class Notifier:
    """通知管理器，负责根据配置分发通知"""
    
    def __init__(self):
        self.settings = SettingsService()
        self.email_service = EmailService()
    
    def _is_email_enabled(self) -> bool:
        return self.settings.get_setting("notification.email.enabled") == "true"

    def notify_subscription_update(self, anime_title: str, episode_title: str):
        """番剧更新通知"""
        if not self._is_email_enabled():
            return
        
        if self.settings.get_setting("notification.enable_subscription_update") != "true":
            return

        subject = f"【番剧更新】{anime_title}"
        content = f"检测到新剧集并在自动下载中：\n\n番剧：{anime_title}\n剧集：{episode_title}\n\nHoshino Bot"
        
        self.email_service.send_email(subject, content)

    def notify_download_complete(self, task_name: str):
        """下载完成通知（未触发归档）"""
        if not self._is_email_enabled():
            return

        if self.settings.get_setting("notification.enable_download_complete") != "true":
            return
        
        subject = f"【下载完成】{task_name}"
        content = f"下载任务已完成：\n\n任务：{task_name}\n\n注意：此任务未触发自动归档整理。\n\nHoshino Bot"
        
        self.email_service.send_email(subject, content)

    def notify_archive_complete(self, task_name: str, logs: str = ""):
        """归档整理完成通知"""
        if not self._is_email_enabled():
            return

        if self.settings.get_setting("notification.enable_archive_complete") != "true":
            return
        
        subject = f"【归档完成】{task_name}"
        content = f"番剧归档整理已完成：\n\n源任务：{task_name}\n\n{logs}\n\nHoshino Bot"
        
        self.email_service.send_email(subject, content)

    def notify_manual_rename_needed(self, task_name: str, reason: str):
        """手动重命名提醒"""
        if not self._is_email_enabled():
            return
            
        if self.settings.get_setting("notification.enable_manual_rename") != "true":
            return
            
        subject = f"【需手动整理】{task_name}"
        content = f"自动归档失败或需要人工干预：\n\n任务：{task_name}\n原因：{reason}\n\n请手动检查重命名。\n\nHoshino Bot"
        
        self.email_service.send_email(subject, content)

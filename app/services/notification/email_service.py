import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from loguru import logger
from app.services.system.settings_service import SettingsService

class EmailService:
    def __init__(self):
        self.settings = SettingsService()

    def _get_config(self):
        """获取邮件配置"""
        return {
            "host": self.settings.get_setting("notification.email.smtp_host"),
            "port": int(self.settings.get_setting("notification.email.smtp_port", 587)),
            "user": self.settings.get_setting("notification.email.smtp_user"),
            "password": self.settings.get_setting("notification.email.smtp_pass"),
            "sender_name": self.settings.get_setting("notification.email.sender_name", "Hoshino Bot"),
            "receivers": self.settings.get_setting("notification.email.receivers", "")
        }

    def send_email(self, subject: str, content: str, to_addresses: list[str] = None) -> bool:
        """发送邮件"""
        config = self._get_config()
        
        # 基础校验
        if not config["host"] or not config["user"] or not config["password"]:
            logger.warning("Email configuration incomplete, skipping email.")
            return False

        receiver_list = []
        if to_addresses:
            receiver_list = to_addresses
        elif config["receivers"]:
            receiver_list = [r.strip() for r in config["receivers"].split(",") if r.strip()]
        
        if not receiver_list:
            logger.warning("No email receivers configured.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((config["sender_name"], config["user"]))
            msg['To'] = ",".join(receiver_list)
            msg['Subject'] = subject

            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            # 连接 SMTP 服务器
            # 尝试根据端口自适应 SSL/TLS
            if config["port"] == 465:
                # SSL
                server = smtplib.SMTP_SSL(config["host"], config["port"])
            else:
                # TLS
                server = smtplib.SMTP(config["host"], config["port"])
                server.starttls()
            
            server.login(config["user"], config["password"])
            server.sendmail(config["user"], receiver_list, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_test_email(self) -> bool:
        """发送测试邮件"""
        return self.send_email(
            subject="【Hoshino】邮件通知测试",
            content="这是一封来自 Hoshino 的测试邮件。如果您收到这封邮件，说明您的 SMTP 配置正确。"
        )

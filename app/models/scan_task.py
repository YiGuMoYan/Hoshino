from sqlalchemy import Column, String, DateTime, JSON, Integer
from app.db.base import Base
from datetime import datetime, timedelta
import uuid

def beijing_now():
    """获取北京时间（UTC+8）"""
    return datetime.utcnow() + timedelta(hours=8)

class ScanTask(Base):
    """扫描任务模型"""
    __tablename__ = "scan_tasks"
    
    # 基础信息
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    directory_path = Column(String, nullable=False)  # 扫描路径
    
    # 任务状态
    status = Column(String, default="pending")  # pending, running, completed, failed
    start_time = Column(DateTime, default=beijing_now)
    end_time = Column(DateTime, nullable=True)
    
    # 结果数据
    plan = Column(JSON, default=list)  # 重命名计划 (List[RenameItem])
    logs = Column(JSON, default=list)  # 日志列表 (List[LogEntry])
    
    # 执行状态
    executed = Column(Integer, default=0)  # 0=未执行, 1=已执行
    error_message = Column(String, nullable=True)
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "directory_path": self.directory_path,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "plan": self.plan,
            "logs": self.logs,
            "executed": bool(self.executed),
            "error_message": self.error_message,
            "file_count": len(self.plan) if self.plan else 0
        }

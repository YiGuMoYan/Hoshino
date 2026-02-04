"""扫描任务执行模块"""
from app.worker import huey
from app.db.session import SessionLocal
from app.models.scan_task import ScanTask, beijing_now
from app.services.core.organizer import OrganizerService
from datetime import datetime
import asyncio


@huey.task(name='execute_scan_task')
def execute_scan_task(task_id: str):
    """
    异步执行扫描任务
    
    Args:
        task_id: 任务 ID
    """
    db = SessionLocal()
    
    try:
        # 获取任务
        task = db.query(ScanTask).filter(ScanTask.id == task_id).first()
        if not task:
            print(f"Task {task_id} not found")
            return
        
        # 更新状态为运行中
        task.status = "running"
        db.commit()
        
        # 执行扫描
        organizer = OrganizerService()
        
        # 重写日志保存方法，直接保存到数据库
        original_add_log = organizer.add_log
        def add_log_to_db(message: str, level: str = "info"):
            original_add_log(message, level)
            # 保存到数据库
            if task.logs is None:
                task.logs = []
            
            # 创建新列表避免 SQLAlchemy 不检测变化
            logs_copy = list(task.logs) if task.logs else []
            logs_copy.append({
                "timestamp": beijing_now().isoformat(),
                "level": level,
                "message": message
            })
            task.logs = logs_copy
            
            # 标记为已修改并提交
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(task, "logs")
            db.commit()
            db.refresh(task)
        
        organizer.add_log = add_log_to_db
        
        # 执行扫描 (需要异步环境)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            plan = loop.run_until_complete(organizer.scan_directory(task.directory_path))
        finally:
            loop.close()
        
        # 保存结果
        task.plan = [
            {
                "original_path": item.original_path,
                "new_path": item.new_path,
                "status": item.status,
                "log": item.log,
                "anime_info": item.anime_info,
                "display_path": item.display_path
            }
            for item in plan
        ]
        task.status = "completed"
        task.end_time = beijing_now()
        db.commit()
        
        print(f"Task {task_id} completed successfully with {len(plan)} files")
        
    except Exception as e:
        # 记录错误
        try:
            task.status = "failed"
            task.error_message = str(e)
            task.end_time = beijing_now()
            db.commit()
        except:
            pass
        
        import traceback
        traceback.print_exc()
        print(f"Task {task_id} failed: {str(e)}")
    
    finally:
        db.close()

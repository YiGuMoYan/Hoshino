import os
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.services.core.organizer import OrganizerService, RenameItem
from app.services.system.deps import get_organizer_service
from app.services.system.settings_service import SettingsService
from app.services.core.file_organizer import FileOrganizer
from app.db.session import get_db
from app.models.scan_task import ScanTask
from app.tasks.scan_task import execute_scan_task

router = APIRouter()

class ScanRequest(BaseModel):
    directory_path: str

@router.post("/scan")
async def scan_directory(
    request: ScanRequest,
    db: Session = Depends(get_db)
):
    """
    创建扫描任务，立即返回任务 ID
    
    任务将在后台异步执行
    """
    # 验证路径
    if not os.path.exists(request.directory_path):
        raise HTTPException(status_code=400, detail=f"路径不存在: {request.directory_path}")
    
    # 创建任务记录
    task = ScanTask(directory_path=request.directory_path)
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 提交到任务队列
    execute_scan_task(task.id)
    
    return {
        "task_id": task.id,
        "message": "任务已创建，正在后台执行"
    }

# 删除旧的 /scan/status 和 /plan 端点 (已由 /tasks/{task_id} 替代)

@router.post("/execute")
async def execute_plan(
    plan: List[RenameItem],
    organizer: OrganizerService = Depends(get_organizer_service)
):
    """
    执行给定的重命名计划,将文件移动到目标媒体库。
    """
    
    # Get target library path from settings
    target_library = SettingsService.get_setting("app.target_library_path", "")
    
    if not target_library:
        raise HTTPException(
            status_code=400,
            detail="目标媒体库路径未配置,请在设置中配置 target_library_path"
        )
    
    if not os.path.exists(target_library):
        raise HTTPException(
            status_code=400,
            detail=f"目标媒体库路径不存在: {target_library}"
        )
    
    try:
        moved_count = 0
        failed_count = 0
        results = []
        
        for item in plan:
            # Extract anime info from new filename
            # Format: 动漫名 - S01E01.mkv
            filename = os.path.basename(item.new_path)
            match = re.match(r'(.+?)\s*-\s*S(\d+)E(\d+)', filename)
            
            if match:
                anime_title = match.group(1).strip()
                season = int(match.group(2))
                
                # Build target path with library structure
                target_path = FileOrganizer.build_target_path(
                    library_root=target_library,
                    anime_title=anime_title,
                    season=season,
                    filename=filename
                )
                
                # Move file
                success = FileOrganizer.move_file(item.original_path, target_path)
                if success:
                    moved_count += 1
                    results.append(RenameItem(original_path=item.original_path, new_path=target_path))
                else:
                    failed_count += 1
            else:
                # Fallback: just use the new filename in root
                target_path = os.path.join(target_library, filename)
                success = FileOrganizer.move_file(item.original_path, target_path)
                if success:
                    moved_count += 1
                    results.append(RenameItem(original_path=item.original_path, new_path=target_path))
                else:
                    failed_count += 1
        
        if failed_count > 0:
            raise HTTPException(
                status_code=500,
                detail=f"Moved {moved_count} files, {failed_count} failed"
            )
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback")
def rollback_last_execution(
    organizer: OrganizerService = Depends(get_organizer_service)
):
    """
    回滚上一次执行的操作。
    """
    try:
        organizer.rollback()
        return {"status": "success", "message": "Rollback successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/logs")
def get_scan_logs(
    organizer: OrganizerService = Depends(get_organizer_service)
):
    """
    获取扫描日志。
    """
    return organizer.get_logs()

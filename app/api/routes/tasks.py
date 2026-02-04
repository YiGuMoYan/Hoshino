"""任务管理 API 路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.scan_task import ScanTask
from app.services.core.organizer import OrganizerService, RenameItem
from typing import List

router = APIRouter()

@router.get("", summary="获取任务列表")
def list_tasks(
    skip: int = 0, 
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取所有任务，按创建时间倒序"""
    tasks = db.query(ScanTask)\
        .order_by(ScanTask.start_time.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [task.to_dict() for task in tasks]

@router.get("/{task_id}", summary="获取任务详情")
def get_task(task_id: str, db: Session = Depends(get_db)):
    """获取指定任务的详细信息，包括日志和计划"""
    task = db.query(ScanTask).filter(ScanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task.to_dict()

@router.delete("/{task_id}", summary="删除任务")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """删除指定任务"""
    task = db.query(ScanTask).filter(ScanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    db.delete(task)
    db.commit()
    return {"message": "任务已删除"}

@router.post("/{task_id}/execute", summary="执行任务计划")
def execute_task_plan(task_id: str, db: Session = Depends(get_db)):
    """执行指定任务的重命名计划"""
    task = db.query(ScanTask).filter(ScanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="只能执行已完成的任务")
    
    if task.executed:
        raise HTTPException(status_code=400, detail="任务已执行")
    
    # 执行计划
    organizer = OrganizerService()
    
    plan = [RenameItem(**item) for item in task.plan]
    organizer.execute_plan(plan)
    
    task.executed = 1
    db.commit()
    
    return {"message": "执行成功"}

@router.post("/{task_id}/rollback", summary="回滚任务")
def rollback_task(task_id: str, db: Session = Depends(get_db)):
    """回滚已执行的任务"""
    task = db.query(ScanTask).filter(ScanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if not task.executed:
        raise HTTPException(status_code=400, detail="任务未执行")
    
    # 回滚
    organizer = OrganizerService()
    organizer.rollback()
    
    task.executed = 0
    db.commit()
    
    return {"message": "回滚成功"}

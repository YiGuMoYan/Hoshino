from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Form
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.scan_task import ScanTask
from app.db.models import DownloadTask
from app.services.external.downloader import DownloaderService, extract_info_hash

router = APIRouter()
downloader = DownloaderService()

@router.get("/list", summary="获取下载任务列表")
def list_download_tasks(db: Session = Depends(get_db)):
    """
    获取所有下载任务及其状态
    合并数据库信息（元数据）与 qBittorrent 实时状态
    """
    # 1. 获取本地任务
    db_tasks = db.query(DownloadTask).order_by(DownloadTask.created_at.desc()).all()
    db_task_map = {t.info_hash.lower(): t for t in db_tasks}
    
    # 2. 获取 qBittorrent 任务
    try:
        qbit_tasks = downloader.get_hoshino_tasks()
    except Exception:
        qbit_tasks = []

    results = []
    
    # 处理 qBittorrent 任务
    # 处理 qBittorrent 任务
    for qt in qbit_tasks:
        h = qt.hash.lower()
        
        # Filter out subscription tasks (tags can be list or string)
        # qbittorrent-api v2 usually returns tags as a string "tag1, tag2"
        # We need to handle both just in case
        tags_str = qt.tags if isinstance(qt.tags, str) else (",".join(qt.tags) if qt.tags else "")
        
        if "Subscription" in tags_str:
            # Important: Remove from db_task_map so it doesn't get picked up by the fallback loop
            if h in db_task_map:
                del db_task_map[h]
            continue

        db_task = db_task_map.get(h)
        
        item = {
            "info_hash": h,
            "name": qt.name,
            "state": qt.state, # downloading, stalledUP, metaDL, 等
            "progress": qt.progress,
            "size": qt.size,
            "downloaded": qt.downloaded,
            "eta": qt.eta,
            "save_path": qt.save_path,
            "added_on": qt.added_on,
            # 数据库中的元数据
            "extra_vars": db_task.extra_vars if db_task else {},
            "archived": db_task.status == "completed" if db_task else False,
            "archive_error": db_task.error_message if db_task else None,
            "log": db_task.log if db_task else None
        }
        results.append(item)
        
        # 从 map 中移除，查看剩余的（失败/已移除的任务）
        if h in db_task_map:
            del db_task_map[h]

    # 处理剩余的数据库任务（可能已从 qBit 中移除或添加失败）
    for task in db_task_map.values():
         results.append({
            "info_hash": task.info_hash,
            "name": task.name or "Unknown",
            "state": "unknown", # Not found in qBit
            "progress": 0,
            "size": 0,
            "extra_vars": task.extra_vars,
            "archived": task.status == "completed",
            "archive_error": task.error_message,
            "log": task.log
         })

    return results

@router.post("/add/magnet", summary="Add magnet link or torrent")
def add_magnet_task(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    payload: {
        "url": "magnet:?...",
        "save_path": "...",
        "category": "hoshino",
        "tags": ["tag1"],
        "is_paused": false,
        "extra_vars": { "series_name": "...", "season": 1, "episode_offset": 0, "total_seasons": 1 }
    }
    """
    url = payload.get("url")
    save_path = payload.get("save_path")
    category = payload.get("category", "hoshino")
    tags = payload.get("tags", [])
    is_paused = payload.get("is_paused", False)
    extra_vars = payload.get("extra_vars", {})
    
    seeding_time = payload.get("seeding_time", -1)
    
    info_hash = extract_info_hash(url)
    if not info_hash:
        raise HTTPException(status_code=400, detail="Invalid magnet link (cannot find hash)")

    # 1. 添加到数据库
    task = db.query(DownloadTask).filter(DownloadTask.info_hash == info_hash).first()
    if not task:
        task = DownloadTask(
            info_hash=info_hash,
            name=extra_vars.get("series_name", "Pending..."),
            save_path=save_path, 
            extra_vars=extra_vars,
            status="paused" if is_paused else "downloading",
            seeding_time=seeding_time
        )
        db.add(task)
    else:
        # 更新现有任务
        task.extra_vars = extra_vars
        task.status = "paused" if is_paused else "downloading"
        task.seeding_time = seeding_time
    
    db.commit()
    
    # 2. 添加到 qBittorrent
    try:
        downloader.add_torrent(
            url, 
            save_path=save_path, 
            category=category, 
            tags=tags, 
            is_paused=is_paused,
            seeding_time=seeding_time
        )
        
        # 强制更新：确保 qBit 任务属性被设置，即使任务已存在
        downloader.update_task(
            info_hash,
            category=category,
            tags=tags,
            save_path=save_path,
            is_paused=is_paused,
            seeding_time=seeding_time
        )
    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to add to qBittorrent: {e}")

    return {"message": "Task added", "info_hash": info_hash}

@router.post("/add/torrent", summary="Add task via torrent file")
async def add_torrent_task(
    file: UploadFile = File(...),
    save_path: str = Form(None),
    category: str = Form("hoshino"),
    tags: str = Form(""),
    is_paused: bool = Form(False),
    seeding_time: int = Form(-1),
    extra_vars: str = Form("{}"),
    db: Session = Depends(get_db)
):
    try:
        file_bytes = await file.read()
        
        # 解析标签
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        
        # 解析 extra_vars
        try:
            extra_vars_dict = json.loads(extra_vars)
        except:
            extra_vars_dict = {}

        # 1. 先添加到 qBittorrent 以获取 Hash
        # 假设如果文件有效，添加不会失败
        # 假设如果文件有效，添加不会失败
        downloader.add_torrent(
            file_bytes,
            save_path=save_path,
            category=category,
            tags=tag_list,
            is_paused=is_paused,
            seeding_time=seeding_time
        )
        
        # 2. 等待并查找 hash
        await asyncio.sleep(1) # 等待 qbit 处理
        
        # 获取分类中的最新任务以识别新任务
        # 逻辑：可能在 'category' 或 'hoshino_preview' 中（如果已预览并合并）
        found_task = None
        
        # 2a. 检查目标分类
        tasks_target = downloader.get_hoshino_tasks(category=category)
        if tasks_target:
             found_task = sorted(tasks_target, key=lambda x: x.added_on, reverse=True)[0]
             
        # 2b. 检查预览分类（回退）
        if not found_task:
            tasks_preview = downloader.get_hoshino_tasks(category="hoshino_preview")
            if tasks_preview:
                found_task = sorted(tasks_preview, key=lambda x: x.added_on, reverse=True)[0]
        
        if not found_task:
             # 回退：列出所有最近的？有风险但是最后的手段
             raise HTTPException(status_code=500, detail="Failed to retrieve added torrent (Duplicate or not found)")
             
        info_hash = found_task.hash.lower()
        name = found_task.name
        
        # 强制更新：即使已添加，也要确保属性被设置（特别是如果已合并）
        downloader.update_task(
            info_hash,
            category=category,
            tags=tag_list,
            save_path=save_path,
            is_paused=is_paused,
            seeding_time=seeding_time
        )
        
        # 3. 添加/更新数据库
        task = db.query(DownloadTask).filter(DownloadTask.info_hash == info_hash).first()
        if not task:
            task = DownloadTask(
                info_hash=info_hash,
                name=extra_vars_dict.get("series_name", name), # 如有系列名称则优先使用，否则使用种子名称
                save_path=save_path or found_task.save_path, 
                extra_vars=extra_vars_dict,
                status="paused" if is_paused else "downloading",
                seeding_time=seeding_time
            )
            db.add(task)
        else:
            task.extra_vars = extra_vars_dict
            task.status = "paused" if is_paused else "downloading"
            task.seeding_time = seeding_time
            # 如果之前未手动设置则更新名称
            # 通常保留原始数据库名称，或在 extra_vars 提供新系列名称时更新
            if extra_vars_dict.get("series_name"):
                task.name = extra_vars_dict.get("series_name")
        
        db.commit()
        
        return {"info_hash": info_hash, "name": task.name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{info_hash}", summary="Delete download task")
def delete_download_task(
    info_hash: str,
    delete_files: bool = False,
    db: Session = Depends(get_db)
):
    # 1. Delete from DB
    task = db.query(DownloadTask).filter(DownloadTask.info_hash == info_hash).first()
    if task:
        db.delete(task)
        db.commit()
    
    # 2. Delete from qBittorrent
    try:
        downloader.delete_task(info_hash, delete_files=delete_files)
    except:
        pass # Ignore if not found in qBit
        
    return {"message": "Task deleted"}


@router.post("/preview", summary="Preview torrent files")
async def preview_torrent(
    magnet: Optional[str] = Body(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Preview files in a torrent (magnet or file).
    Adds task in paused state to 'hoshino_preview' category, waits for metadata, returns file list.
    """
    import asyncio
    
    info_hash = None
    source = None
    
    if magnet:
        info_hash = extract_info_hash(magnet)
        source = magnet
    elif file:
        # Read file content
        content = await file.read()
        source = content
        # For file, we might need to parse it to get hash, but downloader.add_torrent handles bytes.
        # We need hash to query files. qbittorrent-api doesn't easily give hash from bytes without adding.
        # So we add and then list torrents in 'hoshino_preview' category to find it? 
        # Or better: rely on the fact that we can list all recent additions?
        # A bit tricky. For now, let's assume we can add it.
        pass
    
    if not source:
         raise HTTPException(status_code=400, detail="No magnet link or file provided")

    try:
        # Add to qBit (Paused, special category)
        # Note: If it's a file, we don't have info_hash yet easily properly without a bencode parser.
        # Detailed approach: 
        # 1. Add torrent
        # 2. Wait 1s
        # 3. Get recent added torrents in 'hoshino_preview' category? 
        # For simplicity, let's just attempt adding.
        
        # If magnet, we have hash
        if info_hash:
             downloader.add_torrent(source, category="hoshino_preview", is_paused=False)
             
             # Poll for metadata (files)
             # Wait up to 5 minutes for metadata (600 * 0.5s)
             for _ in range(600): 
                 files = downloader.get_files(info_hash)
                 if files:
                     # Stop downloading content immediately
                     downloader.update_task(info_hash, is_paused=True)
                     
                     file_list = [{"name": f.name, "size": f.size} for f in files]
                     return {"info_hash": info_hash, "files": file_list}
                 await asyncio.sleep(0.5)
             
             raise HTTPException(status_code=408, detail="Timeout waiting for metadata (5 minutes)")
             
        else:
             # For file upload, we add it, then find what was added. 
             # Or we can verify if python can parse bencode to get hash first.
             # Installing 'bencode.py' or similar might be overkill.
             # Let's try adding and then fetching the latest added torrent in this category.
             downloader.add_torrent(source, category="hoshino_preview", is_paused=True)
             await asyncio.sleep(1) # Wait for qbit to process
             
             # Find the task
             tasks = downloader.get_hoshino_tasks(category="hoshino_preview")
             # Sort by added_on
             if not tasks:
                 raise HTTPException(status_code=500, detail="Failed to find added task")
             
             # Get latest
             latest = sorted(tasks, key=lambda x: x.added_on, reverse=True)[0]
             info_hash = latest.hash
             
             # Get files
             files = downloader.get_files(info_hash)
             file_list = [{"name": f.name, "size": f.size} for f in files]
             return {"info_hash": info_hash, "files": file_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection", summary="Test qBittorrent connection")
def test_connection(
    payload: dict = Body(...),
):
    host = payload.get("host")
    username = payload.get("username")
    password = payload.get("password")
    
    success, msg = downloader.test_connection(host, username, password)
    return {"success": success, "message": msg}

@router.post("/retry/{info_hash}", summary="Retry archiving for a failed task")
def retry_download_task(
    info_hash: str,
    db: Session = Depends(get_db)
):
    """
    Resets a failed or completed task's status to 'downloading' to trigger 
    the background organization process again.
    """
    task = db.query(DownloadTask).filter(DownloadTask.info_hash == info_hash).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Reset status to 'downloading' so the monitor picks it up
    task.status = "downloading"
    task.error_message = None # Clear previous error
    task.log = None # Clear previous logs
    db.commit()
    
    return {"message": "Retry scheduled", "info_hash": info_hash}

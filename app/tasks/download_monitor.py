from app.worker import huey
from app.services.external.downloader import DownloaderService
from app.services.core.organizer import OrganizerService
from app.db.session import get_db
from app.db.models import DownloadTask
from app.db.models import DownloadTask
from datetime import datetime
import asyncio
from huey import crontab
from app.services.notification.notifier import Notifier

# Disabled: Auto-scan after download is not needed
# @huey.periodic_task(crontab(minute='*')) # Run every minute, actually per internal clock, 
# but huey crontab is minute based. For 30s we might need custom loop or just minute is fine.
# Let's use loop inside or just minute. Minute is safe. 
# Or use huey's internal loop capability if available? 
# Standard crontab min resolution is 1 minute.
# We can use @huey.periodic_task(crontab(minute='*/1'))
def check_downloads():
    pass  # Disabled
    # check_downloads_task()

def check_downloads_task():
    """
    Check for completed downloads and trigger archiving.
    This runs synchronously in the worker.
    """
    db = next(get_db())
    downloader = DownloaderService()
    organizer = OrganizerService()

    try:
        # Get pending tasks from DB
        pending_tasks = db.query(DownloadTask).filter(
            DownloadTask.status.in_(["downloading", "organizing"])
        ).all()

        if not pending_tasks:
            return

        # Get all hoshino tasks from qBit to minimize API calls
        qbit_tasks = downloader.get_hoshino_tasks()
        qbit_map = {t.hash.lower(): t for t in qbit_tasks}

        for task in pending_tasks:
            q_task = qbit_map.get(task.info_hash.lower())
            
            if not q_task:
                # Task missing in qBit?
                if (datetime.utcnow() - task.created_at).total_seconds() > 3600:
                    # If missing for > 1 hour, mark failed
                    task.status = "failed"
                    task.error_message = "Task not found in qBittorrent"
                    db.commit()
                continue
            
            # Check status
            # qBit states: downloading, stalledUP, upload, pausedUP, queuedUP, metaDL, etc.
            # Completed usually means progress=1 or state like upload/stalledUP
            is_completed = q_task.progress == 1.0 or q_task.state in ["uploading", "stalledUP", "pausedUP", "queuedUP"]
            
            if is_completed and task.status == "downloading":
                # Start organizing
                print(f"[Monitor] Task completed: {task.name}. Starting organization...")
                task.status = "organizing"
                db.commit()
                
                try:
                    # Execute scan with context
                    # OrganizerService.scan_directory is async, but we are in sync worker
                    # Use asyncio.run
                    context = task.extra_vars or {}
                    
                    # We need to construct absolute save path
                    # qBit save_path might be absolute or relative
                    # If we use Docker, paths might map differently. 
                    # Assuming local execution or mapped volumes match for now.
                    # Or `save_path` from qBit is container path.
                    
                    target_path = q_task.content_path # This is usually the full path to single file or folder
                    
                    # Log to Huey/Stout
                    print(f"[Monitor] Scanning: {target_path} Context: {context}")

                    # Run async function
                    async def run_scan():
                        # We need to instantiate a new OrganizerService potentially or use existing
                        # organizer.scan_directory returns a Plan (RenameItems)
                        # We should also execute it instantly?
                        # The requirement said "Auto Archive".
                        # organizer.scan_directory just generates plan. 
                        # We need organizer.execute_plan(plan)
                        
                        plan = await organizer.scan_directory(target_path, context=context)
                        if plan:
                            organizer.execute_plan(plan)
                            return True
                        return False

                    completed = asyncio.run(run_scan())
                    
                    if completed:
                        task.status = "completed"
                        try:
                            Notifier().notify_archive_complete(task.name, logs=formatted_log if 'formatted_log' in locals() else "")
                        except Exception:
                            pass
                    else:
                        # No files moved?
                        task.status = "completed" # Still mark completed as download is done
                        task.error_message = "No files matched for archiving"
                        try:
                            Notifier().notify_manual_rename_needed(task.name, reason="未找到匹配文件，无法自动归档")
                        except Exception:
                            pass
                    
                    # Save logs
                    logs = organizer.get_logs()
                    formatted_log = "\n".join([f"[{l['timestamp']}] [{l['level'].upper()}] {l['message']}" for l in logs])
                    task.log = formatted_log

                except Exception as e:
                    task.status = "failed"
                    task.error_message = f"Archiving failed: {str(e)}"
                    print(f"[Monitor] Error: {e}")
                    
                    try:
                        Notifier().notify_manual_rename_needed(task.name, reason=f"归档出错: {str(e)}")
                    except Exception:
                        pass
                    
                    # Save logs on error too
                    logs = organizer.get_logs()
                    formatted_log = "\n".join([f"[{l['timestamp']}] [{l['level'].upper()}] {l['message']}" for l in logs])
                    task.log = formatted_log
                
                db.commit()

    except Exception as e:
        print(f"[Monitor] Loop error: {e}")
    finally:
        db.close()



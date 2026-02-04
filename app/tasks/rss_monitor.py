
from huey import crontab
from app.worker import huey
from app.db.session import SessionLocal
from app.db.models import Subscription, RSSItem, DownloadTask
from app.services.external.mikan import MikanService
from app.services.external.downloader import DownloaderService, extract_info_hash
from app.services.system.settings_service import SettingsService
from app.services.core.renamer import RenamerService
from datetime import datetime
from loguru import logger
import re
import time
from app.services.notification.notifier import Notifier

@huey.periodic_task(crontab(minute='*/30'), name='check_rss_updates')
def check_rss_updates():
    """定时检查 RSS 更新（默认每 30 分钟）"""
    settings = SettingsService()
    interval = int(settings.get_setting("mikan.check_interval", 30))
    
    logger.info("Starting periodic RSS check...")
    
    db = SessionLocal()
    try:
        # Get active subscriptions with auto_download enabled
        subscriptions = db.query(Subscription).filter(
            Subscription.status == "active",
            Subscription.auto_download == True
        ).all()
        
        for sub in subscriptions:
            try:
                check_subscription_sync(sub, db)
            except Exception as e:
                logger.error(f"Error checking subscription {sub.title}: {e}")
            
    finally:
        db.close()

@huey.task(name='check_subscription_immediate')
def check_subscription_immediate(sub_id: int):
    """立即检查单个订阅更新"""
    logger.info(f"Immediate check triggered for subscription {sub_id}")
    db = SessionLocal()
    try:
        sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
        if sub:
            check_subscription_sync(sub, db)
        else:
            logger.warning(f"Subscription {sub_id} not found during immediate check")
    except Exception as e:
        logger.error(f"Error in immediate check for {sub_id}: {e}")
    finally:
        db.close()

def check_subscription_sync(sub: Subscription, db):
    """同步执行单个订阅检查逻辑"""
    mikan = MikanService()
    downloader = DownloaderService()
    renamer = RenamerService()
    
    logger.info(f"Checking updates for subscription: {sub.title}")
    
    # Parse RSS
    items = mikan.parse_rss(sub.rss_url)
    
    new_count = 0
    for item in items:
        # Check if exists by GUID
        existing = db.query(RSSItem).filter(
            RSSItem.guid == item['guid']
        ).first()
        
        rss_item = None
        
        if existing:
            if existing.downloaded:
                # Already processed successfully
                continue
            
            # Exists but failed previously - Retry
            logger.info(f"Retrying previous failed item: {item['title']}")
            rss_item = existing
        else:
            # Apply filters for NEW items
            if not _match_filters(item['title'], sub):
                logger.info(f"Skipping due to filter: {item['title']} (Regex: {sub.filter_regex}, Kws: {sub.filter_keywords})")
                continue
            
            # New Item!
            logger.info(f"Found new episode: {item['title']}")
            
            # Create RSS Item
            rss_item = RSSItem(
                subscription_id=sub.id,
                guid=item['guid'],
                title=item['title'],
                magnet_link=item['magnet'],
                torrent_url=item['torrent_url'],
                pub_date=datetime(*item['pub_date'][:6]) if item['pub_date'] else datetime.utcnow()
            )
            db.add(rss_item)
        
        # Try to get valid source
        source = item['magnet'] or item['torrent_url'] or item['link']

        # Add to Download
        info_hash = None
        
        try:
            logger.info(f"Adding torrent: {item['title'][:50]}...")
            logger.debug(f"Source type - Magnet: {bool(item['magnet'])}, Torrent URL: {bool(item['torrent_url'])}")
            
            # Get current task hashes BEFORE adding
            tasks_before = set()
            if not item['magnet']:  # Only needed for non-magnet links
                try:
                    current_tasks = downloader.get_hoshino_tasks()
                    tasks_before = {t.hash.lower() for t in current_tasks}
                    logger.debug(f"Tasks before adding: {len(tasks_before)}")
                except Exception as e:
                    logger.warning(f"Could not get tasks before adding: {e}")
            
            # Add torrent without renaming - keep original title for reliable hash extraction
            downloader.add_torrent(
                source,
                save_path=sub.save_path,
                category=sub.category,
                tags=["Subscription", sub.title],
                is_paused=False
            )
            
            # Extract hash from magnet link
            if item['magnet']:
                match = re.search(r'xt=urn:btih[:=]([a-fA-F0-9]{40})', item['magnet'])
                if match:
                    info_hash = match.group(1).lower()
                    logger.info(f"Extracted hash from magnet: {info_hash}")
                else:
                    logger.warning(f"Failed to extract hash from magnet link")
            
            # If no hash from magnet, find the newly added task by comparing lists
            if not info_hash and tasks_before is not None:
                logger.info("No hash from magnet, finding newly added torrent...")
                
                # Try multiple times with increasing delays
                for attempt in range(3):
                    wait_time = 2 + attempt  # 2s, 3s, 4s
                    logger.debug(f"Attempt {attempt + 1}/3: waiting {wait_time}s...")
                    time.sleep(wait_time)
                    
                    try:
                        tasks_after = downloader.get_hoshino_tasks()
                        tasks_after_hashes = {t.hash.lower(): t for t in tasks_after}
                        
                        # Find new hashes
                        new_hashes = set(tasks_after_hashes.keys()) - tasks_before
                        logger.debug(f"Tasks after: {len(tasks_after_hashes)}, New hashes: {len(new_hashes)}")
                        
                        if new_hashes:
                            # Get the new task
                            new_hash = list(new_hashes)[0]
                            new_task = tasks_after_hashes[new_hash]
                            logger.info(f"✅ Found newly added task: '{new_task.name[:60]}' (hash: {new_hash})")
                            info_hash = new_hash
                            break
                        else:
                            logger.debug(f"No new tasks found yet, retrying...")
                    except Exception as e:
                        logger.error(f"Error querying tasks: {e}")
                
                if not info_hash:
                    logger.warning(f"Could not find newly added task after 3 attempts")
            
            if info_hash:
                logger.info(f"Saving hash {info_hash} to database...")
                task = DownloadTask(
                    info_hash=info_hash,
                    name=sub.extra_vars.get('series_name', sub.title),
                    save_path=sub.save_path,
                    extra_vars=sub.extra_vars,
                    status="downloading"
                )
                if not db.query(DownloadTask).filter(DownloadTask.info_hash == info_hash).first():
                    db.add(task)
                    
                rss_item.downloaded = True
                rss_item.download_task_id = info_hash
                logger.info(f"✅ Linked RSS item to hash: {info_hash}")
                
                # Enforce Seeding Time Limits
                # Even if add_torrent tried, it might have failed if hash wasn't known then.
                # Now we definitely have the hash.
                try:
                    settings = SettingsService()
                    global_seeding_time = int(settings.get_setting("downloader.seeding_time", -1))
                    if global_seeding_time != -1:
                         logger.info(f"Enforcing seeding time limit: {global_seeding_time} min for {info_hash}")
                         downloader.update_task(info_hash, seeding_time=global_seeding_time, is_paused=False)
                    else:
                         # Ensure it's resumed even if no limit needed (just in case)
                         downloader.update_task(info_hash, is_paused=False)
                except Exception as e:
                    logger.warning(f"Failed to set seeding time for {info_hash}: {e}")
            else:
                logger.warning(f"⚠️  Could not extract hash for {item['title']}, marking as downloaded without hash")
                rss_item.downloaded = True
                
                # Send Notification
                try:
                    notifier = Notifier()
                    notifier.notify_subscription_update(sub.title, item['title'])
                except Exception as ne:
                    logger.error(f"Failed to send notification: {ne}")
                
            new_count += 1
            
        except Exception as e:
            logger.error(f"Failed to add torrent for {item['title']}: {e}", exc_info=True)

    # Update check time
    sub.last_check_at = datetime.utcnow()
    db.commit()

def _match_filters(title: str, subscription: Subscription) -> bool:
    """检查标题是否匹配过滤规则"""
    # Regex Filter (First priority)
    if subscription.filter_regex:
        try:
            if not re.search(subscription.filter_regex, title, re.IGNORECASE):
                return False
        except Exception as e:
            logger.error(f"Invalid regex for sub {subscription.id}: {e}")
            return False

    # Includes
    if subscription.filter_keywords:
         for kw in subscription.filter_keywords:
             if kw and kw.lower() not in title.lower():
                 return False
    
    # Excludes
    if subscription.exclude_keywords:
        for kw in subscription.exclude_keywords:
            if kw and kw.lower() in title.lower():
                return False
    
    return True

@huey.periodic_task(crontab(minute='*'), name='auto_rename_files')
def auto_rename_files():
    """定时检查并重命名下载文件"""
    renamer = RenamerService()
    downloader = DownloaderService()
    
    try:
        tasks = downloader.get_hoshino_tasks()
        if not tasks:
            return

        for task in tasks:
            if task.state in ['metaDL', 'allocating', 'queuedDL', 'checkingResumeData']:
                 continue
            
            # Use RenamerService logic
            renamer.rename_torrent_files(task.hash)
                    
    except Exception as e:
        logger.error(f"Auto-rename task failed: {e}")


import re
from loguru import logger
from app.db.session import SessionLocal
from app.db.models import RSSItem, Subscription
from app.services.external.downloader import DownloaderService

class RenamerService:
    def __init__(self):
        self.downloader = DownloaderService()

    def rename_torrent_files(self, info_hash: str) -> bool:
        """
        Check and rename files for a specific torrent hash.
        Returns True if renamed something, False otherwise.
        """
        db = SessionLocal()
        try:
            # 1. Find RSSItem
            rss_item = db.query(RSSItem).filter(RSSItem.download_task_id == info_hash.lower()).first()
            if not rss_item:
                logger.debug(f"Renamer: RSS Item not found for hash {info_hash}")
                return False
            
            # Skip if already renamed
            if rss_item.renamed:
                logger.debug(f"Renamer: File already renamed for {rss_item.title}, skipping")
                return False
                
            sub = rss_item.subscription
            if not sub:
                return False

            # 2. Get Files
            files = self.downloader.get_files(info_hash)
            if not files:
                logger.warning(f"Renamer: No files found for task {info_hash}")
                return False
            
            # 3. Find Main Video File
            # Use dict access for qbittorrent-api reliability
            video_files = [f for f in files if f['name'].lower().endswith(('.mp4', '.mkv', '.avi'))]
            if not video_files:
                return False
                
            main_file = max(video_files, key=lambda f: f['size'])
            
            # 4. Construct Target Name
            ep_num = self._extract_episode(rss_item.title)
            if not ep_num:
                logger.debug(f"Renamer: Could not extract episode from {rss_item.title}")
                return False
                
            season_num = sub.extra_vars.get('season', 1)
            series_name = sub.extra_vars.get('series_name', sub.title)
            series_name = re.sub(r'[\\/:*?"<>|]', '_', series_name).strip()
            
            ext = main_file['name'].split('.')[-1]
            new_name = f"{series_name} - S{int(season_num):02d}E{ep_num}.{ext}"
            
            # 5. Rename if needed
            # main_file['name'] is relative path inside torrent, e.g. "Folder/File.mkv"
            path_parts = main_file['name'].split('/')
            current_basename = path_parts[-1]
            
            if current_basename != new_name:
                logger.info(f"Renamer: Renaming '{current_basename}' -> '{new_name}' for {sub.title}")
                self.downloader.rename_file(info_hash, main_file['name'], new_name)
                
                # Mark as renamed
                rss_item.renamed = True
                db.commit()
                logger.info(f"✅ Marked {rss_item.title} as renamed")
                return True
            else:
                logger.debug(f"Renamer: File already named correctly: {current_basename}")
                # Mark as renamed even if name is already correct
                rss_item.renamed = True
                db.commit()
                return False
                
        except Exception as e:
            logger.error(f"Renamer Error: {e}")
            return False
        finally:
            db.close()
            
    def _extract_episode(self, title: str) -> str:
        """Extract episode number from title"""
        patterns = [
            r'\[(\d{2,3})(?:v\d)?\]',       # [05], [05v2]
            r'[\s\[\-](\d{2,3})(?:v\d)?[\s\]]', #  05 , - 05
            r'第(\d{1,3})[话話集]',           # 第05话
            r'(?:Ep|EP|ep)\.?\s*(\d{1,3})', # Ep05
            r' - (\d{1,3})(?: |$)',         # - 05
        ]
        
        for pat in patterns:
            match = re.search(pat, title)
            if match:
                 return match.group(1)
        return None

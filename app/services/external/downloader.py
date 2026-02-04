from qbittorrentapi import Client
from app.services.system.settings_service import SettingsService
from loguru import logger
import time

import re

def extract_info_hash(source: str) -> str:
    """Extract info hash from magnet link or hash string (Hex or Base32)"""
    import base64
    import binascii

    source = str(source).strip()
    
    # Extract hash string from magnet or use raw string
    hash_str = None
    if source.startswith("magnet:?"):
        # Try finding hex hash first
        match = re.search(r'xt=urn:btih[:=]([a-fA-F0-9]{40})', source)
        if match:
            return match.group(1).lower()
            
        # Try finding base32 hash
        match = re.search(r'xt=urn:btih[:=]([a-zA-Z2-7]{32})', source)
        if match:
            hash_str = match.group(1)
    elif len(source) == 40:
        return source.lower()
    elif len(source) == 32:
        hash_str = source

    # Convert Base32 to Hex if found
    if hash_str and len(hash_str) == 32:
        try:
            return base64.b32decode(hash_str.upper() + "=" * ((8 - len(hash_str) % 8) % 8)).hex().lower()
        except:
            return None
            
    return None

class DownloaderService:
    def __init__(self):
        self.settings = SettingsService()
        self.client = None
        # 延迟连接：不在 __init__ 中连接
    
    def _connect(self):
        """使用设置初始化到 qBittorrent 的连接"""
        # 如果已连接则返回
        if self.client:
            try:
                # 可选：快速检查是否活跃？
                # self.client.app.version 
                # 但那是一个 API 调用。让我们相信它直到失败
                return
            except:
                self.client = None

        host = self.settings.get_setting("downloader.host", "http://qbittorrent:8080")
        username = self.settings.get_setting("downloader.username", "admin")
        password = self.settings.get_setting("downloader.password", "adminadmin")

        try:
            # 短超时以避免挂起
            self.client = Client(host=host, username=username, password=password, REQUESTS_ARGS={'timeout': 5})
            self.client.auth_log_in()
            logger.info(f"Connected to qBittorrent at {host}")
        except Exception as e:
            # 用户请求删除检查/减少日志
            # 仅在真正需要调试时才有用的信息，避免刷屏
            # Implement a simple throttling mechanism using a static variable or similar if possible, 
            # but for now, just log debug or simplified warning.
            # logger.warning(f"Failed to connect to qBittorrent: {e}")
            pass # Silencing as requested
            self.client = None

    def test_connection(self, host, username, password):
        """Test connection with provided credentials"""
        try:
            temp_client = Client(host=host, username=username, password=password, REQUESTS_ARGS={'timeout': 5})
            temp_client.auth_log_in()
            version = temp_client.app.version
            return True, f"Connected to qBittorrent v{version}"
        except Exception as e:
            return False, str(e)

    def add_torrent(self, torrent_source, save_path=None, category="hoshino", tags=None, is_paused=False, rename=None, seeding_time: int = -1):
        """
        添加种子到 qBittorrent
        torrent_source: 可以是磁力链接、.torrent 文件路径或 infohash
        seeding_time: -1 (default), 0 (no seed), >0 (minutes)
        """
        import re

        if not self.client:
            self._connect()
            if not self.client:
                raise Exception("Downloader not connected")

        try:
            # Resolve global seeding time if default
            effective_seeding_time = seeding_time
            if effective_seeding_time == -1:
                global_setting = self.settings.get_setting("downloader.seeding_time", -1)
                effective_seeding_time = int(global_setting)
            
            # Try to infer hash for immediate setting
            source = str(torrent_source)
            current_hash = extract_info_hash(source)
            
            # Determine if we need to set limits (best effort)
            need_limit = (effective_seeding_time != -1)
            
            # Prepare arguments
            kwargs = {
                "save_path": save_path,
                "category": category,
                "tags": tags,
                "is_paused": is_paused, # User control only
                "rename": rename
            }
            
            # Check if source is link
            if source.startswith("magnet:?") or len(source) == 40 or len(source) == 32:
                 # Clean magnet link if it is one
                 if source.startswith("magnet:?"):
                     match = re.search(r'xt=urn:btih[:=]([a-fA-F0-9]{40})', source)
                     if match:
                         # Reconstruct clean magnet with hex
                         kwargs['urls'] = f"magnet:?xt=urn:btih:{match.group(1).lower()}"
                     else:
                         # Use original (might be base32, qbit handles it)
                         kwargs['urls'] = source
                 else:
                     # It's a hash, make it a magnet link
                     kwargs['urls'] = f"magnet:?xt=urn:btih:{source}"
                 
                 resp = self.client.torrents_add(**kwargs)
            elif source.startswith("http://") or source.startswith("https://"):
                 # URL to torrent file
                 kwargs['urls'] = source
                 resp = self.client.torrents_add(**kwargs)
            else:
                 # Assumed to be file path or bytes
                 resp = self.client.torrents_add(torrent_files=torrent_source, **kwargs)

            # Helper to set limits if we have hash (Best Effort)
            if current_hash:
                logger.info(f"debug: add_torrent processing hash {current_hash}. is_paused={is_paused}, need_limit={need_limit}")
                # Set limits if needed
                if need_limit:
                    try:
                        limit = effective_seeding_time if effective_seeding_time >= 0 else -1
                        logger.info(f"debug: Setting share limits for {current_hash}: time={limit}")
                        self.client.torrents_set_share_limits(seeding_time_limit=limit, torrent_hashes=current_hash, ratio_limit=-1, inactive_seeding_time_limit=-1)
                    except Exception as e:
                        logger.warning(f"Best-effort limit setting failed for {current_hash}: {e}")
                
                # Explicitly resume if not paused (ensure it starts)
                if not is_paused:
                    try:
                        # Small delay to allow qBit to register the task state
                        time.sleep(0.5)
                        logger.info(f"debug: Explicitly resuming task {current_hash}")
                        self.client.torrents_resume(torrent_hashes=current_hash)
                    except Exception as e:
                        logger.warning(f"Explicit resume failed for {current_hash}: {e}")
            else:
                logger.info(f"debug: No current_hash found for source, skipping immediate resume/limit.")

            if resp == "Ok." or resp == "Fails.": 
                 return True
            return True 
        except Exception as e:
            logger.error(f"Error adding torrent: {e}")
            raise e

    def get_files(self, info_hash):
        """Get file list for a torrent"""
        if not self.client:
            self._connect()
            if not self.client:
                return []
        
        try:
            return self.client.torrents_files(torrent_hash=info_hash)
        except Exception as e:
            logger.error(f"Error getting files: {e}")
            return []

    def get_task_status(self, info_hash):
        """Get status of a specific torrent"""
        if not self.client:
            self._connect()
            if not self.client:
                return None
        
        try:
            torrents = self.client.torrents_info(torrent_hashes=info_hash)
            if torrents:
                return torrents[0]
            return None
        except Exception as e:
            logger.error(f"Error getting torrent info: {e}")
            return None

    def get_hoshino_tasks(self, category="hoshino"):
        """Get all tasks with hoshino category"""
        if not self.client:
            self._connect()
            if not self.client:
                # Return empty list if cannot connect, supressing error at this level
                return []
        
        try:
            return self.client.torrents_info(category=category)
        except Exception as e:
            self.client = None
            return []

    def update_task(self, info_hash, category=None, tags=None, save_path=None, is_paused=None, seeding_time: int = -1):
        """Update properties of an existing task"""
        if not self.client:
            self._connect()
            if not self.client:
                 raise Exception("Downloader not connected")
            
        try:
             # Basic properties
             if category is not None:
                 self.client.torrents_set_category(category=category, torrent_hashes=info_hash)
             
             if tags is not None:
                 self.client.torrents_add_tags(tags=tags, torrent_hashes=info_hash)
             
             if is_paused is not None:
                 if is_paused:
                     self.client.torrents_pause(torrent_hashes=info_hash)
                 else:
                     self.client.torrents_resume(torrent_hashes=info_hash)

             # Save path (Location) - moves files if exist
             if save_path:
                 self.client.torrents_set_location(location=save_path, torrent_hashes=info_hash)
            
             # Seeding Time
             if seeding_time != -1:
                 # Set seeding time limit (minutes)
                 limit = seeding_time if seeding_time >= 0 else -1
                 self.client.torrents_set_share_limits(seeding_time_limit=limit, torrent_hashes=info_hash, ratio_limit=-1, inactive_seeding_time_limit=-1)
                 
             return True
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            raise e

    def rename_file(self, info_hash, old_path, new_name):
        """Rename a file inside a torrent"""
        if not self.client:
            self._connect()
            if not self.client:
                 raise Exception("Downloader not connected")

        try:
            self.client.torrents_rename_file(torrent_hash=info_hash, old_path=old_path, new_path=new_name)
            return True
        except Exception as e:
            logger.error(f"Error renaming file: {e}")
            raise e

    def delete_task(self, info_hash, delete_files=False):
        """Delete task(s) from qBittorrent
        
        Args:
            info_hash: Single hash string or list of hashes
            delete_files: Whether to delete downloaded files
        """
        logger.info(f"delete_task called: info_hash={info_hash}, delete_files={delete_files}")
        logger.info(f"info_hash type: {type(info_hash)}, is list: {isinstance(info_hash, list)}")
        
        if not self.client:
            logger.info("Client not connected, connecting...")
            self._connect()
            if not self.client:
                 raise Exception("Downloader not connected")

        try:
            # qBittorrent API accepts both single hash and list of hashes
            logger.info(f"Calling qBittorrent API: torrents_delete(delete_files={delete_files}, torrent_hashes={info_hash})")
            result = self.client.torrents_delete(delete_files=delete_files, torrent_hashes=info_hash)
            logger.info(f"qBittorrent API call completed. Result: {result}")
        except Exception as e:
            logger.error(f"❌ Error deleting task: {e}", exc_info=True)
            raise e

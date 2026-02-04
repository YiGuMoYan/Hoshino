import os
import re
from typing import List, Optional, Dict
from loguru import logger
from app.services.system.settings_service import SettingsService
from app.services.external.tmdb_service import TMDBService

class AnimeItem:
    def __init__(self, title: str, path: str, poster_url: Optional[str] = None, season_count: int = 0,
                 year: str = None, status: str = None, air_day: int = None, tmdb_id: int = None,
                 vote_average: float = 0.0, overview: str = None):
        self.title = title
        self.path = path
        self.poster_url = poster_url
        self.season_count = season_count
        self.year = year
        self.status = status
        self.air_day = air_day
        self.tmdb_id = tmdb_id
        self.vote_average = vote_average
        self.overview = overview

    def to_dict(self):
        return {
            "title": self.title,
            "path": self.path,
            "poster_url": self.poster_url,
            "season_count": self.season_count,
            "year": self.year,
            "status": self.status
            # Add others if needed for debugging, but mostly used by LibraryItem
        }

class LibraryService:
    def __init__(self):
        self.settings = SettingsService()
        self.tmdb = TMDBService()

    async def scan_and_refresh(self) -> Dict[str, int]:
        """
        Scan and refresh the library database.
        Returns stats: {"added": x, "updated": y, "removed": z}
        """
        target_path = self.settings.get_setting("app.target_library_path")
        if not target_path or not os.path.exists(target_path):
            logger.warning(f"Library path not configured or exists: {target_path}")
            return {"added": 0, "updated": 0, "removed": 0}

        from app.db.session import SessionLocal
        from app.db.models import LibraryItem, Subscription
        from datetime import datetime

        stats = {"added": 0, "updated": 0, "removed": 0}
        
        # Load subscriptions for matching
        with SessionLocal() as db:
            subs = db.query(Subscription).all()
            # Normalize titles helper
            def normalize(s): return re.sub(r'\s+', '', s.lower()) if s else ""
            sub_map = {normalize(s.title): True for s in subs}
        
        # Track current paths to identify deletions at the end
        current_paths = set()

        try:
            # Find all candidate anime folders
            candidate_paths = []
            
            def scan_dir(path, depth=0):
                if depth > 1: # Max depth 1 means Root -> Category -> Anime
                    return
                
                try:
                    with os.scandir(path) as it:
                        for entry in it:
                            if entry.is_dir():
                                # Check if this folder looks like an anime (has video or seasons)
                                # Or if it is a category (assume if it doesn't match above, we scan inside)
                                
                                is_anime = False
                                has_seasons = False
                                has_video = False
                                
                                # Quick check content
                                try:
                                    with os.scandir(entry.path) as sub_it:
                                        for sub in sub_it:
                                            if sub.is_dir() and ("season" in sub.name.lower() or "specials" in sub.name.lower()):
                                                has_seasons = True
                                                break
                                            if sub.is_file() and sub.name.lower().endswith(('.mp4', '.mkv', '.avi', '.m4v')):
                                                has_video = True
                                except Exception:
                                    pass
                                
                                if has_seasons or has_video:
                                    candidate_paths.append((entry.path, entry.name))
                                else:
                                    # Treat as category/container, recurse
                                    scan_dir(entry.path, depth + 1)
                except Exception as e:
                    logger.warning(f"Error scanning dir {path}: {e}")

            scan_dir(target_path)

            for path, name in candidate_paths:
                item_data = await self._process_anime_folder(path, name)
                if item_data:
                    current_paths.add(item_data.path)
                    
                    # Check subscription status
                    # Logic: exact match or stripped match of title
                    is_sub = False
                    if normalize(item_data.title) in sub_map:
                        is_sub = True
                    
                    with SessionLocal() as db:
                        existing = db.query(LibraryItem).filter(LibraryItem.path == item_data.path).first()
                        if existing:
                            # Update if changed
                            # Always update metadata significantly
                            existing.season_count = item_data.season_count
                            existing.poster_path = item_data.poster_url
                            existing.updated_at = datetime.utcnow()
                            existing.year = item_data.year
                            existing.status = item_data.status
                            existing.air_day = item_data.air_day
                            existing.tmdb_id = item_data.tmdb_id
                            existing.vote_average = item_data.vote_average
                            existing.overview = item_data.overview
                            existing.is_subscribed = is_sub
                            
                            db.commit()
                            stats["updated"] += 1
                            
                            # Proactively trigger metadata fetch
                            try:
                                from app.tasks.library_tasks import task_fetch_bangumi_metadata
                                task_fetch_bangumi_metadata(existing.id)
                            except Exception: pass
                        else:
                            # Insert new
                            new_item = LibraryItem(
                                title=item_data.title,
                                path=item_data.path,
                                poster_path=item_data.poster_url,
                                season_count=item_data.season_count,
                                year=item_data.year,
                                status=item_data.status,
                                air_day=item_data.air_day,
                                tmdb_id=item_data.tmdb_id,
                                vote_average=item_data.vote_average,
                                overview=item_data.overview,
                                is_subscribed=is_sub
                            )
                            db.add(new_item)
                            db.commit()
                            db.refresh(new_item)
                            stats["added"] += 1
                            
                            # Proactively trigger metadata fetch for new items
                            try:
                                from app.tasks.library_tasks import task_fetch_bangumi_metadata
                                task_fetch_bangumi_metadata(new_item.id)
                            except Exception: pass
            
            # Remove stale items
            with SessionLocal() as db:
                all_items = db.query(LibraryItem).all()
                for item in all_items:
                    if item.path not in current_paths:
                        db.delete(item)
                        stats["removed"] += 1
                db.commit()
                
        except Exception as e:
            logger.error(f"Error scanning library: {e}")
            import traceback
            traceback.print_exc()
            
        logger.info(f"Library scan completed: {stats}")
        return stats

    def get_all_items(self) -> List[Dict]:
        """Get all library items from DB"""
        from app.db.session import SessionLocal
        from app.db.models import LibraryItem
        
        with SessionLocal() as db:
            items = db.query(LibraryItem).order_by(LibraryItem.title).all()
            return [item.to_dict() for item in items]

    def get_item(self, item_id: int) -> Optional[Dict]:
        """Get a single library item"""
        from app.db.session import SessionLocal
        from app.db.models import LibraryItem
        
        with SessionLocal() as db:
            item = db.query(LibraryItem).filter(LibraryItem.id == item_id).first()
            return item.to_dict() if item else None

    async def get_episodes(self, item_id: int) -> List[Dict]:
        """Get all video files for an item and enrich with TMDB metadata"""
        item = self.get_item(item_id)
        if not item:
            return []
            
        path = item["path"]
        if not os.path.exists(path):
            return []
            
        videos = []
        import base64
        import re
        
        # Regex for SxxExx or Exx
        se_pattern = re.compile(r'[sS](\d+)[eE](\d+)')
        ep_pattern = re.compile(r'[eE](\d+)')
        num_pattern = re.compile(r'[^0-9](\d{1,3})[^0-9]') # Fallback for simple numbers
        
        found_seasons = set()
        
        # 1. Scan files
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(('.mp4', '.mkv', '.avi', '.m4v', '.webm')):
                    full_path = os.path.join(root, f)
                    encoded_path = base64.urlsafe_b64encode(full_path.encode()).decode()
                    
                    # Try to parse season and episode
                    s_num, e_num = None, None
                    se_match = se_pattern.search(f)
                    if se_match:
                        s_num, e_num = int(se_match.group(1)), int(se_match.group(2))
                    else:
                        ep_match = ep_pattern.search(f)
                        if ep_match:
                             s_num, e_num = 1, int(ep_match.group(1))
                             # Try to check if folder name has season
                             folder_match = re.search(r'Season\s*(\d+)', root, re.I)
                             if folder_match:
                                 s_num = int(folder_match.group(1))
                    
                    if s_num is not None:
                        found_seasons.add(s_num)

                    videos.append({
                        "name": f,
                        "path": full_path,
                        "stream_url": f"/api/library/stream/{encoded_path}",
                        "size": os.path.getsize(full_path),
                        "season": s_num,
                        "episode": e_num
                    })
        
        # 2. Fetch Bangumi Metadata from Cache ONLY
        series_title = item.get("title", "Unknown")
        
        from app.db.session import SessionLocal
        from app.db.models import BangumiEpisode, BangumiSubjectMapping
        
        bangumi_metadata = {}
        missing_metadata = False
        
        with SessionLocal() as db:
            # 2.1 Get all subject-to-season mappings for this item
            mappings = db.query(BangumiSubjectMapping).filter(BangumiSubjectMapping.item_id == item_id).all()
            season_to_subject = {m.season: m.subject_id for m in mappings}
            
            # 2.2 If S1 mapping is missing but LibraryItem has bangumi_id, use it
            if 1 not in season_to_subject and item.get("bangumi_id"):
                season_to_subject[1] = item["bangumi_id"]
            
            # 2.3 Try to fetch cache for each found season
            for s in found_seasons:
                if s == 0: continue
                
                target_subject_id = season_to_subject.get(s)
                
                if target_subject_id:
                    season_cached = db.query(BangumiEpisode).filter(
                        BangumiEpisode.subject_id == target_subject_id
                    ).all()
                    
                    if season_cached:
                        season_eps = {}
                        for ce in season_cached:
                            season_eps[ce.sort] = {
                                "name": ce.name_cn or ce.name,
                                "summary": ce.summary or ""
                            }
                        bangumi_metadata[s] = season_eps
                    else:
                        missing_metadata = True
                else:
                    missing_metadata = True

        # Trigger background fetch if missing
        if missing_metadata:
            try:
                from app.tasks.library_tasks import task_fetch_bangumi_metadata
                task_fetch_bangumi_metadata(item_id)
            except Exception as e:
                logger.error(f"Failed to trigger background metadata fetch: {e}")

        # 3. Filter and Format
        final_videos = []
        for v in videos:
            s, e = v.get("season"), v.get("episode")
            if s == 0: continue
            
            # Match metadata
            metadata = bangumi_metadata.get(s, {}).get(e)
            if metadata:
                v["display_name"] = f"S{s:02d}E{e:02d} - {metadata['name']}"
                v["summary"] = metadata["summary"]
            elif s is not None and e is not None:
                v["display_name"] = f"S{s:02d}E{e:02d} - {series_title}"
            else:
                v["display_name"] = os.path.splitext(v["name"])[0]
                
            final_videos.append(v)

        # Sort by season and episode
        final_videos.sort(key=lambda x: (x.get("season") or 999, x.get("episode") or 999, x["name"]))
        return final_videos

    async def fetch_item_metadata_background(self, item_id: int):
        """Fetch and save metadata in the background. Triggered by worker."""
        item = self.get_item(item_id)
        if not item: return
        
        series_title = item.get("title", "Unknown")
        bangumi_id = item.get("bangumi_id")
        path = item["path"]
        
        found_seasons = set()
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(('.mp4', '.mkv', '.avi', '.m4v', '.webm')):
                    folder_match = re.search(r'Season\s*(\d+)', root, re.I)
                    if folder_match:
                        found_seasons.add(int(folder_match.group(1)))
                    else:
                        se_match = re.search(r'[sS](\d+)[eE](\d+)', f)
                        if se_match:
                            found_seasons.add(int(se_match.group(1)))
                        else:
                            found_seasons.add(1)
        
        import asyncio
        tasks = []
        for s in found_seasons:
            if s == 0: continue
            tasks.append(self._sync_season_metadata(s, series_title, bangumi_id, item_id))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def _sync_season_metadata(self, s: int, series_title: str, bangumi_id: int, item_id: int):
        """Fetch from API and save to DB. NO RETURN."""
        from app.services.external.bangumi import BangumiService
        from app.db.session import SessionLocal
        from app.db.models import BangumiEpisode, LibraryItem, BangumiSubjectMapping
        
        bgm_service = BangumiService()
        target_subject_id = None
        
        # 1. Try to find existing mapping for this season
        with SessionLocal() as db:
            mapping = db.query(BangumiSubjectMapping).filter(
                BangumiSubjectMapping.item_id == item_id,
                BangumiSubjectMapping.season == s
            ).first()
            if mapping:
                target_subject_id = mapping.subject_id
            elif s == 1 and bangumi_id:
                target_subject_id = bangumi_id

        # 2. If no ID, search and save mapping
        if not target_subject_id:
            search_query = series_title if s == 1 else f"{series_title} 第{s}季"
            bgm_match = await bgm_service.match_anime(search_query)
            if bgm_match:
                target_subject_id = bgm_match["id"]
                with SessionLocal() as db:
                    # Save mapping
                    db.merge(BangumiSubjectMapping(item_id=item_id, season=s, subject_id=target_subject_id))
                    # If S1, also update LibraryItem
                    if s == 1:
                        db.query(LibraryItem).filter(LibraryItem.id == item_id).update({"bangumi_id": target_subject_id})
                    db.commit()
        
        # 3. Fetch episodes if not in cache
        if target_subject_id:
            with SessionLocal() as db:
                exists = db.query(BangumiEpisode).filter(BangumiEpisode.subject_id == target_subject_id).first()
                if exists: return
                
                bgm_eps = await bgm_service.get_episodes(target_subject_id)
                for be in bgm_eps:
                    ep_num = int(be.get("sort", 0))
                    if ep_num == 0: ep_num = int(be.get("number", 0))
                    
                    db.add(BangumiEpisode(
                        subject_id=target_subject_id,
                        sort=ep_num,
                        name=be.get("name"),
                        name_cn=be.get("name_cn"),
                        summary=be.get("desc") or be.get("summary") or ""
                    ))
                db.commit()

    async def _process_anime_folder(self, folder_path: str, folder_name: str) -> Optional[AnimeItem]:
        """Process a single anime folder"""
        try:
            # Check for seasons
            seasons = 0
            with os.scandir(folder_path) as it:
                for entry in it:
                    if entry.is_dir() and (
                        "season" in entry.name.lower() or 
                        "specials" in entry.name.lower()
                    ):
                        seasons += 1
            if seasons == 0:
                # Might be a single season folder structure or flat structure
                # For now assume if it has video files it's at least 1 season
                has_video = False
                for root, _, files in os.walk(folder_path):
                    if any(f.endswith(('.mp4', '.mkv', '.avi')) for f in files):
                        has_video = True
                        break
                if has_video:
                    seasons = 1

            # Check for local images
            poster_url = None
            local_images = ["poster.jpg", "poster.png", "folder.jpg", "cover.jpg"]
            for img_name in local_images:
                if os.path.exists(os.path.join(folder_path, img_name)):
                    import base64
                    encoded_path = base64.urlsafe_b64encode(os.path.join(folder_path, img_name).encode()).decode()
                    poster_url = f"/api/library/image/{encoded_path}"
                    break
            
            # Metadata holders
            year = None
            status = None
            air_day = None
            tmdb_id = None
            vote_average = 0.0
            overview = None

            # Fetch TMDB metadata
            try:
                tmdb_results = await self.tmdb.search_anime(folder_name)
                if tmdb_results:
                    best_match = tmdb_results[0]
                    tmdb_id = best_match.id
                    
                    # Use TMDB poster if no local one
                    if not poster_url and best_match.poster_path:
                        poster_url = f"https://image.tmdb.org/t/p/w500{best_match.poster_path}"
                    
                    # Get detailed info
                    details = await self.tmdb.get_tv_details(tmdb_id)
                    if details:
                        first_air = details.get('first_air_date', '')
                        if first_air:
                            year = str(first_air.split('-')[0])
                        
                        status = details.get('status')
                        vote_average = details.get('vote_average', 0.0)
                        overview = details.get('overview', '')
                        
                        next_ep = details.get('next_episode_to_air')
                        if next_ep and next_ep.get('air_date'):
                            try:
                                from datetime import datetime
                                dt = datetime.strptime(next_ep['air_date'], "%Y-%m-%d")
                                air_day = dt.weekday()
                            except:
                                pass
            except Exception as e:
                logger.warning(f"TMDB fetch failed for {folder_name}: {e}")

            return AnimeItem(
                title=folder_name,
                path=folder_path,
                poster_url=poster_url,
                season_count=seasons,
                year=year,
                status=status,
                air_day=air_day,
                tmdb_id=tmdb_id,
                vote_average=vote_average,
                overview=overview
            )
        except Exception as e:
            logger.error(f"Error processing folder {folder_name}: {e}")
            return None

    def delete_item(self, item_id: int, delete_file: bool = False, cancel_subscription: bool = False) -> bool:
        """
        Delete a library item.
        :param item_id: Library Item ID
        :param delete_file: Whether to delete the local folder/file
        :param cancel_subscription: Whether to cancel (delete) the associated subscription
        :return: True if successful
        """
        from app.db.session import SessionLocal
        from app.db.models import LibraryItem, Subscription, BangumiSubjectMapping, RSSItem
        import shutil
        
        logger.info(f"Deleting item {item_id}, delete_file={delete_file}, cancel_sub={cancel_subscription}")

        with SessionLocal() as db:
            item = db.query(LibraryItem).filter(LibraryItem.id == item_id).first()
            if not item:
                logger.warning(f"Item {item_id} not found")
                return False

            # 1. Handle Subscription Cancellation
            if cancel_subscription and item.is_subscribed:
                # Find subscription by normalized title match
                # Logic copied from scan_and_refresh
                def normalize(s): return re.sub(r'\s+', '', s.lower()) if s else ""
                target_title = normalize(item.title)
                
                subs = db.query(Subscription).all()
                target_sub = None
                for sub in subs:
                    if normalize(sub.title) == target_title:
                        target_sub = sub
                        break
                
                if target_sub:
                    logger.info(f"Found associated subscription {target_sub.title} (ID: {target_sub.id}). Deleting...")
                    # Delete RSS items first
                    db.query(RSSItem).filter(RSSItem.subscription_id == target_sub.id).delete()
                    # Delete subscription
                    db.delete(target_sub)
                else:
                    logger.warning(f"Subscription for {item.title} not found despite is_subscribed=True")

            # 2. Handle File Deletion
            if delete_file:
                if os.path.exists(item.path):
                    logger.info(f"Deleting path: {item.path}")
                    try:
                        if os.path.isdir(item.path):
                            shutil.rmtree(item.path)
                        else:
                            os.remove(item.path)
                    except Exception as e:
                        logger.error(f"Failed to delete {item.path}: {e}")
                        # Continue to delete DB entry even if file delete fails?
                        # Usually yes.
                else:
                    logger.warning(f"Path does not exist: {item.path}")

            # 3. Clean up DB Relations
            # Bangumi Subject Mappings
            db.query(BangumiSubjectMapping).filter(BangumiSubjectMapping.item_id == item_id).delete()
            
            # Delete the Item itself
            db.delete(item)
            db.commit()
            
            logger.info(f"Item {item_id} deleted successfully")
            return True

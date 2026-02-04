import httpx
from typing import List, Optional, Dict, Any
from loguru import logger
from app.services.system.settings_service import SettingsService

class BangumiService:
    BASE_URL = "https://api.bgm.tv"
    
    def __init__(self):
        self.settings = SettingsService()
        self.api_key = self.settings.get_setting("bangumi.api_key", "")
        # Note: If no setting exists, default to Enabled=True for this feature
        self.enabled = self.settings.get_setting("bangumi.enabled", True)
        
        self.headers = {
            "User-Agent": "Hoshino/0.2 (https://github.com/YiGuMoYan/Hoshino)",
            "Accept": "application/json"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def search(self, keyword: str) -> List[Dict[str, Any]]:
        """Search anime using Bangumi Legacy API (No Auth Required)"""
        if not self.enabled:
            return []
            
        url = f"{self.BASE_URL}/search/subject/{keyword}"
        params = {
            "type": 2, # Anime
            "responseGroup": "small"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=self.headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                
                results = []
                # Legacy search structure is {"results": int, "list": [...]}
                if "list" in data and data["list"]:
                    for item in data["list"]:
                        results.append({
                            "id": item["id"],
                            "name": item["name"],
                            "name_cn": item.get("name_cn", ""),
                            "images": item.get("images", {}),
                            "score": item.get("rating", {}).get("score", 0),
                            "summary": item.get("summary", "")
                        })
                return results
        except Exception as e:
            logger.error(f"Failed to search Bangumi: {e}")
            return []
            
    async def get_subject(self, subject_id: int) -> Dict[str, Any]:
        """Get subject details using API v0 (Public)"""
        if not self.enabled:
            return {}
            
        url = f"{self.BASE_URL}/v0/subjects/{subject_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"Failed to get Bangumi subject {subject_id}: {e}")
            return {}

    async def get_episodes(self, subject_id: int) -> List[Dict[str, Any]]:
        """Get episodes for a subject using Legacy API (Public, contains full ep list)"""
        if not self.enabled:
            return []
            
        # Legacy GET /subject/{id}?responseGroup=large contains 'eps' field
        url = f"{self.BASE_URL}/subject/{subject_id}"
        params = {
            "responseGroup": "large"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=self.headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                
                # Format to look like v0 episodes for compatibility
                episodes = []
                for ep in data.get("eps", []):
                    # Filter regular episodes (type 0)
                    if ep.get("type") == 0:
                        episodes.append({
                            "sort": ep.get("sort"),
                            "name": ep.get("name"),
                            "name_cn": ep.get("name_cn"),
                            "desc": ep.get("desc") or ep.get("summary") or ""
                        })
                return episodes
        except Exception as e:
            logger.error(f"Failed to get episodes for Bangumi legacy subject {subject_id}: {e}")
            return []
            
    async def match_anime(self, title: str) -> Optional[Dict[str, Any]]:
        """Match anime by title"""
        if not self.enabled:
            return None
            
        results = await self.search(title)
        if results:
            # Simple best match: prioritize name_cn exactly or first result
            for res in results:
                if res["name_cn"] == title or res["name"] == title:
                    return res
            return results[0]
        return None

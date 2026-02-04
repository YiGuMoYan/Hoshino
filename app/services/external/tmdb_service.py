import httpx
from typing import List, Optional, Dict, Any
from app.core.config import get_settings
from loguru import logger

class TMDBCandidate:
    """TMDB search result candidate"""
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.name = data.get('name', '')
        self.original_name = data.get('original_name', '')
        self.first_air_date = data.get('first_air_date', '')
        self.overview = data.get('overview', '')
        self.vote_average = data.get('vote_average', 0)
        self.popularity = data.get('popularity', 0)
        self.genre_ids = data.get('genre_ids', [])
        self.origin_country = data.get('origin_country', [])
        self.original_language = data.get('original_language', '')
        self.poster_path = data.get('poster_path', '')
        
    @property
    def year(self) -> Optional[int]:
        """Extract year from first_air_date"""
        if self.first_air_date:
            try:
                return int(self.first_air_date.split('-')[0])
            except:
                return None
        return None
    
    def __repr__(self):
        return f"<TMDBCandidate {self.name} ({self.year})>"

class TMDBService:
    """Service for interacting with TMDB API to search anime"""
    
    ANIMATION_GENRE_ID = 16  # Animation genre ID in TMDB
    
    def __init__(self):
        from app.services.system.settings_service import SettingsService
        
        self.settings = get_settings()
        self.base_url = self.settings.TMDB_BASE_URL
        
        # Read settings
        self.bearer_token = SettingsService.get_setting("tmdb.bearer_token", "")
        self.api_key = SettingsService.get_setting("tmdb.api_key", "")
        self.config_cache = {}

    async def get_configuration(self) -> Dict[str, Any]:
        """Fetch and cache TMDB configuration (images, etc)"""
        if self.config_cache:
            return self.config_cache

        if not self.api_key and not self.bearer_token:
            return {}

        headers = {}
        params = {}

        # Prioritize Bearer Token
        if self.bearer_token:
             headers['Authorization'] = f"Bearer {self.bearer_token}"
        elif self.api_key:
             # Legacy check: if user put bearer in api_key field
             if self.api_key.startswith("ey"):
                 headers['Authorization'] = f"Bearer {self.api_key}"
             else:
                 params['api_key'] = self.api_key

        try:
             async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/configuration",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                self.config_cache = response.json()
                return self.config_cache
        except Exception as e:
            logger.error(f"TMDB Config Error: {e}")
            return {}
        
    async def search_anime(self, query: str, year: Optional[int] = None) -> List[TMDBCandidate]:
        """
        Search for anime on TMDB
        
        Args:
            query: Anime title to search for
            year: Optional year to filter results
            
        Returns:
            List of TMDBCandidate objects
        """
        if not self.api_key:
            logger.warning("Warning: TMDB_API_KEY not configured")
            return []
        
        # Get language preference from settings
        from app.services.system.settings_service import SettingsService
        # Default save/display language
        default_lang = SettingsService.get_setting("tmdb.language", "zh-CN")
        # Search language (fallback to default_lang)
        search_lang = SettingsService.get_setting("tmdb.search_language", default_lang)
        
        params = {
            'query': query,
            'language': search_lang,
            'include_adult': 'false'
        }

        headers = {}
        params = {
            'query': query,
            'language': search_lang,
            'include_adult': 'false'
        }

        # Prioritize Bearer Token
        if self.bearer_token:
             headers['Authorization'] = f"Bearer {self.bearer_token}"
        elif self.api_key:
             if self.api_key.startswith("ey"):
                 headers['Authorization'] = f"Bearer {self.api_key}"
             else:
                 params['api_key'] = self.api_key
        
        if year:
            params['first_air_date_year'] = year
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search/tv",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                
                # Filter for animation genre and Japanese origin
                anime_results = [
                    TMDBCandidate(result) 
                    for result in results
                    if self.ANIMATION_GENRE_ID in result.get('genre_ids', [])
                    and ('JP' in result.get('origin_country', []) or 
                         result.get('original_language') == 'ja')
                ]
                
                return anime_results
                
        except httpx.HTTPStatusError as e:
            logger.error(f"TMDB API HTTP Error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.exception("TMDB API Error")
            return []
    
    async def get_tv_details(self, tv_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a TV show
        
        Args:
            tv_id: TMDB TV show ID
            
        Returns:
            Dictionary with TV show details
        """
        if not self.api_key and not self.bearer_token:
            return None
        
        # Get language preference from settings
        from app.services.system.settings_service import SettingsService
        language = SettingsService.get_setting("tmdb.language", "zh-CN")
        
        params = {
            'language': language
        }
        
        headers = {}
        params = {
            'language': language
        }
        
        # Prioritize Bearer Token
        if self.bearer_token:
             headers['Authorization'] = f"Bearer {self.bearer_token}"
        elif self.api_key:
             if self.api_key.startswith("ey"):
                 headers['Authorization'] = f"Bearer {self.api_key}"
             else:
                 params['api_key'] = self.api_key
        
        try:
            # Append useful metadata: alternative_titles, external_ids, keywords
            params['append_to_response'] = 'alternative_titles,external_ids,keywords,content_ratings'
            
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tv/{tv_id}",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"TMDB API Error: {e}")
            return None

    async def get_season_details(self, tv_id: int, season_number: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a season, including episodes
        """
        if not self.api_key and not self.bearer_token:
            return None
        
        from app.services.system.settings_service import SettingsService
        language = SettingsService.get_setting("tmdb.language", "zh-CN")
        
        headers = {}
        params = {
            'language': language
        }
        
        if self.bearer_token:
             headers['Authorization'] = f"Bearer {self.bearer_token}"
        elif self.api_key:
             if self.api_key.startswith("ey"):
                 headers['Authorization'] = f"Bearer {self.api_key}"
             else:
                 params['api_key'] = self.api_key
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tv/{tv_id}/season/{season_number}",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"TMDB API Error (Season {season_number}): {e}")
            return None
    
    def calculate_confidence(self, candidate: TMDBCandidate, query: str, year: Optional[int] = None) -> float:
        """
        Calculate confidence score for a TMDB candidate
        
        Args:
            candidate: TMDBCandidate object
            query: Original search query
            year: Optional year from filename
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.0
        
        # Title similarity (basic check)
        query_lower = query.lower()
        if query_lower in candidate.name.lower() or query_lower in candidate.original_name.lower():
            score += 0.4
        
        # Year match
        if year and candidate.year == year:
            score += 0.3
        
        # Popularity bonus (normalized)
        if candidate.popularity > 10:
            score += min(0.2, candidate.popularity / 100)
        
        # Vote average bonus
        if candidate.vote_average > 7:
            score += 0.1
        
        return min(1.0, score)

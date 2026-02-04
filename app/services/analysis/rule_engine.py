import re
from typing import Optional
from app.models.result import AnimeNamingResult

class RuleEngine:
    @staticmethod
    def parse_filename(filename: str) -> Optional[AnimeNamingResult]:
        """
        尝试使用正则解析文件名。
        如果找到高置信度的匹配，返回 AnimeNamingResult，否则返回 None。
        """
        # Clean extension
        name_no_ext = filename.rsplit('.', 1)[0]
        
        # Pattern 1: Standard S01E01
        # Example: [Group] Anime Title - S01E01 [1080p]
        s_e_pattern = re.compile(r'(?:\[.*?\]\s*)?(.*?)\s*-\s*S(\d+)E(\d+)', re.IGNORECASE)
        match = s_e_pattern.search(name_no_ext)
        if match:
            title = match.group(1).strip()
            season = int(match.group(2))
            episode = int(match.group(3))
            return AnimeNamingResult(
                anime_title=title,
                season=season,
                episode=episode,
                cour=1,
                original_name=filename,
                rename_to=f"{title} - S{season:02d}E{episode:02d}.mkv", # Temporary extension assumption
                confidence=1.0 # High confidence for explicit SxxExx
            )

        # Pattern 2: Simple numbering
        # Example: [Group] Anime Title - 01 [1080p]
        # This is riskier, as 01 could be anything.
        # We need to rely on the " - " separator usually found in fansubs
        simple_pattern = re.compile(r'(?:\[.*?\]\s*)?(.*?)\s*-\s*(\d+)\s*(?:\[.*?\])?', re.IGNORECASE)
        match = simple_pattern.search(name_no_ext)
        if match:
             title = match.group(1).strip()
             episode_str = match.group(2)
             episode = int(episode_str)
             # Basic sanity check: episode shouldn't be too year-like (e.g. 2023) if it's 4 digits
             if len(episode_str) == 4 and (1900 < episode < 2100):
                 pass # Probably a year
             else:
                return AnimeNamingResult(
                    anime_title=title,
                    season=1, # Default to S1 for simple numbering
                    episode=episode,
                    cour=1,
                    original_name=filename,
                    rename_to=f"{title} - S01E{episode:02d}.mkv",
                    confidence=0.8
                )

        return None

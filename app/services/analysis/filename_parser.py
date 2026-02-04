import re
from typing import Optional, Tuple

class FilenameParser:
    """Helper class to extract anime metadata from filenames"""
    
    @staticmethod
    def extract_anime_info(filename: str) -> Tuple[Optional[str], Optional[int], Optional[int], str]:
        """
        Extract anime title, season, episode and type from filename
        
        Returns:
            Tuple of (title, season, episode, type)
            type is one of: "episode", "ova", "cm", "special"
        """
        # Remove extension
        name_no_ext = filename.rsplit('.', 1)[0]
        
        # Pattern 0: Special/OVA detection (Season 0)
        # Check for [OVA], [OAD], [SP], [Special] tags
        special_pattern = re.compile(r'\[(OVA|OAD|SP|SPECIAL)(?:\s*(\d+))?\]', re.IGNORECASE)
        special_match = special_pattern.search(name_no_ext)
        
        if special_match:
            # It is a special
            episode = int(special_match.group(2)) if special_match.group(2) else 1
            
            # If no number inside tag (e.g. just [OVA]), look for standalone [01]
            if not special_match.group(2):
                 # Search for [digits] anywhere in filename
                 # Be careful not to pick up resolution like [1080] (usually 3-4 digits)
                 # So limit to 1-2 digits for episode typically
                 
                 # But some long series have ep 100+. So 1-3 digits.
                 # Avoid years (19xx, 20xx).
                 
                 potential_eps = re.findall(r'\[(\d{1,3})\]', name_no_ext)
                 if potential_eps:
                     episode = int(potential_eps[0])
            
            # Determine type
            tag = special_match.group(1).upper()
            file_type = "ova"
            
            if "CM" in filename.upper() or "[CM" in filename.upper(): 
                 if "CM" in tag: file_type = "cm"
            
            # Refine type based on tag
            if tag == "SP" or tag == "SPECIAL": file_type = "special"
            
            return (name_no_ext, 0, episode, file_type)

        # Pattern 0b: CM check
        cm_pattern = re.compile(r'\[(CM|PV|NC(?:OP|ED)?)(?:\s*(\d+))?\]', re.IGNORECASE)
        cm_match = cm_pattern.search(name_no_ext)
        if cm_match:
             tag = cm_match.group(1).upper()
             episode = int(cm_match.group(2)) if cm_match.group(2) else 1
             
             # Fallback for bare [CM]
             if not cm_match.group(2):
                 potential_eps = re.findall(r'\[(\d{1,3})\]', name_no_ext)
                 if potential_eps:
                     episode = int(potential_eps[0])
             
             file_type = "cm"
             if "PV" in tag: file_type = "pv"
             if "NC" in tag: file_type = "nc"
             
             return (name_no_ext, 0, episode, file_type)

        # Pattern 1a: Strict Fansub format [Group][Title][Episode]
        fansub_strict = re.compile(r'^\[([^\]]+)\]\[([^\]]+)\]\[(\d+)\]', re.IGNORECASE)
        match = fansub_strict.search(name_no_ext)
        if match:
            title = match.group(2).strip()
            episode = int(match.group(3))
            return (title, None, episode, "episode")

        # Pattern 1b: Relaxed Fansub [Group] Title [Episode] or Title [Episode]
        # Look for the last standalone [number] which is likely the episode
        # But be careful not to match [1080p] or [x264] 
        # Usually episode is [01] or [12], 2 digits. Resolution often 3-4 digits.
        
        # Regex to find [01] or [12] or [123] surrounded by brackets, potentially at the end or middle
        # We capture the text BEFORE this as title candidate (stripping leading [...] groups)
        
        # Example: [Group] Title [01][1080p]
        bracket_ep = re.compile(r'(?:\[.*?\]\s*)*(.*?)\s*\[(\d{1,3})\]', re.IGNORECASE)
        match = bracket_ep.match(name_no_ext) 
        # Note: .match starts from beginning. 
        # But we want to match specifically the structure where title is before episode.
        
        # Let's try a different approach:
        # Find all [digits] occurrences
        bracket_nums = list(re.finditer(r'\[(\d{1,3})\]', name_no_ext))
        if bracket_nums:
            # Usually the first one that looks like an episode (1-3 chars) is the episode
            # But sometimes it could be [1920x1080] (captured as 1920?? no regex restricted to 1-3)
            # If we have multiple, heuristics needed.
            # For now, take the first one found, assuming [Group] doesn't contain [123]
            
            # Better specific regex for the failing case:
            # [Group] Title [Episode]...
            relaxed_pattern = re.compile(r'^\[.*?\]\s*(.+?)\s*\[(\d{1,3})\]', re.IGNORECASE)
            match = relaxed_pattern.search(name_no_ext)
            if match:
                title = match.group(1).strip()
                # If title contains brackets (like nested tags), might need cleaning, but let's trust regex
                # Also exclude if matched "title" is just brackets
                if not title.startswith('[') and not title.endswith(']'): 
                     episode = int(match.group(2))
                     return (title, None, episode, "episode")

        
        # Pattern 2: Standard S##E## format
        # Remove common tags in brackets first
        cleaned = re.sub(r'\[.*?\]', '', name_no_ext).strip()
        
        # Try to extract S##E## pattern
        s_e_pattern = re.compile(r'(.*?)\s*-?\s*S(\d+)E(\d+)', re.IGNORECASE)
        match = s_e_pattern.search(cleaned)
        if match:
            title = match.group(1).strip()
            season = int(match.group(2))
            episode = int(match.group(3))
            return (title, season, episode, "episode")
        
        # Pattern 3: Simple episode pattern: Title - 01
        simple_pattern = re.compile(r'(.*?)\s*-\s*(\d+)', re.IGNORECASE)
        match = simple_pattern.search(cleaned)
        if match:
            title = match.group(1).strip()
            episode_str = match.group(2)
            
            # Skip if it looks like a year
            if len(episode_str) == 4 and (1900 < int(episode_str) < 2100):
                return (cleaned, None, None, "episode")
            
            episode = int(episode_str)
            return (title, None, episode, "episode")  # Default to None (let directory info decide)
        
        # Just return the cleaned title
        return (cleaned, None, None, "episode")
    
    @staticmethod
    def extract_year(filename: str) -> Optional[int]:
        """Extract year from filename if present"""
        # Look for 4-digit year pattern
        year_pattern = re.compile(r'\b(19\d{2}|20\d{2})\b')
        match = year_pattern.search(filename)
        if match:
            return int(match.group(1))
        return None

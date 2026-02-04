"""
File organizer - handles moving files to target library with proper structure
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import re

class FileOrganizer:
    """Organizes anime files into library structure"""
    
    @staticmethod
    def get_first_letter_folder(anime_title: str) -> str:
        """
        Get the first letter folder (A-Z, 0-9, or #)
        
        Args:
            anime_title: Anime title
            
        Returns:
            Folder name (A-Z, 0-9, or #)
        """
        if not anime_title:
            return "#"
        
        first_char = anime_title[0].upper()
        
        # Check if it's strictly ASCII A-Z
        if 'A' <= first_char <= 'Z':
            return first_char
        # Check if it's 0-9
        elif first_char.isdigit():
            return "0-9"
        # Everything else (including Chinese) goes to #
        else:
            return "#"
    
    @staticmethod
    def extract_year_from_title(anime_title: str) -> Optional[int]:
        """Extract year from anime title if present"""
        # Look for (YYYY) or [YYYY] pattern
        match = re.search(r'[\(\[](\d{4})[\)\]]', anime_title)
        if match:
            return int(match.group(1))
        return None
    
    @staticmethod
    def build_target_path(
        library_root: str,
        anime_title: str,
        season: int,
        filename: str,
        year: Optional[int] = None
    ) -> str:
        """
        Build target path following the structure:
        /media/番剧/A-Z/动漫名 (年份)/Season 01/动漫名 - S01E01.mkv
        
        Args:
            library_root: Root library path
            anime_title: Anime title
            season: Season number
            filename: Final filename
            year: Optional year
            
        Returns:
            Full target path
        """
        # Get first letter folder
        letter_folder = FileOrganizer.get_first_letter_folder(anime_title)
        
        # Build anime folder name
        if year:
            anime_folder = f"{anime_title} ({year})"
        else:
            anime_folder = anime_title
        
        # Build season folder
        season_folder = f"Season {season:02d}"
        
        # Combine all parts
        target_path = os.path.join(
            library_root,
            letter_folder,
            anime_folder,
            season_folder,
            filename
        )
        
        return target_path
    
    @staticmethod
    def move_file(source_path: str, target_path: str, dry_run: bool = False) -> bool:
        """
        Move file from source to target, creating directories as needed
        
        Args:
            source_path: Source file path
            target_path: Target file path
            dry_run: If True, only simulate the move
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if dry_run:
                print(f"[DRY RUN] Would move: {source_path} -> {target_path}")
                return True
            
            # Create target directory if it doesn't exist
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Move the file
            shutil.move(source_path, target_path)
            print(f"✓ Moved: {source_path} -> {target_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to move {source_path}: {e}")
            return False

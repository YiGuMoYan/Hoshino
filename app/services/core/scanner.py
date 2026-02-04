import os
from pathlib import Path
from typing import List, Dict, Any
from app.models.payload import FileNode

VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.iso', '.ts', '.ass', '.srt', '.sub', '.vtt'}

class ScannerService:
    @staticmethod
    def scan_directory(path: str) -> Dict[str, List[FileNode]]:
        """
        递归扫描目录并按父目录分组视频文件。
        Returns: { "directory_path": [FileNode, ...] }
        """
        result = {}
        root_path = Path(path)
        
        if not root_path.exists() or not root_path.is_dir():
            raise ValueError(f"Invalid directory path: {path}")

        for dirpath, dirnames, filenames in os.walk(root_path):
            current_dir_files = []
            for f in filenames:
                file_path = Path(dirpath) / f
                if file_path.suffix.lower() in VIDEO_EXTENSIONS:
                    # Calculate relative path from the scan root, or just from the immediate parent
                    # Requirement says "group by directory", so we treat each leaf dir as a unit.
                    
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    node = FileNode(
                        name=f,
                        size_mb=round(size_mb, 2),
                        # Relative path from the scan root might be useful for display
                        rel_path=str(file_path.relative_to(root_path))
                    )
                    current_dir_files.append(node)
            
            if current_dir_files:
                result[dirpath] = current_dir_files
                
        return result

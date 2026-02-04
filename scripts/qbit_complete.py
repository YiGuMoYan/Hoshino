
import sys
import os
import argparse
from loguru import logger

# Add project root to sys.path
# Assuming script is in /scripts/, so root is ../
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Setup Logger to file
log_path = os.path.join(project_root, "logs", "qbit_callback.log")
logger.add(log_path, rotation="1 MB", level="INFO")

def main():
    parser = argparse.ArgumentParser(description="qBittorrent Completion Callback")
    parser.add_argument("info_hash", help="Torrent Info Hash")
    args = parser.parse_args()
    
    info_hash = args.info_hash
    logger.info(f"Callback triggered for hash: {info_hash}")
    
    try:
        from app.services.core.renamer import RenamerService
        service = RenamerService()
        result = service.rename_torrent_files(info_hash)
        
        if result:
            logger.info(f"Successfully renamed files for {info_hash}")
        else:
            logger.info(f"No rename performed for {info_hash} (Check logs/logic)")
            
    except Exception as e:
        logger.error(f"Callback failed: {e}")

if __name__ == "__main__":
    main()

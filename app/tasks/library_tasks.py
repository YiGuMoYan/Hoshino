from huey import crontab
from app.worker import huey
from loguru import logger
from app.services.core.library import LibraryService
import asyncio

@huey.task(name='task_scan_library')
def task_scan_library():
    """
    Background task to scan the media library.
    """
    logger.info("Starting background library scan...")
    try:
        service = LibraryService()
        # Since LibraryService.scan_and_refresh is async, we need to run it in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stats = loop.run_until_complete(service.scan_and_refresh())
        loop.close()
        
        logger.info(f"Background scan finished. Stats: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Background scan failed: {e}")
        import traceback
        traceback.print_exc()
@huey.task(name='task_fetch_bangumi_metadata')
def task_fetch_bangumi_metadata(item_id: int):
    """
    Background task to fetch and cache Bangumi metadata for an item's episodes.
    """
    logger.info(f"Starting background Bangumi metadata fetch for item {item_id}...")
    try:
        service = LibraryService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # We need a method that specifically fetches and saves, without returning data
        loop.run_until_complete(service.fetch_item_metadata_background(item_id))
        loop.close()
        logger.info(f"Background metadata fetch finished for item {item_id}")
    except Exception as e:
        logger.error(f"Background metadata fetch failed for item {item_id}: {e}")
        import traceback
        traceback.print_exc()

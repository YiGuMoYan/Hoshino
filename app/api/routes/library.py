from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict
import base64
import os
from loguru import logger
from app.services.core.library import LibraryService
from app.tasks.library_tasks import task_scan_library

router = APIRouter()

@router.post("/scan", summary="Trigger Library Scan")
def trigger_scan():
    """
    Trigger a background library scan.
    """
    task = task_scan_library()
    return {"status": "success", "message": "Scan started", "task_id": task.id}

@router.get("/items", summary="Get Library Items")
def get_library_items() -> List[Dict]:
    """
    Get all library items from the database.
    """
    service = LibraryService()
    return service.get_all_items()

@router.get("/items/{item_id}/episodes", summary="Get Item Episodes")
async def get_item_episodes(item_id: int) -> List[Dict]:
    """Get all video files for a library item."""
    service = LibraryService()
    return await service.get_episodes(item_id)

@router.delete("/items/{item_id}", summary="Delete Library Item")
def delete_library_item(
    item_id: int, 
    delete_file: bool = False, 
    cancel_subscription: bool = False
):
    """
    Delete a library item.
    - **delete_file**: Also delete the local folder/file
    - **cancel_subscription**: Also cancel/delete the associated subscription
    """
    service = LibraryService()
    success = service.delete_item(item_id, delete_file, cancel_subscription)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found or failed to delete")
    return {"status": "success", "message": "Item deleted"}

@router.get("/stream/{encoded_path}", summary="Stream Video")
def stream_video(encoded_path: str):
    """Stream a video file."""
    try:
        # Decode path
        missing_padding = len(encoded_path) % 4
        if missing_padding:
            encoded_path += '=' * (4 - missing_padding)
        file_path = base64.urlsafe_b64decode(encoded_path).decode()

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Basic range support provided by FileResponse
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            # Fallback for common types if system registry is minimal
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.mkv':
                mime_type = 'video/x-matroska'
            elif ext == '.mp4':
                mime_type = 'video/mp4'
            else:
                mime_type = "application/octet-stream"

        return FileResponse(file_path, media_type=mime_type, filename=os.path.basename(file_path))
    except Exception as e:
        logger.error(f"Error streaming video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/image/{encoded_path}", summary="Serve Local Image")
def get_library_image(encoded_path: str):
    """
    Serve a local image file given its base64 encoded path.
    """
    try:
        # Decode path
        try:
            # Handle padding if needed
            missing_padding = len(encoded_path) % 4
            if missing_padding:
                encoded_path += '=' * (4 - missing_padding)
            file_path = base64.urlsafe_b64decode(encoded_path).decode()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid encoded path")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Verify it's an image
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            raise HTTPException(status_code=400, detail="Invalid image format")

        return FileResponse(file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

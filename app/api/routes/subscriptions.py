
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

import re
from loguru import logger
from app.db.session import get_db
from app.db.models import Subscription, RSSItem
from app.services.external.mikan import MikanService
from app.services.external.bangumi import BangumiService
from app.services.external.tmdb_service import TMDBService
from app.services.system.settings_service import SettingsService

router = APIRouter()
mikan_service = MikanService()
bangumi_service = BangumiService()
tmdb_service = TMDBService()

@router.post("/search", summary="Search Mikan Anime")
def search_mikan(
    payload: dict = Body(...),
    # db: Session = Depends(get_db) # Not needed for search
):
    keyword = payload.get("keyword")
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required")
        
    results = mikan_service.search(keyword)
    return results

@router.get("/bangumi/{mikan_id}", summary="Get Mikan Bangumi Detail (with TMDB & Regex Analysis)")
async def get_mikan_bangumi(mikan_id: str):
    """获取 Mikan 番剧详情（字幕组、TMDB建议等）"""
    # Initial Result from Mikan
    result = mikan_service.get_bangumi_detail(mikan_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Bangumi not found")

    # Enrich with TMDB and Regex Analysis
    title = result.get("title", "")
    enriched = await _analyze_title(title)
    
    # Merge results
    result.update(enriched)
    
    return result

async def _analyze_title(title: str) -> dict:
    """Analyze title to extract season and find TMDB match"""
    
    res = {
        "suggested_title": title,
        "suggested_season": 1,
        "tmdb_id": None,
        "poster_url": None
    }
    
    if not title:
         return res
         
    # 1. Regex Extract Season
    # Common patterns: "第x季", "Season x", "S2"
    # Also support Chinese numerals: 第一季, 第二季...
    cn_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    
    # Regex including Chinese characters
    season_match = re.search(r'(?:第(\d+|[一二三四五六七八九十]+)季|Season\s*(\d+)|S(\d+))', title, re.IGNORECASE)
    
    if season_match:
        # Get groups
        g1, g2, g3 = season_match.groups()
        season_str = g1 or g2 or g3
        
        if season_str in cn_map:
            res["suggested_season"] = cn_map[season_str]
        elif season_str.isdigit():
             res["suggested_season"] = int(season_str)
        
        # Clean title for TMDB search
        # Strip the full matched part
        clean_title = re.sub(r'(?:第(\d+|[一二三四五六七八九十]+)季|Season\s*(\d+)|S(\d+)|II|III)', '', title, flags=re.IGNORECASE).strip()
        search_query = clean_title
    else:
        search_query = title
        
    # 2. TMDB Lookup
    try:
        candidates = await tmdb_service.search_anime(search_query)
        if candidates:
            best = candidates[0]
            res["suggested_title"] = best.name
            res["tmdb_id"] = best.id
            
            # Fetch details for poster if possible (or just use what search gave if it had it?)
            # TMDBCandidate might not have full poster path unless we fetch config
            # But search result usually has 'poster_path'
            # Let's check TMDBCandidate class or just fetch details
            # Or assume TMDBCandidate is enough if we trust the search
            pass
            
            # To be safe and get a good poster, let's try getting config + path
            # But for now, we just want the Name. 
            # Frontend can start a search/scrape if needed, but returning it here is nice.
            
    except Exception as e:
        logger.error(f"TMDB analysis failed: {e}")
        
    return res

@router.post("/", summary="Create Subscription")
def create_subscription(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    payload: {
        "mikan_id": "3405",
        "title": "Frieren",
        "subgroup_id": "615",
        "subgroup_name": "ANi",
        "filter_keywords": ["1080p"],
        "exclude_keywords": [],
        "filter_resolution": "1080p",
        "save_path": "...",
        "auto_download": true,
        "extra_vars": {}
    }
    """
    mikan_id = payload.get("mikan_id")
    subgroup_id = payload.get("subgroup_id")
    
    # Generate RSS URL
    rss_url = mikan_service.get_rss_url(mikan_id, subgroup_id)
    
    # Optional: Enhance with Bangumi Metadata
    bgm_meta = {}
    if bangumi_service.enabled:
        bgm_match = bangumi_service.match_anime(payload.get("title"))
        if bgm_match:
            try:
                bgm_detail = bangumi_service.get_subject(bgm_match["id"])
                bgm_meta = {
                    "bangumi_id": bgm_match["id"],
                    "bangumi_rating": bgm_match.get("rating"),
                    "bangumi_summary": bgm_detail.get("summary"),
                    "bangumi_tags": [t.get("name") for t in bgm_detail.get("tags", [])]
                }
            except:
                pass

    sub = Subscription(
        mikan_id=mikan_id,
        title=payload.get("title"),
        cover_url=payload.get("cover_url"),
        rss_url=rss_url,
        subgroup_id=subgroup_id,
        subgroup_name=payload.get("subgroup_name"),
        filter_keywords=payload.get("filter_keywords", []),
        exclude_keywords=payload.get("exclude_keywords", []),
        filter_resolution=payload.get("filter_resolution"),
        filter_regex=payload.get("filter_regex"),
        save_path=payload.get("save_path"),
        category=payload.get("category", "hoshino"),
        auto_download=payload.get("auto_download", True),
        extra_vars=payload.get("extra_vars", {}),
        status="active",
        last_check_at=datetime.utcnow(), # Set now to indicate checked/fresh
        **bgm_meta
    )
    
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    # Trigger immediate RSS check
    try:
        from app.tasks.rss_monitor import check_subscription_immediate
        check_subscription_immediate(sub.id)
    except Exception as e:
        logger.error(f"Failed to trigger immediate RSS check: {e}")
        
    return sub

@router.get("/", summary="List Subscriptions")
def list_subscriptions(db: Session = Depends(get_db)):
    return db.query(Subscription).order_by(Subscription.created_at.desc()).all()

@router.get("/{id}", summary="Get Subscription")
def get_subscription(id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub

@router.put("/{id}", summary="Update Subscription")
def update_subscription(
    id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(Subscription.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    for key, value in payload.items():
        if hasattr(sub, key):
            setattr(sub, key, value)
            
    # If subgroup changed, update RSS URL
    if "subgroup_id" in payload:
        sub.rss_url = mikan_service.get_rss_url(sub.mikan_id, payload.get("subgroup_id"))
        
    db.commit()
    return sub

@router.delete("/{id}", summary="Delete Subscription")
def delete_subscription(
    id: int, 
    delete_files: bool = False,
    db: Session = Depends(get_db)
):
    logger.info(f"Delete subscription called: id={id}, delete_files={delete_files}")
    
    sub = db.query(Subscription).filter(Subscription.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    logger.info(f"Found subscription: {sub.title}")
    
    # Delete from qBittorrent if requested
    if delete_files:
        logger.info("delete_files=True, fetching RSS items...")
        items = db.query(RSSItem).filter(RSSItem.subscription_id == id).all()
        logger.info(f"Found {len(items)} RSS items")
        
        hashes = [item.download_task_id for item in items if item.download_task_id]
        logger.info(f"Extracted {len(hashes)} hashes (before dedup): {hashes}")
        
        # Deduplicate hashes
        hashes = list(set(hashes))
        logger.info(f"After deduplication: {len(hashes)} unique hashes: {hashes}")
        
        if hashes:
            try:
                from app.services.external.downloader import DownloaderService
                downloader = DownloaderService()
                logger.info(f"Calling downloader.delete_task with {len(hashes)} hashes and delete_files=True")
                downloader.delete_task(hashes, delete_files=True)
                logger.info(f"✅ Successfully deleted {len(hashes)} tasks and files for subscription {id}")
            except Exception as e:
                logger.error(f"❌ Failed to delete tasks from qBittorrent: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to delete torrents: {str(e)}")
        else:
            logger.warning(f"No hashes found for subscription {id}, skipping qBittorrent deletion")
        
        # Delete the subscription folder from disk
        if sub.save_path:
            import shutil
            import os
            try:
                if os.path.exists(sub.save_path):
                    logger.info(f"Deleting folder: {sub.save_path}")
                    shutil.rmtree(sub.save_path)
                    logger.info(f"✅ Successfully deleted folder: {sub.save_path}")
                else:
                    logger.warning(f"Folder does not exist: {sub.save_path}")
            except Exception as e:
                logger.error(f"❌ Failed to delete folder {sub.save_path}: {e}", exc_info=True)
                # Don't raise exception, continue with database deletion
    else:
        logger.info("delete_files=False, skipping qBittorrent deletion")
                
    # Delete associated RSS items
    logger.info("Deleting RSS items from database...")
    db.query(RSSItem).filter(RSSItem.subscription_id == id).delete()
    logger.info("Deleting subscription from database...")
    db.delete(sub)
    db.commit()
    logger.info(f"✅ Subscription {id} deleted from database")
    return {"message": "Deleted"}

@router.post("/{id}/pause", summary="Pause Subscription")
def pause_subscription(id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == id).first()
    if sub:
        sub.status = "paused"
        db.commit()
    return {"message": "Paused"}

@router.post("/{id}/resume", summary="Resume Subscription")
def resume_subscription(id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == id).first()
    if sub:
        sub.status = "active"
        db.commit()
    return {"message": "Resumed"}

@router.post("/{id}/check", summary="Manual Check Subscription")
def check_subscription_manual(id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    try:
        from app.tasks.rss_monitor import check_subscription_immediate
        check_subscription_immediate(sub.id)
    except Exception as e:
        logger.error(f"Failed to trigger manual check: {e}")
        return {"message": "Check triggered but failed to enqueue"}
        
    return {"message": "Check triggered"}

@router.get("/{id}/items", summary="Get RSS Items")
def get_rss_items(id: int, db: Session = Depends(get_db)):
    return db.query(RSSItem).filter(RSSItem.subscription_id == id).order_by(RSSItem.pub_date.desc()).all()

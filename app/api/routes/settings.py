from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.system.settings_service import SettingsService
from app.db.session import get_db
from app.db.models import LLMConfig, LLMPreset
from app.models.settings import AppSettingsSchema, AppSettingsBase, LLMConfigSchema, LLMConfigBase
from app.models.preset import LLMPresetCreate, LLMPresetResponse
from app.services.analysis.llm_engine import LLMEngine

router = APIRouter()

# --- Settings API (Key-Value) ---

# --- Presets API ---

@router.get("/presets", response_model=List[LLMPresetResponse])
def list_presets(db: Session = Depends(get_db)):
    """
    List all available LLM presets.
    """
    import os
    from app.core.logger import logger
    logger.info(f"DEBUG: list_presets called.")
    logger.info(f"DEBUG: DB URL: {db.bind.url}")
    presets = db.query(LLMPreset).all()
    logger.info(f"DEBUG: Found {len(presets)} presets.")
    for p in presets:
        logger.info(f"DEBUG: Preset: {p.name} (id={p.id})")
    return presets

@router.post("/presets", response_model=LLMPresetResponse)
def create_preset(
    preset: LLMPresetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new custom preset.
    """
    db_preset = LLMPreset(
        name=preset.name,
        base_url=preset.base_url,
        model=preset.model,
        api_key=preset.api_key
    )
    try:
        db.add(db_preset)
        db.commit()
        db.refresh(db_preset)
        return db_preset
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Preset name already exists or invalid data.")

@router.delete("/presets/{preset_id}")
def delete_preset(
    preset_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a preset.
    """
    preset = db.query(LLMPreset).filter(LLMPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    db.delete(preset)
    db.commit()
    return {"status": "success", "message": "Preset deleted"}

@router.put("/presets/{preset_id}", response_model=LLMPresetResponse)
def update_preset(
    preset_id: int,
    preset_data: LLMPresetCreate,
    db: Session = Depends(get_db)
):
    """
    Update an existing preset.
    """
    preset = db.query(LLMPreset).filter(LLMPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    preset.name = preset_data.name
    preset.base_url = preset_data.base_url
    preset.model = preset_data.model
    if preset_data.api_key:
        preset.api_key = preset_data.api_key
    
    try:
        db.commit()
        db.refresh(preset)
        return preset
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update failed")

# --- LLM Test ---

@router.post("/llm/test")
async def test_llm_connection(
    config: LLMConfigBase,
):
    """
    Test LLM connection with provided config.
    """
    # Create a temporary config object for testing
    temp_config = LLMConfig(
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model
    )
    
    success = await LLMEngine.test_connection(temp_config)
    if success:
        return {"status": "success", "message": "Connection successful"}
    else:
        raise HTTPException(status_code=400, detail="Connection failed")

# --- Settings API (Key-Value) ---

@router.get("")
def get_all_settings():
    """
    获取所有设置，按类别分组。
    返回格式: {"app": [...], "llm": [...], "tmdb": [...]}
    """
    return SettingsService.get_all_settings()

@router.get("/{category}")
def get_settings_by_category(category: str):
    """
    获取指定类别的设置。
    """
    return SettingsService.get_settings_by_category(category)

class SettingsUpdate(BaseModel):
    updates: Dict[str, str]

@router.put("")
def update_settings(data: SettingsUpdate):
    """
    批量更新设置
    """
    success = SettingsService.batch_update(data.updates)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")
    return {"status": "success", "message": "Settings updated"}

@router.post("/notification/test-email")
def send_test_email():
    """
    发送测试邮件
    """
    from app.services.notification.email_service import EmailService
    email_service = EmailService()
    success = email_service.send_test_email()
    if success:
        return {"status": "success", "message": "Email sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")


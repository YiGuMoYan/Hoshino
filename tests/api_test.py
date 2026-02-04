import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, init_db
from app.db.models import SettingsModel
from app.main import app

client = TestClient(app)

# Ensure DB is init
init_db()

# Mock LLM response
async def mock_analyze(payload):
    # ... mock logic ...
    pass

@pytest.fixture(autouse=True)
def setup_db():
    # Insert test settings
    db = SessionLocal()
    settings = SettingsModel(
        openai_api_key="test-key",
        openai_base_url="http://test-url",
        openai_model="test-model"
    )
    # Clear old table if needed or just add
    db.query(SettingsModel).delete()
    db.add(settings)
    db.commit()
    db.close()

# Mock LLM response
async def mock_analyze(payload):
    results = []
    for f in payload.files:
        results.append(AnimeNamingResult(
            anime_title="Mock API Title",
            season=1,
            episode=1,
            cour=1,
            original_name=f.name,
            rename_to=f"Mock API Title - S01E01.mkv",
            confidence=0.9
        ))
    return BatchNamingResult(results=results)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hoshino Backend is running"}

def test_scan_flow():
    # Setup dummy directory
    test_dir = "test_media_api/A-Z/TestAPI"
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "TestAPI - 01.mkv"), 'w') as fh:
        fh.write("dummy")

    try:
        # Patch LLM to avoid real calls
        with patch('app.services.llm_engine.LLMEngine.analyze', side_effect=mock_analyze):
            # 1. SCAN
            response = client.post("/api/scan", json={"path": "test_media_api"})
            assert response.status_code == 200
            plan = response.json()
            assert len(plan) > 0
            assert plan[0]["status"] == "pending"
            assert "S01E01" in plan[0]["new_path"]

            # 2. EXECUTE
            response = client.post("/api/execute", json=plan)
            assert response.status_code == 200
            executed_plan = response.json()
            assert executed_plan[0]["status"] == "done"
            # Wait, my execute_plan implementation returns the input plan.
            # But the 'organizer.execute_plan' modifies the objects in place?
            # Pydantic models are immutable-ish or at least copied when passed via API.
            # The SERVER side 'organizer' has the journal.
            
            # Let's verify file movement
            new_path = plan[0]["new_path"]
            assert os.path.exists(new_path)
            assert not os.path.exists(plan[0]["original_path"])

            # 3. ROLLBACK
            response = client.post("/api/rollback")
            assert response.status_code == 200
            
            # Verify rollback
            assert os.path.exists(plan[0]["original_path"])
            assert not os.path.exists(new_path)

    finally:
        import shutil
        if os.path.exists("test_media_api"):
            shutil.rmtree("test_media_api")

def test_settings():
    # GET default (inserted by fixture)
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["openai_api_key"] == "test-key"

    # UPDATE
    new_settings = {
        "openai_api_key": "new-key",
        "openai_base_url": "new-url",
        "openai_model": "new-model"
    }
    response = client.post("/api/settings", json=new_settings)
    assert response.status_code == 200
    
    # GET again
    response = client.get("/api/settings")
    assert response.json()["openai_api_key"] == "new-key"

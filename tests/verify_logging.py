import asyncio
import json
import os
import sys
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app.core.logger import setup_logger
from loguru import logger
from app.api.routes.logs import get_logs

async def verify_logger():
    print("--- 1. Testing Logger Write ---")
    setup_logger()
    
    test_msg = f"Verification Test Message {datetime.now().timestamp()}"
    logger.info(test_msg)
    
    # Check if file exists
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = f"logs/hoshino_{today}.log"
    
    if not os.path.exists(log_file):
        print(f"FAILED: Log file {log_file} not created.")
        return False
        
    print(f"SUCCESS: Log file {log_file} exists.")
    
    # Check content
    found = False
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if test_msg in line:
                try:
                    data = json.loads(line)
                    if data["record"]["message"] == test_msg:
                        found = True
                        break
                except:
                    pass
    
    if found:
        print("SUCCESS: Log message found and is valid JSON.")
    else:
        print("FAILED: Log message not found in file.")
        return False

    print("\n--- 2. Testing API Read ---")
    # Simulate API call
    try:
        logs = await get_logs(limit=10)
        # Check if our message is in the returned logs
        api_found = False
        for log in logs:
            if log["message"] == test_msg:
                api_found = True
                print(f"API Log Entry: {log}")
                break
        
        if api_found:
            print("SUCCESS: API retrieved the log entry.")
            return True
        else:
            print("FAILED: API did not return the test log entry.")
            return False
            
    except Exception as e:
        print(f"FAILED: API call threw exception: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(verify_logger())
    if not success:
        sys.exit(1)

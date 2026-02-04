from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pathlib import Path
import json
from datetime import date as date_type
from datetime import datetime

router = APIRouter()

LOG_DIR = Path("logs")

@router.get("", response_model=List[dict])
async def get_logs(
    date: Optional[date_type] = None,
    level: Optional[str] = None,
    module: Optional[str] = None,
    limit: int = 1000
):
    """
    获取系统日志
    
    - date: 日期 (默认今天)
    - level: 日志级别 filter (INFO, WARNING, ERROR)
    - module: 模块名 filter
    - limit: 返回条数限制
    """
    if date is None:
        target_date = datetime.now().date()
    else:
        target_date = date
        
    # 构建文件名: hoshino_2024-02-03.log
    filename = f"hoshino_{target_date.strftime('%Y-%m-%d')}.log"
    file_path = LOG_DIR / filename
    
    if not file_path.exists():
        # 如果文件不存在，返回空列表 (可能是今天还没日志，或者请求了未来的日期)
        return []

    logs = []
    
    try:
        # 读取文件 (JSON Lines 格式)
        # 注意：如果文件很大，这里应该倒序读取或流式读取。
        # 考虑到按天切割且 limit 存在，这里简单读取全部再过滤
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # 倒序处理，显示最新的日志
        for line in reversed(lines):
            if len(logs) >= limit:
                break
                
            try:
                log_entry = json.loads(line)
                record = log_entry.get("record", {})
                
                # Filter by Level
                if level and record.get("level", {}).get("name") != level.upper():
                    continue
                    
                # Filter by Module (简单的子串匹配)
                if module and module.lower() not in record.get("name", "").lower():
                    continue
                
                # 提取前端需要的字段，简化 payload
                formatted_entry = {
                    "timestamp": datetime.fromtimestamp(record["time"]["timestamp"]).isoformat(),
                    "level": record["level"]["name"],
                    "module": f"{record['name']}:{record['function']}:{record['line']}",
                    "message": record["message"],
                    "extra": record["extra"]
                }
                
                logs.append(formatted_entry)
                
            except json.JSONDecodeError:
                continue
                
        return logs

    except Exception as e:
        # 记录读取错误但不崩溃
        print(f"Error reading logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to read logs")

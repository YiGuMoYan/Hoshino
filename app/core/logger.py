import sys
from loguru import logger
from pathlib import Path

# 定义日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 配置日志文件路径
LOG_FILE = LOG_DIR / "hoshino_{time:YYYY-MM-DD}.log"

def setup_logger():
    """
    配置全局 Logger
    - 移除默认 Handler
    - 添加控制台输出 (带颜色)
    - 添加文件输出 (JSON 格式，按天轮转，保留 7 天)
    """
    logger.remove()
    
    # console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # file handler (JSON)
    logger.add(
        LOG_FILE,
        rotation="00:00",  # 每天午夜轮转
        retention="7 days", # 保留 7 天
        serialize=True,     # 保存为 JSON 格式
        encoding="utf-8",
        level="INFO",
        enqueue=True # 异步写入
    )

    logger.info("系统日志初始化完成")

# 初始化
setup_logger()

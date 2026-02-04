from huey import SqliteHuey
import os

# 使用 SQLite 作为 Huey 后端
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.getenv("HOSHINO_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
db_path = os.path.join(DATA_DIR, 'huey_tasks.db')

# 确保目录存在
os.makedirs(os.path.dirname(db_path), exist_ok=True)

huey = SqliteHuey(
    'hoshino_tasks',
    filename=db_path,
    immediate=False  # 异步执行
)

"""Huey Worker 启动脚本"""
from app.worker import huey

# 导入所有任务以注册到 TaskRegistry
# 导入所有任务以注册到 TaskRegistry
from app.tasks.scan_task import execute_scan_task
import app.tasks.download_monitor # 导入监控任务
import app.tasks.rss_monitor # 导入 RSS 监控任务
import app.tasks.library_tasks # 导入媒体库扫描任务

if __name__ == "__main__":
    from huey.consumer import Consumer
    
    print("Starting Huey worker...")
    print("Registered tasks:")
    for task_name in huey._registry._registry:
        print(f"  - {task_name}")
    print("Press Ctrl+C to stop")
    print()
    
    consumer = Consumer(huey)
    consumer.run()

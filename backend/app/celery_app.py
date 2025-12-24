"""
Celery异步任务配置
"""
try:
    from celery import Celery
    from app.core.config import settings
    
    celery_app = Celery(
        "film_education",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks.ai_tasks"]
    )
    
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30分钟超时
        task_soft_time_limit=25 * 60,  # 25分钟软超时
    )
    
    CELERY_AVAILABLE = True
except ImportError:
    # Celery未安装，使用模拟对象
    class MockAsyncResult:
        def __init__(self, task_id):
            self.id = task_id
            self.state = "PENDING"
            self.result = None
            self.info = {}
    
    class MockCelery:
        def AsyncResult(self, task_id):
            return MockAsyncResult(task_id)
    
    celery_app = MockCelery()
    CELERY_AVAILABLE = False


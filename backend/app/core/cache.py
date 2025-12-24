"""
缓存服务 - 使用Redis或内存缓存
"""
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import time

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("警告: Redis未安装，将使用内存缓存")

from app.core.config import settings

class CacheService:
    """缓存服务"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache: dict = {}
        self.use_redis = False
        
        if REDIS_AVAILABLE:
            try:
                # 尝试连接Redis
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
                self.redis_client.ping()
                self.use_redis = True
                print("✅ Redis缓存已启用")
            except Exception as e:
                print(f"⚠️  Redis连接失败，使用内存缓存: {e}")
                self.use_redis = False
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if self.use_redis and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                print(f"Redis获取缓存失败: {e}")
        
        # 内存缓存
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if time.time() < entry['expires_at']:
                return entry['value']
            else:
                del self.memory_cache[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
                return
            except Exception as e:
                print(f"Redis设置缓存失败: {e}")
        
        # 内存缓存
        self.memory_cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
    
    def delete(self, key: str):
        """删除缓存"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                print(f"Redis删除缓存失败: {e}")
        
        self.memory_cache.pop(key, None)
    
    def clear(self, pattern: Optional[str] = None):
        """清除缓存"""
        if self.use_redis and self.redis_client and pattern:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                print(f"Redis清除缓存失败: {e}")
        
        if not pattern:
            self.memory_cache.clear()

# 全局缓存实例
cache_service = CacheService()

def cached(prefix: str, ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_service._make_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator












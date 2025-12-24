"""
AI模型管理器 - 统一管理模型加载、缓存和生命周期
"""
import os
import time
from typing import Dict, Any, Optional, Callable
from functools import lru_cache
import threading
from datetime import datetime, timedelta

class ModelCache:
    """模型缓存管理"""
    def __init__(self, ttl: int = 3600):  # 默认1小时过期
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if datetime.now() < entry['expires_at']:
                    return entry['value']
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        with self.lock:
            self.cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=self.ttl),
                'created_at': datetime.now()
            }
    
    def clear(self, key: Optional[str] = None):
        """清除缓存"""
        with self.lock:
            if key:
                self.cache.pop(key, None)
            else:
                self.cache.clear()
    
    def cleanup_expired(self):
        """清理过期缓存"""
        with self.lock:
            now = datetime.now()
            expired_keys = [
                k for k, v in self.cache.items()
                if now >= v['expires_at']
            ]
            for k in expired_keys:
                del self.cache[k]

class ModelManager:
    """AI模型管理器 - 延迟加载和缓存策略"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_loaders: Dict[str, Callable] = {}
        self.model_cache = ModelCache()
        self.loading_locks: Dict[str, threading.Lock] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_model(
        self,
        model_name: str,
        loader_func: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """注册模型加载器"""
        self.model_loaders[model_name] = loader_func
        self.loading_locks[model_name] = threading.Lock()
        self.model_metadata[model_name] = metadata or {}
    
    def get_model(self, model_name: str, force_reload: bool = False) -> Optional[Any]:
        """获取模型实例（延迟加载）"""
        # 检查缓存
        cache_key = f"model_{model_name}"
        if not force_reload:
            cached = self.model_cache.get(cache_key)
            if cached is not None:
                return cached
        
        # 如果已加载，直接返回
        if model_name in self.models and not force_reload:
            return self.models[model_name]
        
        # 延迟加载
        if model_name not in self.model_loaders:
            raise ValueError(f"模型 {model_name} 未注册")
        
        # 使用锁防止并发加载
        lock = self.loading_locks.get(model_name)
        if lock:
            with lock:
                # 双重检查
                if model_name in self.models and not force_reload:
                    return self.models[model_name]
                
                try:
                    print(f"🔄 正在加载模型: {model_name}")
                    start_time = time.time()
                    model = self.model_loaders[model_name]()
                    load_time = time.time() - start_time
                    
                    self.models[model_name] = model
                    self.model_cache.set(cache_key, model)
                    
                    print(f"✅ 模型 {model_name} 加载完成，耗时 {load_time:.2f}秒")
                    return model
                except Exception as e:
                    print(f"❌ 模型 {model_name} 加载失败: {e}")
                    return None
        
        return None
    
    def unload_model(self, model_name: str):
        """卸载模型（释放内存）"""
        if model_name in self.models:
            del self.models[model_name]
            self.model_cache.clear(f"model_{model_name}")
            print(f"🗑️  模型 {model_name} 已卸载")
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            'name': model_name,
            'loaded': model_name in self.models,
            'metadata': self.model_metadata.get(model_name, {}),
        }
        return info
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """列出所有已注册的模型"""
        return {
            name: self.get_model_info(name)
            for name in self.model_loaders.keys()
        }

# 全局模型管理器实例
model_manager = ModelManager()












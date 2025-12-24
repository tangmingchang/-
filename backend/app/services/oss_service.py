"""
阿里云OSS对象存储服务
用于将本地图片上传到公网可访问的OSS
"""
import os
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
from app.core.config import settings

try:
    import oss2
    OSS2_AVAILABLE = True
except ImportError:
    OSS2_AVAILABLE = False
    oss2 = None


class OSSService:
    """阿里云OSS服务"""
    
    def __init__(self):
        self.access_key_id = getattr(settings, 'OSS_ACCESS_KEY_ID', '')
        self.access_key_secret = getattr(settings, 'OSS_ACCESS_KEY_SECRET', '')
        self.bucket_name = getattr(settings, 'OSS_BUCKET_NAME', '')
        self.endpoint = getattr(settings, 'OSS_ENDPOINT', '')
        self.bucket_domain = getattr(settings, 'OSS_BUCKET_DOMAIN', '')  # 自定义域名，如：https://cdn.example.com
        
        self._bucket = None
        
        # 检查OSS配置
        if self.access_key_id and self.access_key_secret and self.bucket_name and self.endpoint:
            print(f"[OSS] ✅ OSS配置已加载")
            print(f"[OSS] Bucket: {self.bucket_name}")
            print(f"[OSS] Endpoint: {self.endpoint}")
            if self.bucket_domain:
                print(f"[OSS] 自定义域名: {self.bucket_domain}")
        else:
            print(f"[OSS] ⚠️  OSS未完全配置，将使用备用方案（base64编码）")
            missing = []
            if not self.access_key_id:
                missing.append("OSS_ACCESS_KEY_ID")
            if not self.access_key_secret:
                missing.append("OSS_ACCESS_KEY_SECRET")
            if not self.bucket_name:
                missing.append("OSS_BUCKET_NAME")
            if not self.endpoint:
                missing.append("OSS_ENDPOINT")
            if missing:
                print(f"[OSS] 缺少配置项: {', '.join(missing)}")
                print(f"[OSS] 配置方法: 在.env文件中添加OSS配置，参考 OSS配置指南.md")
    
    def _get_bucket(self):
        """获取OSS Bucket对象"""
        if not OSS2_AVAILABLE:
            return None
        
        if not all([self.access_key_id, self.access_key_secret, self.bucket_name, self.endpoint]):
            return None
        
        if self._bucket is None:
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self._bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
        
        return self._bucket
    
    def upload_file(self, local_file_path: str, object_key: Optional[str] = None) -> Dict[str, Any]:
        """
        上传文件到OSS
        
        Args:
            local_file_path: 本地文件路径
            object_key: OSS对象键（路径），如果不提供则自动生成
        
        Returns:
            包含公网URL的字典
        """
        if not OSS2_AVAILABLE:
            return {
                "error": "oss2未安装",
                "message": "请安装oss2: pip install oss2",
                "fallback": True  # 标记可以使用备用方案
            }
        
        bucket = self._get_bucket()
        if not bucket:
            return {
                "error": "OSS未配置",
                "message": "请在.env文件中配置OSS相关参数",
                "fallback": True
            }
        
        if not os.path.exists(local_file_path):
            return {
                "error": "文件不存在",
                "message": f"本地文件不存在: {local_file_path}"
            }
        
        # 生成对象键（如果没有提供）
        if not object_key:
            file_ext = os.path.splitext(local_file_path)[1]
            object_key = f"images/{uuid.uuid4().hex}{file_ext}"
        
        try:
            # 上传文件
            with open(local_file_path, 'rb') as f:
                bucket.put_object(object_key, f)
            
            # 生成公网URL
            if self.bucket_domain:
                # 使用自定义域名
                public_url = f"{self.bucket_domain.rstrip('/')}/{object_key}"
            else:
                # 使用OSS默认域名
                public_url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '').replace('http://', '')}/{object_key}"
            
            return {
                "success": True,
                "public_url": public_url,
                "object_key": object_key,
                "message": "文件上传成功"
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "message": f"OSS上传失败: {type(e).__name__}",
                "fallback": True
            }
    
    def upload_file_content(self, file_content: bytes, file_ext: str = ".jpg", object_key: Optional[str] = None) -> Dict[str, Any]:
        """
        直接上传文件内容到OSS（不需要先保存到本地）
        
        Args:
            file_content: 文件内容（字节）
            file_ext: 文件扩展名
            object_key: OSS对象键（路径），如果不提供则自动生成
        
        Returns:
            包含公网URL的字典
        """
        if not OSS2_AVAILABLE:
            return {
                "error": "oss2未安装",
                "message": "请安装oss2: pip install oss2",
                "fallback": True
            }
        
        bucket = self._get_bucket()
        if not bucket:
            return {
                "error": "OSS未配置",
                "message": "请在.env文件中配置OSS相关参数",
                "fallback": True
            }
        
        # 生成对象键（如果没有提供）
        if not object_key:
            object_key = f"images/{uuid.uuid4().hex}{file_ext}"
        
        try:
            # 上传文件内容
            bucket.put_object(object_key, file_content)
            
            # 生成公网URL
            if self.bucket_domain:
                # 使用自定义域名
                public_url = f"{self.bucket_domain.rstrip('/')}/{object_key}"
            else:
                # 使用默认Bucket域名
                endpoint_clean = self.endpoint.replace('https://', '').replace('http://', '')
                public_url = f"https://{self.bucket_name}.{endpoint_clean}/{object_key}"
            
            print(f"[OSS] 上传成功: {object_key}")
            print(f"[OSS] 公网URL: {public_url}")
            
            return {
                "success": True,
                "public_url": public_url,
                "object_key": object_key,
                "message": "文件上传成功"
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "message": f"OSS上传失败: {type(e).__name__}",
                "fallback": True
            }


class SimpleImageHostingService:
    """简单的图床服务（备用方案）"""
    
    async def upload_to_smms(self, file_path: str) -> Dict[str, Any]:
        """
        上传到sm.ms图床（需要登录，已废弃）
        现在使用本地HTTP服务器方案
        """
        # sm.ms需要登录，不再使用
        return {
            "error": "sm.ms需要登录",
            "message": "请配置OSS或使用本地HTTP服务器",
            "fallback": True
        }
    
    def get_local_server_url(self, file_path: str, port: int = 8888) -> Dict[str, Any]:
        """
        获取本地HTTP服务器URL（用于测试）
        注意：这需要启动一个本地HTTP服务器
        
        Args:
            file_path: 本地文件路径
            port: 服务器端口
        
        Returns:
            包含本地URL的字典
        """
        if not os.path.exists(file_path):
            return {
                "error": "文件不存在",
                "message": f"本地文件不存在: {file_path}"
            }
        
        # 生成相对路径（从项目根目录）
        abs_path = os.path.abspath(file_path)
        # 尝试找到项目根目录
        project_root = Path(__file__).parent.parent.parent
        try:
            rel_path = os.path.relpath(abs_path, project_root)
            # Windows路径转换为URL路径
            rel_path = rel_path.replace('\\', '/')
            local_url = f"http://localhost:{port}/{rel_path}"
        except:
            # 如果无法计算相对路径，使用绝对路径的简化版本
            filename = os.path.basename(file_path)
            local_url = f"http://localhost:{port}/media/test/{filename}"
        
        return {
            "success": True,
            "public_url": local_url,
            "message": f"本地HTTP服务器URL（需要启动服务器在端口{port}）",
            "note": "这是测试用的本地URL，生产环境请配置OSS"
        }


class ImageUploadService:
    """统一的图片上传服务（自动选择OSS或备用方案）"""
    
    def __init__(self):
        self.oss_service = OSSService()
        self.simple_service = SimpleImageHostingService()
    
    async def upload_image(self, file_path: str, use_fallback: bool = True, local_server_port: int = 8888) -> Dict[str, Any]:
        """
        上传图片到公网
        
        Args:
            file_path: 本地文件路径
            use_fallback: 如果OSS不可用，是否使用备用方案
            local_server_port: 本地HTTP服务器端口（用于测试）
        
        Returns:
            包含公网URL的字典
        """
        # 优先使用OSS
        result = self.oss_service.upload_file(file_path)
        
        if result.get("success"):
            return result
        
        # 如果OSS不可用且允许使用备用方案
        if use_fallback and result.get("fallback"):
            print("⚠️  OSS不可用，使用本地HTTP服务器（测试用）")
            print(f"   提示: 请确保本地HTTP服务器在端口{local_server_port}运行")
            print(f"   启动命令: python start_image_server.py")
            return self.simple_service.get_local_server_url(file_path, local_server_port)
        
        return result
    
    async def upload_image_content(self, file_content: bytes, file_ext: str = ".jpg", use_fallback: bool = True) -> Dict[str, Any]:
        """
        直接上传图片内容到公网（不需要先保存到本地）
        
        Args:
            file_content: 图片内容（字节）
            file_ext: 文件扩展名
            use_fallback: 如果OSS不可用，是否使用备用方案
        
        Returns:
            包含公网URL的字典
        """
        # 优先使用OSS
        result = self.oss_service.upload_file_content(file_content, file_ext)
        
        if result.get("success"):
            return result
        
        # 如果OSS不可用，需要先保存到临时文件
        if use_fallback and result.get("fallback"):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            try:
                print("⚠️  OSS不可用，使用备用图床服务（sm.ms）")
                return await self.simple_service.upload_to_smms(tmp_path)
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        
        return result


# 全局实例
image_upload_service = ImageUploadService()


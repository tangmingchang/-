"""
将media/videos中的视频添加到student1的项目中
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.project import Project, MediaAsset
from datetime import datetime

def main():
    db = SessionLocal()
    try:
        # 查找student1
        student = db.query(User).filter(User.username == "student1").first()
        if not student:
            print("错误：找不到student1用户")
            return
        
        print(f"找到学生: {student.username} (ID: {student.id})")
        
        # 查找student1的项目（取第一个，或者名为"AI生成cp视频"的项目）
        project = db.query(Project).filter(
            Project.owner_id == student.id,
            Project.name.like("%AI%")
        ).first()
        
        if not project:
            # 如果没有找到，取第一个项目
            project = db.query(Project).filter(Project.owner_id == student.id).first()
        
        if not project:
            print("错误：找不到student1的项目")
            return
        
        print(f"找到项目: {project.name} (ID: {project.id})")
        
        # 查找media/videos目录中的视频
        videos_dir = os.path.join(os.path.dirname(__file__), "media", "videos")
        if not os.path.exists(videos_dir):
            print(f"错误：视频目录不存在: {videos_dir}")
            return
        
        video_files = [f for f in os.listdir(videos_dir) 
                      if os.path.isfile(os.path.join(videos_dir, f)) 
                      and f.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'))]
        
        print(f"找到 {len(video_files)} 个视频文件")
        
        # 检查每个视频是否已经关联到项目
        added_count = 0
        for video_file in video_files:
            file_path = os.path.join(videos_dir, video_file)
            relative_path = f"/media/videos/{video_file}"
            
            # 检查是否已经存在
            existing = db.query(MediaAsset).filter(
                MediaAsset.project_id == project.id,
                MediaAsset.file_path == relative_path
            ).first()
            
            if existing:
                print(f"  视频已存在: {video_file}")
                continue
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 确定MIME类型
            ext = os.path.splitext(video_file)[1].lower()
            mime_types = {
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime',
                '.wmv': 'video/x-ms-wmv',
                '.flv': 'video/x-flv',
                '.mkv': 'video/x-matroska',
                '.webm': 'video/webm'
            }
            mime_type = mime_types.get(ext, 'video/mp4')
            
            # 创建MediaAsset记录
            media_asset = MediaAsset(
                project_id=project.id,
                name=video_file,
                asset_type="video",
                file_path=relative_path,
                file_size=file_size,
                mime_type=mime_type,
                is_ai_generated=True,  # 假设是AI生成的
                created_at=datetime.utcnow()
            )
            
            db.add(media_asset)
            added_count += 1
            print(f"  添加视频: {video_file}")
        
        if added_count > 0:
            db.commit()
            print(f"\n成功添加 {added_count} 个视频到项目 '{project.name}'")
        else:
            print("\n所有视频已经关联到项目")
        
        # 显示项目中的所有媒体资产
        all_assets = db.query(MediaAsset).filter(MediaAsset.project_id == project.id).all()
        print(f"\n项目 '{project.name}' 现在有 {len(all_assets)} 个媒体资产:")
        images = [a for a in all_assets if a.asset_type == 'image']
        videos = [a for a in all_assets if a.asset_type == 'video']
        print(f"  图片: {len(images)} 个")
        print(f"  视频: {len(videos)} 个")
        for asset in all_assets:
            print(f"  - {asset.name} ({asset.asset_type})")
        
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()


"""
数据库迁移脚本：为evaluations表添加缺失的列
"""
import sqlite3
import os
from pathlib import Path

def migrate_evaluations_table():
    """为evaluations表添加缺失的列"""
    # 获取脚本所在目录（backend目录）
    script_dir = Path(__file__).parent
    db_path = script_dir / "film_education.db"
    
    if not db_path.exists():
        print("数据库文件不存在，将在下次启动时自动创建")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluations'")
        if not cursor.fetchone():
            print("evaluations表不存在，将在下次启动时自动创建")
            conn.close()
            return
        
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(evaluations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 添加缺失的列
        if 'teacher_feedback_box' not in columns:
            print("添加 teacher_feedback_box 列...")
            cursor.execute("ALTER TABLE evaluations ADD COLUMN teacher_feedback_box TEXT")
            print("[OK] teacher_feedback_box 列已添加")
        else:
            print("teacher_feedback_box 列已存在")
        
        if 'detailed_analysis' not in columns:
            print("添加 detailed_analysis 列...")
            cursor.execute("ALTER TABLE evaluations ADD COLUMN detailed_analysis JSON")
            print("[OK] detailed_analysis 列已添加")
        else:
            print("detailed_analysis 列已存在")
        
        if 'updated_at' not in columns:
            print("添加 updated_at 列...")
            cursor.execute("ALTER TABLE evaluations ADD COLUMN updated_at DATETIME")
            print("[OK] updated_at 列已添加")
        else:
            print("updated_at 列已存在")
        
        conn.commit()
        print("[OK] 数据库迁移完成")
        
    except Exception as e:
        print(f"[ERROR] 迁移失败: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_evaluations_table()


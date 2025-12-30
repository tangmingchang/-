"""
检查并修复数据库结构
"""
import sqlite3
from pathlib import Path

def check_and_fix():
    script_dir = Path(__file__).parent
    db_path = script_dir / "film_education.db"
    
    if not db_path.exists():
        print("数据库文件不存在")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluations'")
        if not cursor.fetchone():
            print("evaluations表不存在")
            conn.close()
            return
        
        # 获取所有列
        cursor.execute("PRAGMA table_info(evaluations)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        print("当前evaluations表的列:")
        for col_name, col_type in columns.items():
            print(f"  - {col_name}: {col_type}")
        
        # 添加缺失的列
        if 'teacher_feedback_box' not in columns:
            print("\n添加 teacher_feedback_box 列...")
            cursor.execute("ALTER TABLE evaluations ADD COLUMN teacher_feedback_box TEXT")
            print("teacher_feedback_box 列已添加")
        else:
            print("\nteacher_feedback_box 列已存在")
        
        if 'detailed_analysis' not in columns:
            print("添加 detailed_analysis 列...")
            cursor.execute("ALTER TABLE evaluations ADD COLUMN detailed_analysis TEXT")
            print("detailed_analysis 列已添加")
        else:
            print("detailed_analysis 列已存在")
        
        if 'updated_at' not in columns:
            print("添加 updated_at 列...")
            cursor.execute("ALTER TABLE evaluations ADD COLUMN updated_at DATETIME")
            print("updated_at 列已添加")
        else:
            print("updated_at 列已存在")
        
        conn.commit()
        print("\n数据库修复完成!")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    check_and_fix()


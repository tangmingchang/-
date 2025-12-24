"""
将student1添加到teacher1的班级，并关联项目
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.models.project import Project

def main():
    db = SessionLocal()
    try:
        # 查找teacher1
        teacher = db.query(User).filter(User.username == "teacher1").first()
        if not teacher:
            print("错误：找不到teacher1用户")
            return
        
        # 查找student1
        student = db.query(User).filter(User.username == "student1").first()
        if not student:
            print("错误：找不到student1用户")
            return
        
        # 查找teacher1的课程（取第一个）
        course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
        if not course:
            print(f"错误：teacher1没有课程，正在创建课程...")
            course = Course(
                name="影视制作基础课程",
                description="影视制作基础课程",
                teacher_id=teacher.id
            )
            db.add(course)
            db.commit()
            db.refresh(course)
            print(f"已创建课程: {course.name} (ID: {course.id})")
        
        # 检查student1是否已经加入课程
        enrollment = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.student_id == student.id
        ).first()
        
        if enrollment:
            print(f"student1已经加入课程 {course.name}")
        else:
            # 添加student1到课程
            enrollment = CourseEnrollment(
                course_id=course.id,
                student_id=student.id
            )
            db.add(enrollment)
            db.commit()
            print(f"已将student1添加到课程 {course.name}")
        
        # 查找student1的项目"AIcp视频项目"
        project = db.query(Project).filter(
            Project.owner_id == student.id,
            Project.name.like("%AIcp%")
        ).first()
        
        if not project:
            # 尝试查找包含"视频"的项目
            project = db.query(Project).filter(
                Project.owner_id == student.id,
                Project.name.like("%视频%")
            ).first()
        
        if project:
            # 将项目关联到课程
            if project.course_id != course.id:
                project.course_id = course.id
                db.commit()
                print(f"已将项目 '{project.name}' 关联到课程 {course.name}")
            else:
                print(f"项目 '{project.name}' 已经关联到课程 {course.name}")
        else:
            print("警告：找不到student1的'AIcp视频项目'，请检查项目名称")
            # 列出student1的所有项目
            all_projects = db.query(Project).filter(Project.owner_id == student.id).all()
            if all_projects:
                print("student1的项目列表：")
                for p in all_projects:
                    print(f"  - {p.name} (ID: {p.id})")
        
        print("\n操作完成！")
        
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()


# 数据模型
from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment, Chapter, CourseResource, ChapterResource
from app.models.project import Project, ProjectStatus, ProjectVersion, Script, Storyboard, MediaAsset
from app.models.evaluation import Evaluation, EvaluationType
from app.models.video_generation import VideoGenerationJob, VideoGenerationStatus

__all__ = [
    "User",
    "UserRole",
    "Course",
    "CourseEnrollment",
    "Chapter",
    "CourseResource",
    "ChapterResource",
    "Project",
    "ProjectStatus",
    "ProjectVersion",
    "Script",
    "Storyboard",
    "MediaAsset",
    "Evaluation",
    "EvaluationType",
    "VideoGenerationJob",
    "VideoGenerationStatus",
]


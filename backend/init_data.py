"""
初始化测试数据脚本
"""
from app.core.database import SessionLocal, engine, Base
from app.models import *
from app.core.security import get_password_hash
from app.models.user import UserRole

def init_test_data():
    """初始化测试数据"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 创建测试教师
        teacher = db.query(User).filter(User.username == "teacher1").first()
        if not teacher:
            teacher = User(
                username="teacher1",
                email="teacher1@example.com",
                hashed_password=get_password_hash("123456"),
                full_name="张老师",
                role=UserRole.TEACHER,
                institution="影视学院"
            )
            db.add(teacher)
            db.commit()
            db.refresh(teacher)
            print(f"✓ 创建教师: {teacher.username}")
        else:
            print(f"✓ 教师已存在: {teacher.username}")
        
        # 创建测试学生
        student = db.query(User).filter(User.username == "student1").first()
        if not student:
            student = User(
                username="student1",
                email="student1@example.com",
                hashed_password=get_password_hash("123456"),
                full_name="李同学",
                role=UserRole.STUDENT,
                institution="影视学院"
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            print(f"✓ 创建学生: {student.username}")
        else:
            print(f"✓ 学生已存在: {student.username}")
        
        # 创建测试课程
        course = db.query(Course).filter(Course.name == "影视制作基础").first()
        if not course:
            course = Course(
                name="影视制作基础",
                description="本课程介绍影视制作的基本流程，包括剧本创作、分镜设计、拍摄技巧和后期制作等内容。",
                teacher_id=teacher.id
            )
            db.add(course)
            db.commit()
            db.refresh(course)
            print(f"✓ 创建课程: {course.name}")
            
            # 创建课程章节
            chapters_data = [
                {
                    "title": "第一章：影视制作概述",
                    "content": """影视制作是一门综合性的艺术与技术相结合的创作活动。本章将深入探讨影视制作的核心概念、历史发展脉络以及完整的制作流程。

首先，我们需要理解影视制作的基本概念。影视制作不仅仅是简单的拍摄和剪辑，它涉及创意构思、剧本创作、前期筹备、实际拍摄、后期制作以及发行推广等多个环节。每一个环节都需要专业的知识和技能，同时也需要团队协作和项目管理能力。

从历史发展的角度来看，影视制作经历了从无声电影到有声电影，从黑白到彩色，从胶片到数字化的巨大变革。每一次技术革新都带来了创作方式的改变，也推动了影视艺术的不断发展。了解这些历史背景，有助于我们更好地理解当前影视制作的技术和艺术特点。

在制作流程方面，影视制作通常分为三个阶段：前期制作、制作期和后期制作。前期制作包括剧本开发、资金筹措、团队组建、场景选择、设备准备等；制作期是实际拍摄阶段，需要协调演员、摄影师、灯光师、录音师等各个部门；后期制作则包括剪辑、特效、调色、声音设计、配乐等环节。

本章还将介绍影视制作中的关键角色和职责，包括导演、制片人、摄影师、剪辑师等，以及他们如何协作完成一部作品。同时，我们也会探讨不同类型的影视作品（如电影、电视剧、纪录片、广告等）在制作上的差异和特点。""",
                    "order": 1
                },
                {
                    "title": "第二章：剧本创作",
                    "content": """剧本是影视作品的基石，一个好的剧本是成功作品的前提。本章将系统学习剧本创作的理论与实践技巧。

剧本创作首先需要掌握故事结构。经典的三幕结构（开端、发展、高潮、结局）是大多数影视作品的基础框架。第一幕建立人物和情境，第二幕展开冲突和挑战，第三幕解决冲突并给出结局。理解这个结构有助于我们构建引人入胜的故事。

人物塑造是剧本创作的核心。一个成功的人物需要有清晰的目标、强烈的动机、独特的性格特征，以及成长弧线。人物的对话应该符合其身份和性格，推动剧情发展，同时展现人物关系。我们还将学习如何通过动作、对话、环境等元素来塑造立体的人物形象。

对白写作是剧本创作的重要技能。好的对白应该简洁有力，符合人物性格，推动剧情发展，同时具有潜台词。我们还将学习如何避免说教式的对白，如何通过对话展现人物关系和冲突。

此外，本章还将介绍剧本格式规范、场景描述技巧、视觉叙事方法等内容。我们也会分析经典剧本案例，学习大师们的创作技巧和叙事手法。""",
                    "order": 2
                },
                {
                    "title": "第三章：分镜设计",
                    "content": """分镜设计是将文字剧本转化为视觉画面的关键环节，是导演与摄影师、剪辑师沟通的重要工具。本章将深入学习分镜头的设计原理和实践方法。

分镜头的设计需要考虑多个因素：景别（远景、全景、中景、近景、特写）、角度（平视、仰视、俯视）、运动（推、拉、摇、移、跟）、构图（对称、三分法、引导线等）。每一种选择都会影响观众的视觉感受和情感体验。

用画面讲故事是分镜设计的核心目标。我们需要思考如何通过镜头语言来传达信息、表达情感、推进剧情。例如，特写可以强调细节和情感，远景可以展现环境和氛围，运动镜头可以创造节奏和张力。

本章还将学习故事板（Storyboard）的绘制技巧，包括如何用简单的草图表达复杂的镜头设计，如何标注镜头运动、时长、对白等信息。我们也会学习如何使用数字工具来制作专业的故事板。

此外，我们还将探讨不同类型场景的分镜设计方法，如对话场景、动作场景、情感场景等，以及如何通过分镜设计来控制影片的节奏和氛围。""",
                    "order": 3
                },
                {
                    "title": "第四章：拍摄技巧",
                    "content": """拍摄是影视制作的核心环节，需要掌握摄影构图、镜头运动、光线运用等多种技巧。本章将系统学习这些拍摄技能。

摄影构图是拍摄的基础。我们需要掌握黄金分割、三分法、对称构图、引导线构图等基本构图方法，以及如何运用前景、中景、背景来创造画面层次。构图不仅要美观，更要服务于叙事和情感表达。

镜头运动是创造视觉节奏和情感张力的重要手段。推镜头可以引导观众注意力，拉镜头可以展现环境，摇镜头可以跟随动作，移镜头可以创造流畅的视觉体验。我们需要学习如何选择合适的镜头运动来配合剧情发展。

光线运用是营造氛围和塑造人物的重要手段。自然光和人工光各有特点，硬光和软光会产生不同的视觉效果。我们需要学习如何利用光线的方向、强度、色温来创造不同的氛围，如何用光线来塑造人物形象和表达情感。

此外，本章还将介绍镜头选择（广角、标准、长焦）、景深控制、色彩运用、拍摄设备操作等实用技能。我们也会学习如何应对不同的拍摄环境和挑战，如室内外拍摄、夜景拍摄、运动拍摄等。""",
                    "order": 4
                },
                {
                    "title": "第五章：后期制作",
                    "content": """后期制作是将拍摄素材转化为完整作品的关键阶段，包括剪辑、调色、声音设计、特效制作等多个环节。本章将全面了解后期制作的流程和技巧。

剪辑是后期制作的核心。我们需要学习如何选择镜头、如何组织素材、如何控制节奏、如何创造连贯性。剪辑不仅要保证故事的流畅性，更要通过剪辑技巧来增强戏剧张力和情感表达。我们还将学习各种剪辑技巧，如跳切、匹配剪辑、交叉剪辑、蒙太奇等。

调色是营造视觉风格的重要手段。通过调整色彩、对比度、饱和度等参数，我们可以创造不同的视觉氛围，如温暖的回忆、冷峻的现实、梦幻的想象等。我们还将学习如何使用调色工具来实现这些效果。

声音设计是增强作品感染力的重要环节。我们需要学习如何录制和编辑对白、如何添加音效、如何设计环境音、如何运用音乐来增强情感表达。声音不仅要清晰，更要与画面完美配合，共同营造沉浸式的观影体验。

此外，本章还将介绍特效制作、字幕设计、输出格式等技术内容，以及如何与剪辑师、调色师、声音设计师等专业人员协作完成后期制作。""",
                    "order": 5
                }
            ]
            
            for chapter_data in chapters_data:
                chapter = Chapter(
                    course_id=course.id,
                    **chapter_data
                )
                db.add(chapter)
            
            db.commit()
            print(f"✓ 创建了 {len(chapters_data)} 个章节")
            
            # 让学生加入课程
            enrollment = db.query(CourseEnrollment).filter(
                CourseEnrollment.course_id == course.id,
                CourseEnrollment.student_id == student.id
            ).first()
            if not enrollment:
                enrollment = CourseEnrollment(
                    course_id=course.id,
                    student_id=student.id
                )
                db.add(enrollment)
                db.commit()
                print(f"✓ 学生 {student.username} 已加入课程")
        else:
            print(f"✓ 课程已存在: {course.name}")
        
        # 创建更多丰富的课程
        courses_data = [
            {
                "name": "AI影视编创与制作",
                "description": "探索AI技术在影视创作中的应用，包括AI辅助剧本创作、智能分镜设计、AI视频生成等前沿技术。",
                "chapters": [
                    {
                        "title": "第一章：AI在影视创作中的概述",
                        "content": "了解AI技术在影视行业的应用现状，包括GPT辅助剧本创作、Stable Diffusion生成概念图、Runway Gen-2视频生成等工具介绍。",
                        "order": 1
                    },
                    {
                        "title": "第二章：AI辅助剧本创作",
                        "content": "学习使用GPT-4等大语言模型辅助剧本创作，包括故事构思、人物设定、对话生成等技巧。掌握提示词工程在剧本创作中的应用。",
                        "order": 2
                    },
                    {
                        "title": "第三章：AI图像生成与概念设计",
                        "content": "使用Stable Diffusion、Midjourney等工具生成分镜概念图、场景设计图、角色设计图。学习提示词优化和图像质量控制。",
                        "order": 3
                    },
                    {
                        "title": "第四章：AI视频生成技术",
                        "content": "探索Runway Gen-2、Pika Labs等AI视频生成工具，学习从文本到视频、图像到视频的生成流程。了解视频生成的参数调节和优化技巧。",
                        "order": 4
                    },
                    {
                        "title": "第五章：AI音频处理与配音",
                        "content": "学习使用Whisper进行语音识别和转录，AI语音合成技术，以及AI辅助音效生成。掌握音频与视频的同步处理。",
                        "order": 5
                    },
                    {
                        "title": "第六章：AI影视制作工作流整合",
                        "content": "整合AI工具到完整的影视制作流程中，从前期策划到后期制作的全流程AI辅助方案。学习如何平衡AI工具与传统制作方法。",
                        "order": 6
                    }
                ]
            },
            {
                "name": "数字视频编辑与后期制作",
                "description": "深入学习数字视频编辑技术，包括非线性编辑软件的使用、剪辑技巧、调色、特效制作和输出优化。",
                "chapters": [
                    {
                        "title": "第一章：非线性编辑基础",
                        "content": "介绍Premiere Pro、DaVinci Resolve、Final Cut Pro等主流编辑软件。学习项目设置、素材导入、时间线操作等基础技能。",
                        "order": 1
                    },
                    {
                        "title": "第二章：剪辑理论与技巧",
                        "content": "学习蒙太奇理论、剪辑节奏控制、镜头组接原则。掌握跳切、匹配剪辑、交叉剪辑等经典剪辑技巧。",
                        "order": 2
                    },
                    {
                        "title": "第三章：色彩校正与调色",
                        "content": "学习色彩理论、色轮工具使用、一级调色和二级调色技巧。掌握DaVinci Resolve的调色工作流，创建电影级色彩风格。",
                        "order": 3
                    },
                    {
                        "title": "第四章：视频特效与合成",
                        "content": "学习关键帧动画、遮罩使用、绿幕抠像、运动跟踪等特效技术。了解After Effects与Premiere的协同工作流程。",
                        "order": 4
                    },
                    {
                        "title": "第五章：音频后期处理",
                        "content": "学习音频同步、降噪处理、音量平衡、混音技巧。掌握背景音乐、音效、对白的协调处理。",
                        "order": 5
                    },
                    {
                        "title": "第六章：输出与交付",
                        "content": "学习不同平台的视频编码设置、分辨率选择、码率控制。掌握YouTube、抖音、电影等不同格式的输出规范。",
                        "order": 6
                    }
                ]
            },
            {
                "name": "影视声音设计",
                "description": "学习影视作品中的声音设计，包括对白录制、音效制作、背景音乐选择、混音技术等完整的音频制作流程。",
                "chapters": [
                    {
                        "title": "第一章：声音设计基础理论",
                        "content": "了解声音在影视作品中的作用，学习声音设计的三大要素：对白、音效、音乐。掌握声音与画面的关系。",
                        "order": 1
                    },
                    {
                        "title": "第二章：对白录制技术",
                        "content": "学习专业录音设备的使用、录音环境搭建、麦克风选择与摆放。掌握对白录制的最佳实践和常见问题处理。",
                        "order": 2
                    },
                    {
                        "title": "第三章：音效制作与采集",
                        "content": "学习音效库的使用、现场音效采集、Foley音效制作。掌握音效的编辑、处理和同步技巧。",
                        "order": 3
                    },
                    {
                        "title": "第四章：背景音乐的选择与编辑",
                        "content": "学习如何选择适合的背景音乐，掌握音乐的情绪表达、节奏匹配。学习音乐的剪辑、淡入淡出等处理技巧。",
                        "order": 4
                    },
                    {
                        "title": "第五章：音频混音技术",
                        "content": "学习多轨混音、音量平衡、EQ调节、压缩器使用、混响效果等。掌握专业混音软件的操作。",
                        "order": 5
                    },
                    {
                        "title": "第六章：环绕声与空间音频",
                        "content": "了解5.1、7.1环绕声制作，学习空间音频技术在影视作品中的应用。掌握沉浸式音频体验的创作方法。",
                        "order": 6
                    }
                ]
            },
            {
                "name": "电影摄影与镜头语言",
                "description": "深入学习电影摄影技术，包括构图原理、镜头运动、光线运用、色彩控制等，掌握用镜头讲故事的技巧。",
                "chapters": [
                    {
                        "title": "第一章：电影摄影基础",
                        "content": "了解电影摄影与静态摄影的区别，学习电影摄影机的选择、镜头类型、感光元件特性等基础知识。",
                        "order": 1
                    },
                    {
                        "title": "第二章：构图与画面设计",
                        "content": "学习三分法、黄金分割、对称构图等经典构图原则。掌握景深控制、焦点选择、画面平衡等技巧。",
                        "order": 2
                    },
                    {
                        "title": "第三章：镜头运动与机位",
                        "content": "学习推拉摇移跟等镜头运动方式，掌握不同机位（高角度、低角度、平视）的叙事效果。了解稳定器、滑轨等设备的使用。",
                        "order": 3
                    },
                    {
                        "title": "第四章：光线运用",
                        "content": "学习自然光与人工光的运用，掌握三点布光法、高调与低调风格。了解不同时段光线的特点和拍摄技巧。",
                        "order": 4
                    },
                    {
                        "title": "第五章：色彩与影调",
                        "content": "学习色彩理论在电影中的应用，掌握冷暖色调的运用、色彩情绪表达。了解不同电影风格的色彩特点。",
                        "order": 5
                    },
                    {
                        "title": "第六章：特殊拍摄技巧",
                        "content": "学习慢动作、延时摄影、航拍、水下拍摄等特殊拍摄技术。掌握特殊镜头的使用和创意拍摄方法。",
                        "order": 6
                    }
                ]
            },
            {
                "name": "剧本创作与故事结构",
                "description": "系统学习剧本创作方法，包括故事结构、人物塑造、对白写作、情节设计等，掌握从创意到完整剧本的创作流程。",
                "chapters": [
                    {
                        "title": "第一章：故事基础与创意开发",
                        "content": "学习故事的基本要素：人物、冲突、目标。掌握创意开发方法，学习如何从生活、新闻、文学中寻找创作灵感。",
                        "order": 1
                    },
                    {
                        "title": "第二章：三幕结构与故事弧线",
                        "content": "深入学习三幕结构理论，掌握开端、发展、高潮、结局的设计。学习故事弧线的构建和节奏控制。",
                        "order": 2
                    },
                    {
                        "title": "第三章：人物塑造",
                        "content": "学习如何创造立体的人物角色，包括人物背景、性格特征、动机、成长弧线。掌握人物关系网的构建。",
                        "order": 3
                    },
                    {
                        "title": "第四章：对白写作技巧",
                        "content": "学习对白的功能和特点，掌握如何写出自然、有张力的对话。了解对白与动作、潜台词的关系。",
                        "order": 4
                    },
                    {
                        "title": "第五章：场景设计与描述",
                        "content": "学习场景描述的方法，掌握如何用文字构建画面感。了解场景转换、场景节奏对故事的影响。",
                        "order": 5
                    },
                    {
                        "title": "第六章：剧本格式与修改",
                        "content": "学习标准剧本格式，掌握剧本软件的使用。学习剧本修改技巧，包括结构调整、情节优化、对白润色等。",
                        "order": 6
                    }
                ]
            },
            {
                "name": "影视特效与视觉设计",
                "description": "学习影视特效制作技术，包括CG特效、合成技术、粒子特效、数字绘景等，掌握现代影视视觉效果的创作方法。",
                "chapters": [
                    {
                        "title": "第一章：影视特效概述",
                        "content": "了解影视特效的发展历程和分类，学习实拍特效与数字特效的区别。掌握特效在叙事中的作用。",
                        "order": 1
                    },
                    {
                        "title": "第二章：绿幕拍摄与抠像技术",
                        "content": "学习绿幕拍摄的最佳实践，掌握Keylight、Ultra Key等抠像工具的使用。学习边缘处理和细节优化技巧。",
                        "order": 2
                    },
                    {
                        "title": "第三章：CG建模与渲染",
                        "content": "学习Maya、Blender等3D软件的基础操作，掌握建模、材质、灯光、渲染流程。了解CG角色和场景的制作。",
                        "order": 3
                    },
                    {
                        "title": "第四章：粒子特效与动力学",
                        "content": "学习粒子系统的创建和控制，掌握爆炸、烟雾、火焰、雨雪等自然现象的特效制作。了解刚体和柔体动力学。",
                        "order": 4
                    },
                    {
                        "title": "第五章：数字绘景与Matte Painting",
                        "content": "学习数字绘景技术，掌握如何创建逼真的背景环境。了解透视、光影、细节处理等绘景技巧。",
                        "order": 5
                    },
                    {
                        "title": "第六章：特效合成与整合",
                        "content": "学习Nuke、After Effects等合成软件的使用，掌握多元素合成、色彩匹配、运动跟踪等高级合成技术。",
                        "order": 6
                    }
                ]
            }
        ]
        
        for course_data in courses_data:
            existing = db.query(Course).filter(Course.name == course_data["name"]).first()
            if not existing:
                chapters = course_data.pop("chapters", [])
                new_course = Course(
                    teacher_id=teacher.id,
                    **course_data
                )
                db.add(new_course)
                db.flush()
                db.refresh(new_course)
                print(f"✓ 创建课程: {new_course.name}")
                
                # 创建章节
                for chapter_data in chapters:
                    chapter = Chapter(
                        course_id=new_course.id,
                        **chapter_data
                    )
                    db.add(chapter)
                print(f"  └─ 创建了 {len(chapters)} 个章节")
                
                # 让学生加入课程
                enrollment = db.query(CourseEnrollment).filter(
                    CourseEnrollment.course_id == new_course.id,
                    CourseEnrollment.student_id == student.id
                ).first()
                if not enrollment:
                    enrollment = CourseEnrollment(
                        course_id=new_course.id,
                        student_id=student.id
                    )
                    db.add(enrollment)
        
        # 添加课程资源（电子书、视频等）
        print("\n正在添加课程资源...")
        all_courses = db.query(Course).all()
        
        # 为每个课程添加资源（视频教程、在线课程等）
        resources_data = [
            # 视频教程资源
            {
                "title": "电影艺术：形式与风格 - 视频课程",
                "resource_type": "video",
                "file_path": "https://www.youtube.com/results?search_query=电影艺术+形式与风格+film+art",
                "description": "经典电影理论视频课程，深入解析电影语言和叙事技巧。点击后跳转到YouTube搜索相关视频。"
            },
            {
                "title": "故事结构：编剧原理与实践 - 视频教程",
                "resource_type": "video",
                "file_path": "https://www.youtube.com/results?search_query=Robert+McKee+Story+screenwriting",
                "description": "罗伯特·麦基编剧理论视频教程，学习故事结构、人物塑造和剧本创作技巧。点击后跳转到YouTube搜索相关视频。"
            },
            {
                "title": "电影摄影技术 - 实战教程",
                "resource_type": "video",
                "file_path": "https://www.youtube.com/results?search_query=cinematography+tutorial+film+photography",
                "description": "电影摄影技术视频教程，包含构图、光线、镜头运动等核心知识。点击后跳转到YouTube搜索相关视频。"
            },
            {
                "title": "视频剪辑技巧 - 完整教程",
                "resource_type": "video",
                "file_path": "https://www.youtube.com/results?search_query=video+editing+tutorial+cutting+techniques",
                "description": "视频剪辑理论和实践技巧的完整教程，适合初学者和进阶学习者。点击后跳转到YouTube搜索相关视频。"
            },
            {
                "title": "电影声音设计 - 音频制作教程",
                "resource_type": "video",
                "file_path": "https://www.youtube.com/results?search_query=film+sound+design+audio+production+tutorial",
                "description": "电影声音设计视频教程，学习音频在电影中的作用和创作方法。点击后跳转到YouTube搜索相关视频。"
            },
            {
                "title": "《编剧的艺术》在线阅读",
                "resource_type": "link",
                "file_path": "https://www.gutenberg.org/ebooks/",
                "description": "学习剧本创作的基础理论和实践技巧，古腾堡计划免费资源。"
            },
            # 视频教程资源
            {
                "title": "Adobe Premiere Pro 官方教程",
                "resource_type": "video",
                "file_path": "https://helpx.adobe.com/premiere-pro/tutorials.html",
                "description": "Adobe官方提供的Premiere Pro视频编辑完整教程，从基础到高级。"
            },
            {
                "title": "DaVinci Resolve 调色教程",
                "resource_type": "video",
                "file_path": "https://www.blackmagicdesign.com/products/davinciresolve/training",
                "description": "Blackmagic官方免费调色教程，适合初学者，包含实战案例。"
            },
            {
                "title": "Blender 3D建模与动画教程",
                "resource_type": "video",
                "file_path": "https://www.blender.org/support/tutorials/",
                "description": "Blender官方免费3D建模和动画教程，适合影视特效制作。"
            },
            {
                "title": "After Effects 特效制作教程",
                "resource_type": "video",
                "file_path": "https://helpx.adobe.com/after-effects/tutorials.html",
                "description": "Adobe官方After Effects教程，学习视频特效和合成技术。"
            },
            {
                "title": "YouTube影视制作频道 - Film Riot",
                "resource_type": "link",
                "file_path": "https://www.youtube.com/c/FilmRiot",
                "description": "优质影视制作教学频道，包含拍摄技巧、后期制作等实用教程。"
            },
            {
                "title": "YouTube影视制作频道 - DSLR Guide",
                "resource_type": "link",
                "file_path": "https://www.youtube.com/c/DSLRguide",
                "description": "专业的电影摄影和制作技巧分享，适合独立电影制作人。"
            },
            # 在线课程平台
            {
                "title": "Coursera 影视制作课程",
                "resource_type": "link",
                "file_path": "https://www.coursera.org/courses?query=film+production",
                "description": "Coursera平台上的免费影视制作在线课程，由知名大学提供。"
            },
            {
                "title": "edX 电影制作课程",
                "resource_type": "link",
                "file_path": "https://www.edx.org/search?q=film+production",
                "description": "edX平台提供的免费电影制作课程，包含MIT、哈佛等名校课程。"
            },
            {
                "title": "Khan Academy 电影与叙事课程",
                "resource_type": "link",
                "file_path": "https://www.khanacademy.org/humanities/hass-storytelling",
                "description": "可汗学院提供的免费电影和叙事课程，适合初学者。"
            },
            {
                "title": "MasterClass 电影制作大师课",
                "resource_type": "link",
                "file_path": "https://www.masterclass.com/classes",
                "description": "由知名导演和制片人讲授的电影制作课程（部分免费内容）。"
            },
            # 实用工具和资源
            {
                "title": "Pexels 免费视频素材库",
                "resource_type": "link",
                "file_path": "https://www.pexels.com/videos/",
                "description": "高质量免费视频素材库，可用于学习和练习剪辑。"
            },
            {
                "title": "Freesound 免费音效库",
                "resource_type": "link",
                "file_path": "https://freesound.org/",
                "description": "海量免费音效资源，适合声音设计和音频制作。"
            },
            {
                "title": "Unsplash 免费图片素材",
                "resource_type": "link",
                "file_path": "https://unsplash.com/",
                "description": "高质量免费图片素材，可用于分镜设计和概念图制作。"
            },
            {
                "title": "OpenShot 免费视频编辑软件",
                "resource_type": "link",
                "file_path": "https://www.openshot.org/",
                "description": "开源免费的视频编辑软件，适合初学者学习剪辑基础。"
            },
            {
                "title": "Audacity 音频编辑软件",
                "resource_type": "link",
                "file_path": "https://www.audacityteam.org/",
                "description": "免费开源的音频编辑软件，适合声音设计和音频处理学习。"
            }
        ]
        
        # 为每个课程分配资源
        for i, course in enumerate(all_courses):
            # 每个课程分配2-3个资源
            start_idx = (i * 2) % len(resources_data)
            course_resources = resources_data[start_idx:start_idx+2] + [resources_data[(start_idx+len(all_courses)) % len(resources_data)]]
            
            for res_data in course_resources:
                existing = db.query(CourseResource).filter(
                    CourseResource.course_id == course.id,
                    CourseResource.title == res_data["title"]
                ).first()
                if not existing:
                    resource = CourseResource(
                        course_id=course.id,
                        **res_data
                    )
                    db.add(resource)
            print(f"  ✓ 为课程 '{course.name}' 添加了 {len(course_resources)} 个资源")
        
        db.commit()
        print("\n✓ 测试数据初始化完成！")
        print("\n测试账号:")
        print("  教师: teacher1 / 123456")
        print("  学生: student1 / 123456")
        print(f"\n已创建:")
        print(f"  - {len(all_courses)} 门课程")
        print(f"  - 多个章节和资源")
        
    except Exception as e:
        db.rollback()
        print(f"✗ 初始化失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("开始初始化测试数据...")
    init_test_data()


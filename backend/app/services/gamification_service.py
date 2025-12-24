"""
游戏化组件服务
镜头语法小游戏、灵感骰子等
"""
import random
from typing import Dict, List, Optional, Any
import json

class GamificationService:
    """游戏化服务"""
    
    def __init__(self):
        self.shot_classifier_available = False
        self._init_models()
        self._init_game_data()
    
    def _init_models(self):
        """初始化模型"""
        # 镜头类型分类模型
        try:
            # from shot_type_classifier import ShotTypeClassifier
            # self.shot_classifier = ShotTypeClassifier()
            # self.shot_classifier_available = True
            pass
        except ImportError:
            print("警告: 镜头分类模型未安装，将使用基础分类")
    
    def _init_game_data(self):
        """初始化游戏数据"""
        # 灵感骰子词库
        self.inspiration_characters = [
            "失意的艺术家", "神秘的陌生人", "年轻的创业者", "退休的侦探",
            "叛逆的学生", "孤独的老人", "寻找真相的记者", "迷失方向的旅人"
        ]
        
        self.inspiration_scenarios = [
            "雨夜的咖啡厅", "废弃的工厂", "繁华的都市街头", "宁静的海边",
            "古老的图书馆", "深夜的地铁站", "山顶的观景台", "昏暗的地下室"
        ]
        
        self.inspiration_conflicts = [
            "过去的秘密被揭露", "梦想与现实的对立", "信任的背叛",
            "时间的紧迫性", "道德的抉择", "身份的迷失", "爱情的考验"
        ]
        
        # 镜头类型说明
        self.shot_type_descriptions = {
            "极远景": "展示广阔的环境，人物很小，强调环境氛围",
            "远景": "展示完整场景，人物可见但较小，建立空间关系",
            "全景": "展示人物全身，包含周围环境，建立人物与环境关系",
            "中景": "展示人物腰部以上，关注人物动作和表情",
            "中近景": "展示人物胸部以上，更关注表情和对话",
            "特写": "展示人物面部或物体细节，强调情感或重要性",
            "极特写": "展示极小的细节，如眼睛、手部动作，营造紧张感"
        }
    
    def generate_shot_quiz(self) -> Dict[str, Any]:
        """
        生成镜头语法小游戏题目
        返回一张随机镜头图片和正确答案
        """
        # 镜头类型列表
        shot_types = list(self.shot_type_descriptions.keys())
        
        # 随机选择一个镜头类型作为答案
        correct_answer = random.choice(shot_types)
        
        # 生成干扰选项（包含正确答案）
        options = [correct_answer]
        while len(options) < 4:
            option = random.choice(shot_types)
            if option not in options:
                options.append(option)
        random.shuffle(options)
        
        # 这里应该从素材库选择或生成对应类型的图片
        # 目前返回占位信息
        quiz = {
            "quiz_id": f"quiz_{random.randint(1000, 9999)}",
            "image_url": f"/media/images/shot_examples/{correct_answer.lower()}.jpg",  # 占位
            "question": "请判断这张图片的镜头类型：",
            "options": options,
            "correct_answer": correct_answer,
            "description": self.shot_type_descriptions.get(correct_answer, ""),
            "hint": f"这种镜头通常用于{self.shot_type_descriptions.get(correct_answer, '')[:20]}..."
        }
        
        return quiz
    
    def check_shot_quiz_answer(self, quiz_id: str, user_answer: str) -> Dict[str, Any]:
        """
        检查镜头语法小游戏答案
        """
        # 这里应该从数据库或缓存中获取quiz信息
        # 简化实现：假设quiz_id包含正确答案信息
        
        # 实际应该查询存储的quiz数据
        # quiz = self.get_quiz_by_id(quiz_id)
        # correct = quiz["correct_answer"] == user_answer
        
        # 模拟实现
        correct = True  # 占位
        
        result = {
            "correct": correct,
            "user_answer": user_answer,
            "feedback": "回答正确！" if correct else "回答错误，再想想看。",
            "explanation": self.shot_type_descriptions.get(user_answer, "")
        }
        
        return result
    
    def roll_inspiration_dice(self, use_llm: bool = False) -> Dict[str, Any]:
        """
        掷灵感骰子
        随机生成创意点子
        """
        if use_llm:
            # 使用LLM生成更丰富的创意
            # prompt = f"给我一个随机的电影创意点子，包括角色、场景和冲突"
            # result = llm.generate(prompt)
            # return {"inspiration": result, "source": "llm"}
            pass
        
        # 随机组合词库
        character = random.choice(self.inspiration_characters)
        scenario = random.choice(self.inspiration_scenarios)
        conflict = random.choice(self.inspiration_conflicts)
        
        inspiration = {
            "id": f"insp_{random.randint(1000, 9999)}",
            "character": character,
            "scenario": scenario,
            "conflict": conflict,
            "description": f"{character}在{scenario}中，面临{conflict}的挑战。",
            "source": "词库随机"
        }
        
        return inspiration
    
    def generate_story_seed(self, elements: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        生成故事种子
        可以指定部分元素，其他随机生成
        """
        character = elements.get("character") if elements else None
        scenario = elements.get("scenario") if elements else None
        conflict = elements.get("conflict") if elements else None
        
        if not character:
            character = random.choice(self.inspiration_characters)
        if not scenario:
            scenario = random.choice(self.inspiration_scenarios)
        if not conflict:
            conflict = random.choice(self.inspiration_conflicts)
        
        return {
            "character": character,
            "scenario": scenario,
            "conflict": conflict,
            "story_seed": f"{character}在{scenario}中，面临{conflict}。这将如何展开？"
        }
    
    def get_shot_type_info(self, shot_type: str) -> Dict[str, Any]:
        """
        获取镜头类型详细信息
        """
        return {
            "type": shot_type,
            "description": self.shot_type_descriptions.get(shot_type, "未知类型"),
            "usage": f"常用于{self._get_shot_usage(shot_type)}",
            "examples": self._get_shot_examples(shot_type)
        }
    
    def _get_shot_usage(self, shot_type: str) -> str:
        """获取镜头使用场景"""
        usage_map = {
            "极远景": "开场建立环境、展示宏大场面",
            "远景": "建立空间关系、展示环境",
            "全景": "展示人物与环境关系、动作场景",
            "中景": "对话场景、人物互动",
            "中近景": "强调表情、重要对话",
            "特写": "情感表达、细节强调",
            "极特写": "紧张时刻、细节特写"
        }
        return usage_map.get(shot_type, "通用场景")
    
    def _get_shot_examples(self, shot_type: str) -> List[str]:
        """获取镜头示例"""
        examples_map = {
            "极远景": ["《2001太空漫游》开场", "《指环王》中土世界全景"],
            "远景": ["《教父》开场", "《肖申克的救赎》监狱场景"],
            "全景": ["动作片打斗场景", "舞蹈场景"],
            "中景": ["对话场景", "会议场景"],
            "中近景": ["重要对话", "情感表达"],
            "特写": ["角色表情", "关键物品"],
            "极特写": ["眼神特写", "手部动作"]
        }
        return examples_map.get(shot_type, [])

# 单例模式
gamification_service = GamificationService()


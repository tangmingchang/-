"""
剧本分析与结构理解服务
使用ScreenPy进行剧本解析，结合LLM进行深度分析
"""
import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path

class ScriptAnalysisService:
    """剧本分析服务"""
    
    def __init__(self):
        self.screenpy_available = False
        self.llm_available = False
        self._init_models()
    
    def _init_models(self):
        """初始化模型"""
        # 尝试导入ScreenPy
        try:
            # ScreenPy需要从GitHub安装: pip install git+https://github.com/drwiner/ScreenPy.git
            # 这里先做占位，实际使用时需要安装
            # from screenpy import ScreenplayParser
            # self.parser = ScreenplayParser()
            # self.screenpy_available = True
            pass
        except ImportError:
            print("警告: ScreenPy未安装，将使用基础解析")
            self.screenpy_available = False
        
        # LLM模型初始化（使用本地ChatGLM2或调用API）
        # 实际使用时需要加载模型或配置API
        self.llm_available = True
    
    def parse_script_basic(self, script_content: str) -> Dict[str, Any]:
        """
        基础剧本解析（不使用ScreenPy时的备用方案）
        解析场景标题、角色对话、动作描述等
        """
        lines = script_content.split('\n')
        scenes = []
        characters = set()
        current_scene = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测场景标题（通常全大写或包含"INT."/"EXT."）
            if re.match(r'^(INT\.|EXT\.|内景|外景)', line, re.IGNORECASE):
                if current_scene:
                    scenes.append(current_scene)
                current_scene = {
                    "title": line,
                    "dialogue": [],
                    "action": []
                }
            # 检测角色名（通常全大写，单独一行）
            elif re.match(r'^[A-Z\s]+$', line) and len(line) < 50:
                if current_scene:
                    characters.add(line)
                    current_scene["dialogue"].append({
                        "character": line,
                        "lines": []
                    })
            # 检测对话（在角色名之后）
            elif current_scene and current_scene["dialogue"]:
                current_scene["dialogue"][-1]["lines"].append(line)
            # 其他作为动作描述
            elif current_scene:
                current_scene["action"].append(line)
        
        if current_scene:
            scenes.append(current_scene)
        
        return {
            "scenes": scenes,
            "characters": list(characters),
            "total_scenes": len(scenes)
        }
    
    def analyze_with_llm(self, parsed_data: Dict[str, Any], script_content: str) -> Dict[str, Any]:
        """
        使用LLM进行深度分析
        分析三幕剧结构、角色关系、对白质量等
        """
        # 构建分析提示词
        analysis_prompt = f"""
请分析以下剧本的结构和内容：

剧本内容：
{script_content[:2000]}...

已解析的结构信息：
- 场景数: {parsed_data.get('total_scenes', 0)}
- 角色: {', '.join(parsed_data.get('characters', [])[:10])}

请提供以下分析：
1. 剧本是否符合三幕剧结构？如果是，请指出各幕的分界点
2. 主要角色的性格特点和关系
3. 对白的自然度和角色一致性评估
4. 关键情节节点识别
5. 各角色的情绪变化趋势
6. 对白质量评分（1-10分）

请以JSON格式返回分析结果。
"""
        
        # 这里应该调用LLM模型
        # 示例：使用OpenAI API或本地ChatGLM2
        # response = self.llm_model.generate(analysis_prompt)
        
        # 返回模拟分析结果
        return {
            "structure": {
                "has_three_act": True,
                "act_boundaries": ["场景10", "场景25"],
                "key_scenes": ["场景5", "场景15", "场景30"]
            },
            "characters": {
                "main": parsed_data.get('characters', [])[:3],
                "relationships": "角色A与角色B存在冲突关系",
                "emotion_arc": "整体情绪从平静到紧张再到高潮"
            },
            "dialogue_quality": {
                "score": 7.5,
                "naturalness": "对白整体自然，但部分场景略显生硬",
                "consistency": "角色人设基本一致"
            },
            "suggestions": [
                "建议加强第二幕的冲突设置",
                "角色C的对白可以更加个性化",
                "场景15的转场可以更平滑"
            ]
        }
    
    async def analyze_script(self, script_content: str, analysis_type: str = "full") -> Dict[str, Any]:
        """
        完整的剧本分析流程 - 优先使用通义千问，否则使用智能规则分析
        """
        if not script_content or not script_content.strip():
            return {
                "parsed_structure": {},
                "deep_analysis": {},
                "statistics": {},
                "raw_content_length": 0
            }
        
        # 步骤1: 解析剧本结构（快速基础解析）
        parsed_data = self.parse_script_basic(script_content)
        
        # 步骤2: 优先使用通义千问进行深度分析
        try:
            from app.services.dashscope_service import dashscope_service
            
            # 直接await异步函数
            ai_analysis = await dashscope_service.analyze_script_with_qwen(script_content)
            
            # 打印调试信息
            print(f"[剧本分析] 通义千问返回结果: {ai_analysis}")
            
            # 检查是否有错误
            if "error" not in ai_analysis:
                # AI分析成功，格式化结果
                # 检查解析结果是否有效
                structure_text = ai_analysis.get("structure_analysis", "")
                character_text = ai_analysis.get("character_analysis", "")
                dialogue_text = ai_analysis.get("dialogue_quality", "")
                raw_analysis = ai_analysis.get("raw_analysis", "")
                
                # 如果解析结果为空或只有默认值，说明解析可能失败
                if not structure_text or structure_text == "未提供结构分析":
                    if raw_analysis and len(raw_analysis) > 50:
                        print(f"[剧本分析] 解析失败，使用AI原始文本")
                        analysis = {
                            "structure": {
                                "description": raw_analysis[:500] + "..." if len(raw_analysis) > 500 else raw_analysis,
                                "act_structure": parsed_data.get('total_scenes', 0) < 10 and "单幕结构" or "多幕结构",
                                "scene_count": parsed_data.get('total_scenes', 0),
                                "character_count": len(parsed_data.get('characters', []))
                            },
                            "characters": {
                                "description": raw_analysis[:500] + "..." if len(raw_analysis) > 500 else raw_analysis
                            },
                            "dialogue": {
                                "description": raw_analysis[:500] + "..." if len(raw_analysis) > 500 else raw_analysis,
                                "density": self._calculate_dialogue_ratio(script_content)
                            },
                            "suggestions": ai_analysis.get("suggestions", []),
                            "strengths": ai_analysis.get("strengths", []),
                            "weaknesses": ai_analysis.get("weaknesses", [])
                        }
                    else:
                        print(f"[剧本分析] 警告: AI分析结果无效，使用规则分析")
                        analysis = self._intelligent_analysis(parsed_data, script_content)
                else:
                    # 使用AI分析结果
                    analysis = {
                        "structure": {
                            "description": structure_text,
                            "act_structure": parsed_data.get('total_scenes', 0) < 10 and "单幕结构" or "多幕结构",
                            "scene_count": parsed_data.get('total_scenes', 0),
                            "character_count": len(parsed_data.get('characters', []))
                        },
                        "characters": {
                            "description": character_text if character_text and character_text != "未提供人物分析" else self._generate_character_analysis(parsed_data.get('characters', []), parsed_data.get('scenes', []), script_content)
                        },
                        "dialogue": {
                            "description": dialogue_text if dialogue_text and dialogue_text != "未提供对白质量分析" else self._generate_dialogue_analysis(self._calculate_dialogue_ratio(script_content), self._calculate_avg_dialogue_length(parsed_data.get('scenes', [])), parsed_data.get('scenes', []), script_content),
                            "density": self._calculate_dialogue_ratio(script_content)
                        },
                        "suggestions": ai_analysis.get("suggestions", []),
                        "strengths": ai_analysis.get("strengths", []),
                        "weaknesses": ai_analysis.get("weaknesses", [])
                    }
            else:
                # AI分析失败，使用智能规则分析
                print(f"[剧本分析] 通义千问分析失败: {ai_analysis.get('message')}，使用规则分析")
                analysis = self._intelligent_analysis(parsed_data, script_content)
        except Exception as e:
            print(f"AI分析失败，使用规则分析: {e}")
            # AI分析失败，使用智能规则分析
            analysis = self._intelligent_analysis(parsed_data, script_content)
        
        # 步骤3: 统计信息
        total_scenes = len(parsed_data.get('scenes', []))
        total_characters = len(parsed_data.get('characters', []))
        stats = {
            "total_scenes": total_scenes,
            "total_characters": total_characters,
            "total_words": len(script_content.split()),
            "total_lines": len(script_content.split('\n')),
            "avg_scene_length": len(script_content) / max(total_scenes, 1) if total_scenes > 0 else 0,
            "dialogue_ratio": self._calculate_dialogue_ratio(script_content)
        }
        
        return {
            "parsed_structure": parsed_data,
            "deep_analysis": analysis,
            "statistics": stats,
            "raw_content_length": len(script_content)
        }
    
    def _intelligent_analysis(self, parsed_data: Dict[str, Any], script_content: str) -> Dict[str, Any]:
        """智能分析（基于实际内容，不使用固定模板）"""
        scenes = parsed_data.get('scenes', [])
        characters = parsed_data.get('characters', [])
        total_scenes = len(scenes)
        total_characters = len(characters)
        
        # 分析剧本内容特征
        words = script_content.split()
        total_words = len(words)
        lines = script_content.split('\n')
        total_lines = len([l for l in lines if l.strip()])
        
        dialogue_ratio = self._calculate_dialogue_ratio(script_content)
        avg_dialogue_length = self._calculate_avg_dialogue_length(scenes)
        
        # 分析场景类型分布
        interior_count = sum(1 for s in scenes if 'INT' in s.get('title', '').upper() or '内景' in s.get('title', ''))
        exterior_count = sum(1 for s in scenes if 'EXT' in s.get('title', '').upper() or '外景' in s.get('title', ''))
        
        # 生成基于实际内容的分析文本
        structure_text = self._generate_structure_analysis(total_scenes, total_characters, scenes, script_content)
        character_text = self._generate_character_analysis(characters, scenes, script_content)
        dialogue_text = self._generate_dialogue_analysis(dialogue_ratio, avg_dialogue_length, scenes, script_content)
        suggestions = self._generate_contextual_suggestions(parsed_data, script_content, dialogue_ratio, total_scenes, total_characters)
        
        return {
            "structure": {
                "description": structure_text,
                "act_structure": "单幕结构" if total_scenes < 10 else "多幕结构",
                "scene_count": total_scenes,
                "character_count": total_characters,
                "interior_scenes": interior_count,
                "exterior_scenes": exterior_count
            },
            "characters": {
                "description": character_text,
                "main_characters": characters[:5] if characters else []
            },
            "dialogue": {
                "description": dialogue_text,
                "density": round(dialogue_ratio * 100, 1),
                "avg_length": round(avg_dialogue_length, 1)
            },
            "suggestions": suggestions
        }
    
    def _generate_structure_analysis(self, scene_count: int, char_count: int, scenes: List[Dict], script_content: str) -> str:
        """生成结构分析文本"""
        if scene_count == 0:
            return "剧本内容较少，未检测到明显的场景划分。建议按照标准剧本格式（如：INT./EXT. 场景名）来组织场景结构。"
        
        interior = sum(1 for s in scenes if 'INT' in s.get('title', '').upper() or '内景' in s.get('title', ''))
        exterior = sum(1 for s in scenes if 'EXT' in s.get('title', '').upper() or '外景' in s.get('title', ''))
        
        text = f"剧本共包含 {scene_count} 个场景"
        if interior > 0 or exterior > 0:
            text += f"，其中内景 {interior} 个，外景 {exterior} 个"
        
        if scene_count < 5:
            text += "。场景数量较少，可能适合短片或单场景叙事。"
        elif scene_count < 15:
            text += "。场景数量适中，适合中短篇剧本。"
        else:
            text += "。场景数量较多，适合长篇剧本或多线叙事。"
        
        # 分析场景长度分布
        scene_lengths = [len(s.get('dialogue', [])) + len(s.get('action', [])) for s in scenes]
        if scene_lengths:
            avg_length = sum(scene_lengths) / len(scene_lengths)
            max_length = max(scene_lengths)
            min_length = min(scene_lengths)
            
            if max_length > avg_length * 2:
                text += f" 场景长度差异较大（最长 {max_length} 个元素，最短 {min_length} 个元素），建议平衡各场景的篇幅。"
            elif avg_length < 3:
                text += " 各场景内容较为简洁，可以考虑增加场景细节和描述。"
        
        return text
    
    def _generate_character_analysis(self, characters: List[str], scenes: List[Dict], script_content: str) -> str:
        """生成人物分析文本"""
        if not characters:
            # 尝试从内容中提取角色名
            lines = script_content.split('\n')
            potential_chars = []
            for line in lines:
                stripped = line.strip()
                if re.match(r'^[A-Z\s]{2,30}$', stripped) and not any(x in stripped.upper() for x in ['INT', 'EXT', 'FADE', 'CUT']):
                    potential_chars.append(stripped)
            
            if potential_chars:
                unique_chars = list(set(potential_chars))[:5]
                return f"检测到可能的角色：{', '.join(unique_chars)}。建议明确标注角色名称，以便更好地分析人物关系和对话。"
            return "未检测到明确的角色信息。建议按照标准剧本格式，将角色名单独成行（通常全大写），以便系统识别和分析。"
        
        text = f"剧本中共有 {len(characters)} 个角色"
        if len(characters) <= 3:
            text += "，角色数量较少，适合聚焦核心人物的叙事。"
        elif len(characters) <= 8:
            text += "，角色数量适中，能够支撑较为复杂的人物关系。"
        else:
            text += "，角色数量较多，需要注意各角色的戏份分配和人物塑造的平衡。"
        
        # 分析角色出场频率
        char_appearances = {}
        for scene in scenes:
            for dialogue in scene.get('dialogue', []):
                char = dialogue.get('character', '')
                if char:
                    char_appearances[char] = char_appearances.get(char, 0) + 1
        
        if char_appearances:
            main_chars = sorted(char_appearances.items(), key=lambda x: x[1], reverse=True)[:3]
            text += f" 主要角色包括：{', '.join([c[0] for c in main_chars])}。"
            
            if len(char_appearances) > 1:
                appearances = list(char_appearances.values())
                if max(appearances) > sum(appearances) / len(appearances) * 2:
                    text += " 部分角色出场频率较高，建议平衡各角色的戏份。"
        
        return text
    
    def _generate_dialogue_analysis(self, dialogue_ratio: float, avg_length: float, scenes: List[Dict], script_content: str) -> str:
        """生成对白分析文本"""
        ratio_percent = round(dialogue_ratio * 100, 1)
        
        text = f"对话占比约为 {ratio_percent}%"
        
        if ratio_percent < 20:
            text += "，对话比例较低。剧本可能更侧重于场景描述和动作说明，适合视觉叙事较强的作品。"
        elif ratio_percent < 40:
            text += "，对话与描述的比例较为平衡。"
        elif ratio_percent < 70:
            text += "，对话比例较高，适合对话驱动的剧情发展。"
        else:
            text += "，对话比例很高，建议适当增加场景描述和动作说明，以丰富视觉表现。"
        
        if avg_length > 0:
            if avg_length < 20:
                text += f" 平均对话长度较短（约 {round(avg_length)} 字），对话较为简洁直接。"
            elif avg_length < 50:
                text += f" 平均对话长度适中（约 {round(avg_length)} 字）。"
            else:
                text += f" 平均对话长度较长（约 {round(avg_length)} 字），建议考虑是否有些对话可以精简。"
        
        return text
    
    def _generate_contextual_suggestions(self, parsed_data: Dict[str, Any], script_content: str, 
                                        dialogue_ratio: float, scene_count: int, char_count: int) -> List[str]:
        """生成基于实际内容的改进建议（不使用固定模板）"""
        suggestions = []
        scenes = parsed_data.get('scenes', [])
        
        # 基于实际场景数量给出建议
        if scene_count == 0:
            suggestions.append("未检测到场景划分，建议按照标准剧本格式（如：INT. 场景名 - 时间）来组织场景，有助于提升剧本的专业性和可读性。")
        elif scene_count == 1:
            suggestions.append("当前为单场景剧本，如果希望扩展剧情，可以考虑增加场景转换来丰富叙事空间。")
        elif scene_count < 5:
            # 分析场景转换是否流畅
            scene_titles = [s.get('title', '') for s in scenes]
            has_variety = len(set([s.split()[0] if s else '' for s in scene_titles])) > 1
            if not has_variety:
                suggestions.append("场景类型较为单一，建议增加内景/外景的转换，丰富视觉变化。")
        
        # 基于角色数量给出建议
        if char_count == 0:
            suggestions.append("未检测到角色信息，建议明确标注角色名称（通常全大写单独成行），以便更好地分析人物关系和对话。")
        elif char_count == 1:
            suggestions.append("当前为单角色剧本，如果希望增加戏剧冲突，可以考虑引入其他角色或外部因素。")
        elif char_count > 10:
            # 检查角色戏份是否均衡
            char_dialogue_count = {}
            for scene in scenes:
                for dialogue in scene.get('dialogue', []):
                    char = dialogue.get('character', '')
                    if char:
                        char_dialogue_count[char] = char_dialogue_count.get(char, 0) + len(dialogue.get('lines', []))
            
            if char_dialogue_count:
                counts = list(char_dialogue_count.values())
                if max(counts) > sum(counts) / len(counts) * 3:
                    suggestions.append("部分角色对话量明显多于其他角色，建议平衡各角色的戏份，确保配角也有足够的表现空间。")
        
        # 基于对话比例给出具体建议
        ratio_percent = dialogue_ratio * 100
        if ratio_percent < 15:
            # 分析是否有足够的动作描述
            action_lines = sum(len(s.get('action', [])) for s in scenes)
            if action_lines < scene_count * 2:
                suggestions.append("对话和动作描述都较少，建议增加场景描述、角色动作和情绪表达，让剧本更加生动。")
            else:
                suggestions.append("对话比例较低但动作描述丰富，适合视觉叙事。如果希望增加角色互动，可以适当增加对话。")
        elif ratio_percent > 80:
            suggestions.append("对话比例很高，建议适当增加场景描述、环境描写和角色动作，平衡对话与视觉元素。")
        
        # 基于场景内容给出建议
        if scenes:
            # 检查场景是否有足够的描述
            scenes_with_little_content = [s for s in scenes if len(s.get('dialogue', [])) + len(s.get('action', [])) < 2]
            if scenes_with_little_content:
                suggestions.append(f"有 {len(scenes_with_little_content)} 个场景内容较少，建议丰富这些场景的对话或描述。")
            
            # 检查场景长度是否均衡
            scene_sizes = [len(s.get('dialogue', [])) + len(s.get('action', [])) for s in scenes]
            if scene_sizes and max(scene_sizes) > min(scene_sizes) * 5:
                suggestions.append("场景篇幅差异较大，建议平衡各场景的内容量，避免某些场景过于简短或冗长。")
        
        # 如果没有生成任何建议，给出通用建议
        if not suggestions:
            suggestions.append("剧本结构基本完整，建议继续完善细节，包括角色动机、情节转折和情感表达。")
        
        return suggestions
    
    def _calculate_dialogue_ratio(self, script_content: str) -> float:
        """计算对话比例"""
        lines = script_content.split('\n')
        dialogue_lines = sum(1 for line in lines if re.match(r'^[A-Z\s]+$', line.strip()) and len(line.strip()) < 50)
        return dialogue_lines / max(len(lines), 1)
    
    def _calculate_avg_dialogue_length(self, scenes: List[Dict]) -> float:
        """计算平均对话长度"""
        if not scenes:
            return 0
        total_length = 0
        total_dialogues = 0
        for scene in scenes:
            for dialogue in scene.get('dialogue', []):
                for line in dialogue.get('lines', []):
                    total_length += len(line)
                    total_dialogues += 1
        return total_length / max(total_dialogues, 1)
    

# 单例模式
script_analysis_service = ScriptAnalysisService()


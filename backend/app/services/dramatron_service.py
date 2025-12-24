"""
Dramatron剧本生成服务
基于DeepMind的Dramatron，使用分层故事生成方法生成剧本
"""
import json
import re
from typing import Dict, List, Optional, Any, NamedTuple
from app.services.ollama_service import ollama_service

# Dramatron的数据结构
class Title(NamedTuple):
    """标题"""
    text: str
    
    @classmethod
    def from_string(cls, text: str):
        return cls(text=text.strip())
    
    def to_string(self) -> str:
        return self.text

class Character(NamedTuple):
    """角色"""
    name: str
    description: str
    
    @classmethod
    def from_string(cls, text: str):
        lines = text.strip().split('\n', 1)
        name = lines[0].strip() if lines else ""
        description = lines[1].strip() if len(lines) > 1 else ""
        return cls(name=name, description=description)

class Scene(NamedTuple):
    """场景"""
    number: int
    place: str
    characters: List[str]
    plot_point: str
    
    def to_string(self) -> str:
        chars_str = ", ".join(self.characters)
        return f"场景 {self.number}: {self.place}\n角色: {chars_str}\n情节: {self.plot_point}"

class Place(NamedTuple):
    """地点"""
    name: str
    description: str
    
    @classmethod
    def from_string(cls, place_name: str, place_text: str):
        return cls(name=place_name.strip(), description=place_text.strip())
    
    def to_string(self) -> str:
        return f"{self.name}: {self.description}"

class Story(NamedTuple):
    """故事"""
    title: Title
    characters: List[Character]
    scenes: List[Scene]
    places: Dict[str, Place]
    dialogs: List[str]

class DramatronService:
    """Dramatron剧本生成服务"""
    
    def __init__(self):
        self.available = ollama_service.available
        self.default_model = "qwen2:1.5b"
    
    async def generate_title(self, storyline: str, model: Optional[str] = None) -> Dict[str, Any]:
        """生成标题"""
        if not self.available:
            return {"error": "Ollama服务不可用"}
        
        prompt = f"""根据以下故事梗概，生成一个吸引人的剧本标题：

故事梗概：{storyline}

请只返回标题，不要其他内容。"""
        
        try:
            result = await ollama_service.chat(
                [{"role": "user", "content": prompt}],
                model=model or self.default_model
            )
            
            if "error" in result:
                return result
            
            title_text = result.get("message", {}).get("content", "").strip()
            # 清理标题（移除引号等）
            title_text = re.sub(r'^["\']|["\']$', '', title_text)
            
            return {
                "success": True,
                "title": Title.from_string(title_text).to_string()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_characters(
        self,
        storyline: str,
        title: str,
        num_characters: int = 3,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成角色"""
        if not self.available:
            return {"error": "Ollama服务不可用"}
        
        prompt = f"""根据以下故事梗概和标题，生成{num_characters}个主要角色的描述：

标题：{title}
故事梗概：{storyline}

请为每个角色生成名称和简短描述（1-2句话），格式如下：
角色1名称
角色1描述

角色2名称
角色2描述

..."""
        
        try:
            result = await ollama_service.chat(
                [{"role": "user", "content": prompt}],
                model=model or self.default_model
            )
            
            if "error" in result:
                return result
            
            text = result.get("message", {}).get("content", "")
            characters = self._parse_characters(text)
            
            return {
                "success": True,
                "characters": [
                    {"name": c.name, "description": c.description}
                    for c in characters
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_scenes(
        self,
        storyline: str,
        title: str,
        characters: List[Dict[str, str]],
        num_scenes: int = 5,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成场景"""
        if not self.available:
            return {"error": "Ollama服务不可用"}
        
        char_descriptions = "\n".join([
            f"- {c['name']}: {c['description']}"
            for c in characters
        ])
        
        prompt = f"""根据以下信息，生成{num_scenes}个场景：

标题：{title}
故事梗概：{storyline}

角色：
{char_descriptions}

请为每个场景生成：
1. 场景编号
2. 地点名称
3. 出现的角色（用逗号分隔）
4. 该场景的情节要点（1-2句话）

格式：
场景1: [地点]
角色: [角色列表]
情节: [情节描述]

场景2: [地点]
..."""
        
        try:
            result = await ollama_service.chat(
                [{"role": "user", "content": prompt}],
                model=model or self.default_model
            )
            
            if "error" in result:
                return result
            
            text = result.get("message", {}).get("content", "")
            scenes = self._parse_scenes(text)
            
            return {
                "success": True,
                "scenes": [
                    {
                        "number": s.number,
                        "place": s.place,
                        "characters": s.characters,
                        "plot_point": s.plot_point
                    }
                    for s in scenes
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_place_descriptions(
        self,
        storyline: str,
        scenes: List[Dict[str, Any]],
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成地点描述"""
        if not self.available:
            return {"error": "Ollama服务不可用"}
        
        places = list(set([s["place"] for s in scenes]))
        places_str = ", ".join(places)
        
        prompt = f"""根据以下故事梗概和场景地点，为每个地点生成简短描述（1-2句话）：

故事梗概：{storyline}
地点列表：{places_str}

格式：
[地点1名称]: [描述]

[地点2名称]: [描述]
..."""
        
        try:
            result = await ollama_service.chat(
                [{"role": "user", "content": prompt}],
                model=model or self.default_model
            )
            
            if "error" in result:
                return result
            
            text = result.get("message", {}).get("content", "")
            place_descriptions = self._parse_places(text, places)
            
            return {
                "success": True,
                "places": {
                    name: {"name": name, "description": desc}
                    for name, desc in place_descriptions.items()
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_dialog(
        self,
        storyline: str,
        scene: Dict[str, Any],
        characters: List[Dict[str, str]],
        place_description: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成对话"""
        if not self.available:
            return {"error": "Ollama服务不可用"}
        
        char_descriptions = "\n".join([
            f"- {c['name']}: {c['description']}"
            for c in characters
            if c['name'] in scene.get("characters", [])
        ])
        
        prompt = f"""根据以下信息，生成场景{scene.get('number', 1)}的对话：

故事梗概：{storyline}
场景：{scene.get('place', '')}
地点描述：{place_description}
情节要点：{scene.get('plot_point', '')}

出现的角色：
{char_descriptions}

请生成该场景的完整对话，使用标准剧本格式：
[角色名]
[对话内容]

[角色名]
[对话内容]
..."""
        
        try:
            result = await ollama_service.chat(
                [{"role": "user", "content": prompt}],
                model=model or self.default_model
            )
            
            if "error" in result:
                return result
            
            dialog_text = result.get("message", {}).get("content", "")
            
            return {
                "success": True,
                "dialog": dialog_text,
                "scene_number": scene.get("number", 1)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_full_script(
        self,
        storyline: str,
        num_scenes: int = 5,
        num_characters: int = 3,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成完整剧本"""
        if not self.available:
            return {"error": "Ollama服务不可用"}
        
        try:
            # 1. 生成标题
            title_result = await self.generate_title(storyline, model)
            if "error" in title_result:
                return title_result
            title = title_result["title"]
            
            # 2. 生成角色
            characters_result = await self.generate_characters(
                storyline, title, num_characters, model
            )
            if "error" in characters_result:
                return characters_result
            characters = characters_result["characters"]
            
            # 3. 生成场景
            scenes_result = await self.generate_scenes(
                storyline, title, characters, num_scenes, model
            )
            if "error" in scenes_result:
                return scenes_result
            scenes = scenes_result["scenes"]
            
            # 4. 生成地点描述
            places_result = await self.generate_place_descriptions(
                storyline, scenes, model
            )
            if "error" in places_result:
                return places_result
            places = places_result["places"]
            
            # 5. 生成每个场景的对话
            dialogs = []
            for scene in scenes:
                place_name = scene["place"]
                place_desc = places.get(place_name, {}).get("description", "")
                
                dialog_result = await self.generate_dialog(
                    storyline, scene, characters, place_desc, model
                )
                if "error" not in dialog_result:
                    dialogs.append({
                        "scene_number": scene["number"],
                        "dialog": dialog_result["dialog"]
                    })
            
            # 6. 组合成完整剧本
            script = self._format_script(title, characters, scenes, places, dialogs)
            
            return {
                "success": True,
                "script": script,
                "title": title,
                "characters": characters,
                "scenes": scenes,
                "places": places,
                "dialogs": dialogs
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_characters(self, text: str) -> List[Character]:
        """解析角色文本"""
        characters = []
        lines = text.strip().split('\n')
        current_name = None
        current_desc = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是角色名（通常是没有冒号的行，或者是新段落）
            if not line.startswith('-') and ':' not in line and len(line) < 30:
                # 可能是角色名
                if current_name:
                    characters.append(Character(
                        name=current_name,
                        description=' '.join(current_desc)
                    ))
                current_name = line
                current_desc = []
            else:
                # 移除"- "前缀和"角色名: "前缀
                clean_line = re.sub(r'^[-•]\s*', '', line)
                clean_line = re.sub(r'^[^:]+:\s*', '', clean_line)
                if clean_line:
                    current_desc.append(clean_line)
        
        if current_name:
            characters.append(Character(
                name=current_name,
                description=' '.join(current_desc) if current_desc else ""
            ))
        
        return characters if characters else [Character(name="未知角色", description="")]
    
    def _parse_scenes(self, text: str) -> List[Scene]:
        """解析场景文本"""
        scenes = []
        # 使用正则表达式匹配场景
        pattern = r'场景\s*(\d+)[:：]\s*(.+?)\n角色[:：]\s*(.+?)\n情节[:：]\s*(.+?)(?=\n场景|\Z)'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            number = int(match.group(1))
            place = match.group(2).strip()
            characters_str = match.group(3).strip()
            plot_point = match.group(4).strip()
            
            characters = [c.strip() for c in re.split(r'[,，、]', characters_str) if c.strip()]
            
            scenes.append(Scene(
                number=number,
                place=place,
                characters=characters,
                plot_point=plot_point
            ))
        
        # 如果没有匹配到，尝试简单解析
        if not scenes:
            lines = text.split('\n')
            current_scene = None
            for line in lines:
                if '场景' in line or 'Scene' in line.lower():
                    if current_scene:
                        scenes.append(current_scene)
                    # 提取场景号
                    num_match = re.search(r'\d+', line)
                    num = int(num_match.group()) if num_match else len(scenes) + 1
                    place_match = re.search(r'[:：]\s*(.+?)(?:\n|$)', line)
                    place = place_match.group(1).strip() if place_match else "未知地点"
                    current_scene = Scene(number=num, place=place, characters=[], plot_point="")
                elif '角色' in line or 'Character' in line.lower():
                    if current_scene:
                        chars = re.split(r'[,，、:]', line)
                        current_scene = Scene(
                            number=current_scene.number,
                            place=current_scene.place,
                            characters=[c.strip() for c in chars[1:] if c.strip()],
                            plot_point=current_scene.plot_point
                        )
                elif '情节' in line or 'Plot' in line.lower():
                    if current_scene:
                        plot = line.split(':', 1)[-1].strip() if ':' in line else line.strip()
                        current_scene = Scene(
                            number=current_scene.number,
                            place=current_scene.place,
                            characters=current_scene.characters,
                            plot_point=plot
                        )
            
            if current_scene:
                scenes.append(current_scene)
        
        return scenes if scenes else [
            Scene(number=1, place="未知地点", characters=["角色1"], plot_point="场景情节")
        ]
    
    def _parse_places(self, text: str, place_names: List[str]) -> Dict[str, str]:
        """解析地点描述"""
        places = {}
        
        for place_name in place_names:
            # 尝试找到该地点的描述
            pattern = rf'{re.escape(place_name)}[:：]\s*(.+?)(?=\n\w+[:：]|\Z)'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                places[place_name] = match.group(1).strip()
            else:
                places[place_name] = f"{place_name}的场景描述"
        
        return places
    
    def _format_script(
        self,
        title: str,
        characters: List[Dict[str, str]],
        scenes: List[Dict[str, Any]],
        places: Dict[str, Dict[str, str]],
        dialogs: List[Dict[str, str]]
    ) -> str:
        """格式化完整剧本"""
        script_lines = [f"《{title}》", "", "=" * 60, ""]
        
        # 角色介绍
        script_lines.append("角色：")
        for char in characters:
            script_lines.append(f"  {char['name']}: {char['description']}")
        script_lines.append("")
        
        # 场景和对话
        dialogs_dict = {d["scene_number"]: d["dialog"] for d in dialogs}
        
        for scene in scenes:
            scene_num = scene["number"]
            script_lines.append("=" * 60)
            script_lines.append(f"场景 {scene_num}: {scene['place']}")
            if scene['place'] in places:
                script_lines.append(f"地点描述: {places[scene['place']]['description']}")
            script_lines.append(f"角色: {', '.join(scene['characters'])}")
            script_lines.append(f"情节: {scene['plot_point']}")
            script_lines.append("")
            
            # 添加对话
            if scene_num in dialogs_dict:
                script_lines.append(dialogs_dict[scene_num])
                script_lines.append("")
        
        return "\n".join(script_lines)

# 全局实例
dramatron_service = DramatronService()












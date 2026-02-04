"""
Directory Analyzer - Uses LLM to analyze entire directory and identify anime
"""
from typing import List, Optional
from pydantic import BaseModel
from app.models.payload import FileNode
import json

class DirectoryInfo(BaseModel):
    """Information about a directory of anime files"""
    is_single_anime: bool  # Are all files from the same anime?
    anime_title: str  # Extracted anime title
    season: Optional[int] = None  # Season number
    episode_range: Optional[List[int]] = None  # [start, end]
    year: Optional[int] = None # Year of release
    confidence: float  # 0-1 confidence score
    reasoning: str  # Why this conclusion

DIRECTORY_ANALYSIS_PROMPT = """你是专业的动漫文件整理专家。请分析以下文件列表,判断它们是否属于同一部动漫作品。

**输出格式要求**:
必须严格按照以下JSON格式输出,不要添加任何markdown标记或其他内容:

{{
  "is_single_anime": true,
  "anime_title": "某科学的超电磁炮",
  "season": 1,
  "year": 2009,
  "episode_range": [1, 24],
  "confidence": 0.95,
  "reasoning": "所有文件遵循相同的命名模式 [字幕组][作品名][集数],集数连续从01到24"
}}

**分析要点**:
1. 检查文件名模式是否一致
2. 提取动漫标题(去除字幕组、分辨率等标签)
3. 识别季度 (Season):
   - 必须将标题中的季度后缀（如 'Zoku', 'Kan', 'Season 2'）分离，转化为数字存入 season 字段。
   - 常见映射: 'Zoku'/ '2nd' -> 2; 'Kan'/'Final'/'3rd' -> 3 (视具体作品而定); 'Kai' -> 可能会重置或延续。
   - anime_title 字段应仅包含基础标题（不含季度后缀），以便 TMDB 搜索。
   - 如果未指定，默认为 1。
4. 提取年份 (Year):
   - 从文件名或目录名中提取发布年份。
5. 评估置信度(0-1之间)

**文件列表**:
{files}

请直接输出JSON,不要包含```json```等标记。
"""

class DirectoryAnalyzer:
    """Analyzes directories to identify anime series"""
    
    @staticmethod
    async def analyze_directory(files: List[FileNode]) -> DirectoryInfo:
        """
        Analyze a directory of files to identify if they belong to the same anime
        
        Args:
            files: List of FileNode objects
            
        Returns:
            DirectoryInfo with analysis results
        """
        from .llm_engine import LLMEngine
        from app.services.system.settings_service import SettingsService
        from openai import AsyncOpenAI
        
        # Get LLM settings
        api_key = SettingsService.get_setting("llm.api_key", "")
        base_url = SettingsService.get_setting("llm.base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = SettingsService.get_setting("llm.model", "qwen-plus")
        
        if not api_key:
            # Return low confidence if no API key
            return DirectoryInfo(
                is_single_anime=False,
                anime_title="",
                confidence=0.0,
                reasoning="LLM API key not configured"
            )
        
        # Prepare file list
        file_list = "\n".join([f"- {f.name}" for f in files[:50]])  # Limit to 50 files
        prompt = DIRECTORY_ANALYSIS_PROMPT.format(files=file_list)
        
        # Create client
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        try:
            # Enable structured output for Qwen models
            extra_params = {}
            if model.startswith("qwen"):
                extra_params["response_format"] = {"type": "json_object"}
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是专业的动漫文件整理助手,擅长分析文件命名模式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                **extra_params
            )
            
            content = response.choices[0].message.content
            # Clean up response
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            data = json.loads(content)
            return DirectoryInfo(**data)
            
        except Exception as e:
            print(f"Directory analysis error: {e}")
            # Return low confidence on error
            return DirectoryInfo(
                is_single_anime=False,
                anime_title="",
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}"
            )

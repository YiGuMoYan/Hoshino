from app.db.session import SessionLocal
from app.db.models import LLMConfig
import json
from openai import AsyncOpenAI
from app.models.payload import AnimeNamingPayload
from app.models.result import AnimeNamingResult, BatchNamingResult
from loguru import logger

SYSTEM_PROMPT = """
你是一个专业的动漫文件整理专家。
你的任务是分析动漫文件名并提取结构化的元数据。

输入: 包含文件列表和候选信息的 JSON payload。
输出: 仅返回 JSON。不要包含 markdown 格式。不要解释。

规则:
1. 识别 动漫标题 (Anime Title), 年份 (Year), 季度 (Season), 集数 (Episode), 分段 (Cour), 部分 (Part)。
2. 标准化标题: 使用最常用的官方中文或日文标题。
3. 季度 (Season): 如果未指定，默认为 1。对于 OVA, OAD, SP, Special 等，Season 必须为 0。
4. 重命名格式: "{Title} - S{Season:02d}E{Episode:02d}.{ext}"
5. 如果置信度较低 (< 0.8)，请相应设置置信度分数。
6. 强制要求: 输出对象中必须包含 "original_name" 字段，且必须完全复制输入的文件名，不得修改。

输出格式示例:
{
  "results": [
    {
      "original_name": "filename.mkv",
      "anime_title": "Title",
      "year": 2023,
      "season": 1,
      "episode": 1,
      "type": "episode",
      "confidence": 1.0,
      "rename_to": "Title - S01E01.mkv"
    }
  ]
}
"""

class LLMEngine:
    @staticmethod
    async def test_connection(config: LLMConfig) -> bool:
        """
        Tests the LLM connection with the provided config.
        """
        try:
            client = AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
            await client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"Test Connection Failed: {e}")
            return False

    @staticmethod
    async def analyze(payload: AnimeNamingPayload) -> BatchNamingResult:
        """
        Sends payload to LLM and returns structured result.
        """
        # Fetch settings from new settings service
        from app.services.system.settings_service import SettingsService
        
        api_key = SettingsService.get_setting("llm.api_key", "")
        base_url = SettingsService.get_setting("llm.base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = SettingsService.get_setting("llm.model", "qwen-plus")
        
        if not api_key:
            logger.error("LLM Error: No API Key configured")
            return BatchNamingResult(results=[])

        # Initialize Client Per Request (or cached if settings haven't changed)
        # For simplicity and thread-safety, we init here. Overhead is low for httpx client usually.
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": payload.model_dump_json()}
                ],
                # response_format={"type": "json_object"}, # Ensure valid JSON (if model supports it)
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            # Basic cleanup if model adds markdown logic
            content = content.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(content)
            
            # Handle different response formats
            if isinstance(data, list):
                # Model returned array directly
                results = [AnimeNamingResult(**item) for item in data]
                return BatchNamingResult(results=results)
            elif isinstance(data, dict):
                if "results" in data:
                    # Standard format with results field
                    results = [AnimeNamingResult(**item) for item in data["results"]]
                    return BatchNamingResult(results=results)
                else:
                    # Single object or malformed - try to parse as single result
                    logger.warning(f"LLM Warning: Response missing 'results' field. Data: {data}")
                    # Try to parse as single AnimeNamingResult
                    try:
                        result = AnimeNamingResult(**data)
                        return BatchNamingResult(results=[result])
                    except:
                        # Cannot parse, return empty
                        logger.error("LLM Error: Cannot parse response as AnimeNamingResult")
                        return BatchNamingResult(results=[])
            else:
                logger.error(f"LLM Error: Unexpected response type: {type(data)}")
                return BatchNamingResult(results=[])

        except json.JSONDecodeError as e:
            logger.error(f"LLM Error: Invalid JSON response - {e}")
            logger.debug(f"Raw content: {content}")
            return BatchNamingResult(results=[])
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return BatchNamingResult(results=[])

    @staticmethod
    async def identify_season_with_context(files: list[str], tmdb_seasons: list[dict]) -> dict:
        """
        Ask LLM to identify season based on files and TMDB context.
        """
        from app.services.system.settings_service import SettingsService
        
        api_key = SettingsService.get_setting("llm.api_key", "")
        base_url = SettingsService.get_setting("llm.base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = SettingsService.get_setting("llm.model", "qwen-plus")

        if not api_key:
            return None

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        # Prepare context
        context_data = {
            "files": files[:10], # Limit to first 10 files to save context
            "tmdb_seasons": tmdb_seasons
        }

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SEASON_MATCH_PROMPT},
                    {"role": "user", "content": json.dumps(context_data, ensure_ascii=False)}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"LLM Season Match Error: {e}")
            return None

    @staticmethod
    async def identify_specials_with_context(files: list[str], tmdb_specials: list[dict]) -> dict:
        """
        Ask LLM to map special files (OVAs, CMs) to TMDB Season 0 episodes.
        Returns: { "filename": episode_number, ... }
        """
        from app.services.system.settings_service import SettingsService
        
        api_key = SettingsService.get_setting("llm.api_key", "")
        base_url = SettingsService.get_setting("llm.base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = SettingsService.get_setting("llm.model", "qwen-plus")

        if not api_key:
            return {}

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        SPECIALS_MATCH_PROMPT = """
你是一个动漫元数据整理专家。
我将提供一组被识别为 "Specials" (Season 0) 的文件名列表，以及 TMDB 上的 Season 0 剧集列表。
你的任务是将每个文件精确匹配到 TMDB 的剧集编号 (Episode Number)。

输入:
1. Files: 文件名列表
2. TMDB Specials: 剧集列表 (Episode Number, Name, Overview)

规则:
1. 根据文件名中的关键词 (如 OVA, CM, Special, 标题) 与 TMDB 剧集标题或简介进行匹配。
2. 比如 "Zoku OVA" 应该匹配名字中包含 "续" 或 "Zoku" 的 OVA。
3. "CM" (Commercial) 如果 TMDB 中有对应的 "CM Collection" 或类似条目，请匹配。如果没有明确对应，请返回 null。
4. 如果无法确定，返回 null。

输出格式 (JSON):
{
  "mappings": {
    "filename1": episode_number_int,
    "filename2": null,
    ...
  }
}
"""
        # Prepare context (simplify TMDB data to save tokens)
        simple_specials = [
            {"episode_number": s.get("episode_number"), "name": s.get("name"), "overview": s.get("overview", "")[:100]}
            for s in tmdb_specials
        ]

        context_data = {
            "files": files,
            "tmdb_specials": simple_specials
        }

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SPECIALS_MATCH_PROMPT},
                    {"role": "user", "content": json.dumps(context_data, ensure_ascii=False)}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            return result.get("mappings", {})
            
        except Exception as e:
            print(f"LLM Special Match Error: {e}")
            return {}

# -*- coding: utf-8 -*-
import os
import shutil
import re
from typing import List, Optional, Tuple
try:
    from pydantic_settings import BaseSettings # dummy check
    from pypinyin import pinyin, Style, lazy_pinyin
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False
    print("Warning: pypinyin not found, falling back to first character.")
from datetime import datetime
from pydantic import BaseModel
from app.services.core.scanner import ScannerService
from app.services.analysis.rule_engine import RuleEngine
from app.services.analysis.llm_engine import LLMEngine
from app.services.external.tmdb_service import TMDBService
from app.services.analysis.filename_parser import FilenameParser
from app.services.system.settings_service import SettingsService
from app.models.payload import AnimeNamingPayload, Context, AnimeCandidates, FileNode
from app.models.result import AnimeNamingResult

class RenameItem(BaseModel):
    original_path: str
    new_path: str
    status: str = "pending" # pending, done, error
    log: Optional[str] = None
    anime_info: Optional[dict] = None # Metadata for UI
    display_path: Optional[str] = None # Relative path for UI display (e.g. "Season 1/file.mkv")

class OrganizerService:
    def __init__(self):
        self.journal = [] # Simple in-memory journal for now
        self.scan_logs = [] # Store scan logs
        self.current_plan = [] # Store current renaming plan
        self.is_scanning = False # Scanning status flag
        self.tmdb_service = TMDBService()  # Initialize TMDB service
    
    def add_log(self, message: str, level: str = "info"):
        """Add a log message with timestamp."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.scan_logs.append(log_entry)
        print(f"[{level.upper()}] {message}")  # Also print to console
    
    def get_logs(self) -> List[dict]:
        """Get all scan logs."""
        return self.scan_logs
    
    def clear_logs(self):
        """Clear all scan logs."""
        self.scan_logs.clear()

    async def scan_directory(self, directory_path: str, context: dict = None) -> List[RenameItem]:
        if self.is_scanning:
             raise Exception("Scan already in progress")
        
        self.is_scanning = True
        
        if context:
            self.add_log(f"使用辅助元数据: {context}", "info")
        
        # 从数据库读取目标媒体库路径
        target_library_path = SettingsService.get_setting("app.target_library_path", "")
        if not target_library_path:
            self.add_log("错误: 未配置目标媒体库路径，请在设置中配置 app.target_library_path", "error")
            self.is_scanning = False
            raise ValueError("目标媒体库路径未配置")
        
        self.target_library_path = target_library_path  # 存储目标库路径
        
        self.clear_logs()
        self.add_log(f"开始扫描目录: {directory_path}", "info")
        self.add_log(f"目标媒体库: {target_library_path}", "info")
        
        try:
             return await self._scan_internal(directory_path, context=context)
        except Exception as e:
             self.add_log(f"扫描过程中发生错误: {str(e)}", "error")
             import traceback
             traceback.print_exc()
             raise e
        finally:
             self.is_scanning = False
    
    def _get_initial(self, text: str) -> str:
        """Get the initial letter of the text (A-Z, #)"""
        if not text:
            return "#"
            
        first_char = text[0]
        
        # English or Number
        if 'a' <= first_char.lower() <= 'z':
            return first_char.upper()
        if '0' <= first_char <= '9':
            return "#"
            
        # Chinese
        try:
             # Try importing inside method to avoid global scope issues if not installed
             from pypinyin import pinyin, Style
             if PYPINYIN_AVAILABLE:
                initials = pinyin(first_char, style=Style.FIRST_LETTER)
                if initials and initials[0]:
                    char = initials[0][0][0].upper()
                    if 'A' <= char <= 'Z':
                        return char
        except ImportError:
             pass
        except Exception:
             pass
        
        return "#"

    def _process_subtitles(self, dir_path: str, subtitle_files: List[FileNode], plan: List[RenameItem]):
        """
        Match subtitles to video files in the current directory plan and generate rename items for them.
        """
        if not subtitle_files or not plan:
            return

        # Filter video items belonging to this directory
        # Exclude subtitles themselves if they somehow got into plan (unlikely but safe)
        current_dir_plan = [item for item in plan if os.path.dirname(item.original_path) == dir_path and item.original_path not in [s.name for s in subtitle_files]]

        for video_item in current_dir_plan:
            vid_name = os.path.basename(video_item.original_path)
            vid_stem = os.path.splitext(vid_name)[0]

            new_vid_name = os.path.basename(video_item.new_path)
            new_vid_stem = os.path.splitext(new_vid_name)[0]
            new_vid_dir = os.path.dirname(video_item.new_path)

            for sub_file in subtitle_files:
                sub_name = sub_file.name
                if sub_name.startswith(vid_stem):
                    remainder = sub_name[len(vid_stem):]
                    new_sub_name = new_vid_stem + remainder
                    new_sub_path = os.path.join(new_vid_dir, new_sub_name)
                    
                    # Avoid duplicate entries
                    if any(item.original_path == os.path.join(dir_path, sub_name) for item in plan):
                        continue

                    plan.append(RenameItem(
                        original_path=os.path.join(dir_path, sub_name),
                        new_path=new_sub_path,
                        anime_info=video_item.anime_info,
                        display_path=video_item.display_path.replace(new_vid_name, new_sub_name) if video_item.display_path else None
                    ))
                    self.add_log(f"✓ 字幕同步: {sub_name} -> {new_sub_name}", "success")

    async def _scan_internal(self, directory_path: str, context: dict = None) -> List[RenameItem]:
        self.clear_logs()  # Clear previous logs
        self.add_log(f"开始扫描: {directory_path}")
        
        # Check if input is a file (common for single file downloads)
        if os.path.isfile(directory_path):
            self.add_log("检测到输入为单文件，切换至单文件处理模式")
            file_name = os.path.basename(directory_path)
            file_dir = os.path.dirname(directory_path)
            file_size_mb = os.path.getsize(directory_path) / (1024 * 1024)
            
            node = FileNode(
                name=file_name,
                size_mb=round(file_size_mb, 2),
                rel_path=file_name
            )
            scan_results = {file_dir: [node]}
        else:
            scan_results = ScannerService.scan_directory(directory_path)
            
        total_files = sum(len(files) for files in scan_results.values())
        self.add_log(f"发现 {len(scan_results)} 个目录节点，共 {total_files} 个文件")
        
        plan = []

        for dir_path, files in scan_results.items():
            self.add_log(f"处理目录: {dir_path} ({len(files)} 个文件)")
            
            # Skip if no files
            if not files:
                continue
            
            # Step 1: Try Rule Engine first for each file
            # Separate video and subtitle files
            video_files = []
            subtitle_files = []
            VIDEO_EXTS = {'.mkv', '.mp4', '.avi', '.mov', '.iso', '.ts'}
            SUBTITLE_EXTS = {'.ass', '.srt', '.sub', '.vtt'}
            
            for f in files:
                ext = os.path.splitext(f.name)[1].lower()
                if ext in VIDEO_EXTS:
                    video_files.append(f)
                elif ext in SUBTITLE_EXTS:
                    subtitle_files.append(f)
            
            # Use only video files for Rule Engine and Analysis
            rule_matched_files = []
            remaining_files = []
            # Group by title for batch processing
            rule_matched_groups = {}
            for file_node in video_files:
                res = RuleEngine.parse_filename(file_node.name)
                if res:
                    if res.anime_title not in rule_matched_groups:
                        rule_matched_groups[res.anime_title] = []
                    rule_matched_groups[res.anime_title].append((file_node, res))
                    rule_matched_files.append(file_node)
                else:
                    remaining_files.append(file_node)

            # Process Rule Engine Matches with TMDB Enrichment
            for anime_title, items in rule_matched_groups.items():
                self.add_log(f"规则引擎分组: {anime_title} ({len(items)} 个文件)")
                
                # TMDB Enrichment
                tmdb_info = None
                best_candidate = None
                poster_path = None
                backdrop_path = None
                tmdb_id = None
                
                try:
                    candidates = await self.tmdb_service.search_anime(anime_title)
                    if candidates:
                        # Find best match
                        best_candidate = max(candidates, key=lambda c: self.tmdb_service.calculate_confidence(c, anime_title))
                        confidence = self.tmdb_service.calculate_confidence(best_candidate, anime_title)
                        
                        if confidence > 0.6:
                            self.add_log(f"✓ TMDB 校验成功: {anime_title} -> {best_candidate.name} (置信度: {confidence:.2f})", "success")
                            
                            # Get details (images, etc)
                            details = await self.tmdb_service.get_tv_details(best_candidate.id)
                            if details:
                                tmdb_id = best_candidate.id
                                poster_path = details.get('poster_path')
                                backdrop_path = details.get('backdrop_path')
                                
                                # Use TMDB name as official title
                                anime_title = best_candidate.name
                        else:
                             self.add_log(f"TMDB 匹配置信度过低 ({confidence:.2f})，保持原名: {anime_title}", "warning")
                    else:
                        self.add_log(f"TMDB 未找到结果，保持原名: {anime_title}", "warning")
                        
                except Exception as e:
                    self.add_log(f"TMDB 查询失败: {e}，保持原名", "error")

                # Get base image URL
                base_url = "https://image.tmdb.org/t/p/"
                if tmdb_id:
                     try:
                         cfg = await self.tmdb_service.get_configuration()
                         base_url = cfg.get('images', {}).get('secure_base_url', base_url)
                     except: 
                        pass

                # Generate Rename Items
                for file_node, res in items:
                     # Re-construct path with potentially updated anime_title
                     initial = self._get_initial(anime_title)
                     season_folder = f"Season {res.season}"
                     
                     # Update destination calculation
                     # logic: [Target]/[Initial]/[Title]/[Season]/[File]
                     
                     # We might need to adjust filename if it used the old title? 
                     # RuleEngine.parse_filename returns 'rename_to' which might use the parsed title.
                     # But actually `res.rename_to` usually preserves the recognized title or formats it.
                     # If we change the title, we might want to update the filename too?
                     # Standard naming: "Title - SxxExx.ext"
                     
                     # Let's reconstruct filename using the NEW title if we have one
                     name, ext = os.path.splitext(res.rename_to)
                     # res.rename_to usually is "Title - S01E01.mkv"
                     # If we just want to replace the Title part...
                     
                     # Safer way: Re-format using standard format
                     # res has .season, .episode
                     # Use sanitized new title
                     # Assuming res.episode is available? RuleEngine result has it?
                     # Let's check RuleEngine return type. It creates AnimeNamingResult.
                     
                     new_filename = res.rename_to
                     if best_candidate:
                         # Re-generate filename with new title
                         # format: Title - SxxExx
                         # Need episode number from res?
                         # RuleEngine result `res` might not expose raw episode number easily if it only returns `rename_to`.
                         # Let's rely on `rename_to` for now but replace the title prefix if it matches?
                         # Or better: Just check if we can parse the episode from file_node again or if res has it?
                         # Viewing RuleEngine code would be ideal but let's stick to replacing the folder path first.
                         # Users usually care most about FOLDER structure being localized.
                         pass

                     new_full_path = os.path.join(self.target_library_path, initial, anime_title, season_folder, res.rename_to)
                     
                     # If we want to rename the file itself to match the new title:
                     if best_candidate:
                         # Try to extract S/E from either res.rename_to or using FilenameParser again?
                         # res.rename_to is e.g. "Frieren - S01E01.mkv"
                         # We want "葬送的芙莉莲 - S01E01.mkv"
                         
                         # Simple string replace? Risk of false positive.
                         # Better: use regex on res.rename_to.
                         # Pattern: ^(.*?) - (S\d+E\d+.*)$
                         match = re.match(r"^(.*?) - (S\d+.*)$", res.rename_to)
                         if match:
                             suffix = match.group(2)
                             new_filename = f"{anime_title} - {suffix}"
                             new_full_path = os.path.join(self.target_library_path, initial, anime_title, season_folder, new_filename)

                     plan.append(RenameItem(
                         original_path=os.path.join(dir_path, file_node.name),
                         new_path=new_full_path,
                         anime_info={
                            "title": anime_title,
                            "year": best_candidate.year if best_candidate else None,
                            "poster": f"{base_url}w500{poster_path}" if poster_path else None,
                            "backdrop": f"{base_url}original{backdrop_path}" if backdrop_path else None,
                            "tmdb_id": tmdb_id,
                            "season": res.season
                         } if tmdb_id else None
                     ))
                     self.add_log(f"✓ 规则归档: {file_node.name} -> {anime_title}/{season_folder}/{new_filename}", "success")
            
            # If all files matched by rule engine, skip to next directory
            if not remaining_files:
                self._process_subtitles(dir_path, subtitle_files, plan)
                continue
            
            self.add_log(f"规则引擎无法识别 {len(remaining_files)} 个文件，使用智能分析...")
            
            # Step 2: Use LLM to analyze directory (identify if single anime)
            from app.services.analysis.directory_analyzer import DirectoryAnalyzer
            
            try:
                self.add_log(f"正在分析目录结构...")
                dir_info = await DirectoryAnalyzer.analyze_directory(remaining_files)
                
                self.add_log(f"目录分析结果: {dir_info.anime_title} Season {dir_info.season} (置信度: {dir_info.confidence:.2f})")
                self.add_log(f"分析原因: {dir_info.reasoning}")

                # Apply Context Overrides
                if context:
                    if context.get('series_name'):
                        self.add_log(f"使用指定番剧名: {context['series_name']} (覆盖识别结果: {dir_info.anime_title})", "warning")
                        dir_info.anime_title = context['series_name']
                        # Increase confidence as it is manually provided
                        dir_info.confidence = 1.0 
                    
                    if context.get('season') is not None:
                        self.add_log(f"使用指定季度: Season {context['season']} (覆盖识别结果: {dir_info.season})", "warning")
                        dir_info.season = int(context['season'])
                        # Increase confidence
                        dir_info.confidence = 1.0
            except Exception as e:
                self.add_log(f"✗ 目录分析失败: {str(e)}", "error")
                import traceback
                traceback.print_exc()
                # Skip this directory on error
                continue
            
            if dir_info.is_single_anime and dir_info.confidence >= 0.7:
                # Step 3: Single TMDB call for the entire directory
                self.add_log(f"TMDB 搜索: {dir_info.anime_title}")
                
                try:
                    candidates = await self.tmdb_service.search_anime(dir_info.anime_title)
                    
                    if candidates:
                        # Get best candidate
                        best_candidate = max(candidates, key=lambda c: self.tmdb_service.calculate_confidence(c, dir_info.anime_title))
                        tmdb_confidence = self.tmdb_service.calculate_confidence(best_candidate, dir_info.anime_title)
                        
                        self.add_log(f"✓ TMDB 匹配: {best_candidate.name} (置信度: {tmdb_confidence:.2f})", "success")
                        
                        # Try to get year from files
                        years = [FilenameParser.extract_year(f.name) for f in remaining_files]
                        years = [y for y in years if y is not None]
                        local_year = None
                        if years:
                            from collections import Counter
                            local_year = Counter(years).most_common(1)[0][0]
                        
                        # Use local year or LLM extracted year
                        target_year = local_year if local_year else getattr(dir_info, 'year', None)
                        
                        # Fetch details for seasons
                        tmdb_info = await self.tmdb_service.get_tv_details(best_candidate.id)
                        
                        matched_season = None
                        matched_season_name = ""

                        if tmdb_info and 'seasons' in tmdb_info:
                             # Check for specific season name match in the directory title
                             # e.g. dir_title = "Oregairu Zoku", season name = "My Teen Romantic Comedy SNAFU TWO!" or "我的青春恋爱物语果然有问题。续"
                             
                             # We can pass the raw directory name or the LLM extracted title for fuzzy matching
                             # But `dir_info.anime_title` is usually normalized.
                             # Let's check `dir_path` basename or `file_node.name`? 
                             # `scan_results` keys are `dir_path`.
                             
                             dir_basename = os.path.basename(dir_path)
                             
                             # 只统计正片集数（排除OVA/SP/NC/CM等特殊内容）
                             # 通过文件名判断：包含 OVA、SP、NC、CM、PV、MENU 等关键词的排除
                             special_keywords = ['OVA', 'SP', 'NC', 'CM', 'PV', 'MENU', 'Menu', 'Special']
                             main_episodes = [
                                 f for f in remaining_files 
                                 if not any(kw.lower() in f.name.lower() for kw in special_keywords)
                             ]
                             local_files_count = len(main_episodes) if main_episodes else len(remaining_files)
                             
                             matched_season, match_score = self._match_best_season(
                                 tmdb_info['seasons'], 
                                 target_year, 
                                 local_files_count, 
                                 dir_info.season,
                                 llm_confidence=dir_info.confidence,  # 传递LLM置信度
                                 query_alias=dir_basename
                             )
                             
                             # Get the name of the matched season for logging
                             if matched_season is not None:
                                 for s in tmdb_info['seasons']:
                                     if s.get('season_number') == matched_season:
                                         matched_season_name = s.get('name', '')
                                         break
                        
                        # Determine correct season number to use
                        season_num = matched_season if matched_season is not None else (dir_info.season or 1)

                        if matched_season is not None:
                            if matched_season != dir_info.season:
                                # 只有在 TMDB 证据极强时才覆盖 LLM 分析
                                # 阈值 25: 需要名称匹配(15) + 年份(10) 或 名称(15) + LLM高置信度(15)
                                OVERRIDE_THRESHOLD = 25
                                if match_score >= OVERRIDE_THRESHOLD:
                                    self.add_log(f"智能修正: Season {dir_info.season} -> Season {matched_season} (匹配来源: {matched_season_name or 'TMDB'}, 分数: {match_score})")
                                    dir_info.season = matched_season
                                    season_num = matched_season
                                else:
                                    self.add_log(f"保留 LLM 分析: Season {dir_info.season} (TMDB 建议 Season {matched_season}, 置信度不足: {match_score}/{OVERRIDE_THRESHOLD})")
                                    season_num = dir_info.season or 1
                            else:
                                self.add_log(f"智能匹配确认: Season {matched_season} ({matched_season_name})")
                        else:
                            # Fallback to LLM with Context
                            self.add_log(f"本地规则无法确定季度，请求 LLM 进行上下文分析...", "info")
                            file_names = [f.name for f in remaining_files]
                            llm_match = await LLMEngine.identify_season_with_context(file_names, tmdb_info['seasons'])
                            
                            if llm_match and llm_match.get('confidence', 0) > 0.6:
                                llm_season = llm_match.get('best_match_season')
                                reason = llm_match.get('reasoning')
                                self.add_log(f"LLM 上下文匹配: Season {llm_season} (置信度: {llm_match.get('confidence')})")
                                self.add_log(f"LLM 推理: {reason}")
                                
                                matched_season = llm_season
                                season_num = llm_season # Update the one used for renaming
                                
                                # Update display name if possible
                                for s in tmdb_info['seasons']:
                                    if s.get('season_number') == matched_season:
                                        matched_season_name = s.get('name', '')
                                        break
                            else:
                                self.add_log(f"LLM 也无法确定季度，使用默认或原始猜测: Season {season_num}", "warning")
                        
                        season_display = f"Season {season_num}"
                        if matched_season_name:
                            season_display += f" : {matched_season_name}"
                        
                        print(f"  [Match] {season_display} (TMDB: {best_candidate.name})")

                        # Get base image URL configuration
                        tmdb_config = await self.tmdb_service.get_configuration()
                        base_url = tmdb_config.get('images', {}).get('secure_base_url', 'https://image.tmdb.org/t/p/')
                        
                        # Extract poster/backdrop paths from the show details
                        poster_path = tmdb_info.get('poster_path')
                        backdrop_path = tmdb_info.get('backdrop_path')
                        
                        # If we matched a specific season, try to get season-specific poster
                        if matched_season is not None:
                             for s in tmdb_info['seasons']:
                                 if s.get('season_number') == matched_season and s.get('poster_path'):
                                     poster_path = s.get('poster_path')
                                     break

                        # Step 4: Batch rename all files in directory

                        # Step 4: Batch rename all files in directory
                        files_for_llm = []
                        
                        # Pre-scan for Specials (Season 0) to resolve collisions
                        special_files = []
                        tmdb_specials = []
                        if tmdb_info and 'seasons' in tmdb_info:
                             tmdb_specials = [s for s in tmdb_info['seasons'] if s.get('season_number') == 0]
                             # Usually 'seasons' in get_tv_details result gives a summary. 
                             # We might need to fetch Season 0 details explicitly IF the summary lacks episode list.
                             # Actually 'seasons' list in TV details usually DOESN'T contain episode list.
                             # We need to fetch season details if we want to do episode matching.
                             pass

                        # If we have potential specials, lets fetch Season 0 details
                        # Or, check if we have season 0 results from existing tmdb_info?
                        # TMDB TV Details 'seasons' is just a list of season metadata (episode_count, etc), NOT episodes.
                        # We need to fetch specific season details to get episode names.
                        
                        # Let's do a quick pass to see if we have Season 0 files
                        potential_specials = []
                        for f in remaining_files:
                             _, s, _, f_type = FilenameParser.extract_anime_info(f.name)
                             # Identify if it maps to Season 0
                             s_num = s if s is not None else (dir_info.season or 1)
                             if s_num == 0 or f_type in ["ova", "special"]: # CMs usually don't map to S0 in TMDB unless explicit
                                 potential_specials.append(f.name)
                        
                        special_mappings = {}
                        if potential_specials:
                             self.add_log(f"检测到 {len(potential_specials)} 个特别篇 (Specials) 文件，正在获取详细元数据...", "info")
                             # Fetch Season 0 details specifically
                             s0_details = await self.tmdb_service.get_season_details(best_candidate.id, 0)
                             if s0_details and 'episodes' in s0_details:
                                 self.add_log(f"正在使用 LLM 匹配 Season 0 剧集 (OVA/SP)...")
                                 special_mappings = await LLMEngine.identify_specials_with_context(potential_specials, s0_details['episodes'])
                                 self.add_log(f"Specials 匹配结果: {len(special_mappings)} 个文件已定位")

                        for file_node in remaining_files:
                            # Extract episode number from filename
                            _, season_extracted, episode, file_type = FilenameParser.extract_anime_info(file_node.name)
                            
                            if episode is not None:
                                # Use TMDB title + extracted episode
                                # Priority: File specific season > Directory season > Default 1
                                # Note: season can be 0 (Specials), so check for None explicitly
                                season_num = season_extracted if season_extracted is not None else (dir_info.season or 1)
                                
                                # Folder structure logic
                                season_folder = f"Season {season_num:02d}"
                                final_filename = ""
                                
                                # Special Handling (OVA, CM, etc)
                                if file_type in ["ova", "cm", "pv", "nc", "special"] or season_num == 0:
                                    # Target Folder Logic
                                    if file_type == "ova" or season_num == 0:
                                        target_folder = os.path.join("OVA", f"Season {matched_season if matched_season else (dir_info.season or 1):02d}")
                                    elif file_type in ["cm", "pv", "nc"]:
                                        target_folder = os.path.join(file_type.upper(), f"Season {matched_season if matched_season else (dir_info.season or 1):02d}")
                                    else:
                                        target_folder = season_folder # Fallback

                                    # Naming Logic
                                    # 1. Try LLM Matching first
                                    if file_node.name in special_mappings and special_mappings[file_node.name] is not None:
                                         corrected_ep = special_mappings[file_node.name]
                                         self.add_log(f"Specials 智能修正: {file_node.name} -> S00E{corrected_ep:02d}")
                                         final_filename = f"{best_candidate.name} - S00E{corrected_ep:02d}.mkv"
                                         season_num = 0
                                    else:
                                         # 2. Fallback: formatted name with type
                                         # Does not map to TMDB S00Exx, so avoid S00Exx collision
                                         # e.g. "Title - Season 02 OVA01.mkv" or "Title - Season 02 CM01.mkv"
                                         # Use the season it belongs to (matched_season or dir_season), not 0
                                         display_season = matched_season if matched_season else (dir_info.season or 1)
                                         type_label = file_type.upper()
                                         final_filename = f"{best_candidate.name} - S{display_season:02d} {type_label}{episode:02d}.mkv"

                                else:
                                    # Standard Episode
                                    target_folder = season_folder
                                    final_filename = f"{best_candidate.name} - S{season_num:02d}E{episode:02d}.mkv"

                                # Construct Archiving Path: [Initial]/[Title]/[SeasonFolder]
                                initial_folder = self._get_initial(best_candidate.name)
                                title_folder = best_candidate.name
                                
                                # Use `target_folder` which is "Season X" or "OVA/Season X"
                                relative_structure = os.path.join(initial_folder, title_folder, target_folder)
                                
                                # 使用目标媒体库路径作为目标根目录
                                destination_root = dir_path
                                if hasattr(self, 'target_library_path') and self.target_library_path:
                                    destination_root = self.target_library_path
                                
                                new_full_path = os.path.join(destination_root, relative_structure, final_filename)
                                
                                display_path_str = os.path.join(initial_folder, title_folder, target_folder, final_filename).replace("\\", "/")
                                plan.append(RenameItem(
                                    original_path=os.path.join(dir_path, file_node.name),
                                    new_path=new_full_path,
                                    anime_info={
                                        "title": best_candidate.name,
                                        "year": best_candidate.year,
                                        "poster": f"{base_url}w500{poster_path}" if poster_path else None,
                                        "backdrop": f"{base_url}original{backdrop_path}" if backdrop_path else None,
                                        "tmdb_id": best_candidate.id,
                                        "season": season_num
                                    },
                                    display_path=display_path_str
                                ))
                                self.add_log(f"✓ 批量重命名: {file_node.name} -> {target_folder}/{final_filename}", "success")
                            else:
                                files_for_llm.append(file_node)
                        
                        # Pre-filter: Move known "Extra" type files to 'Other' folder to avoid bad renaming
                        # Keywords: Event, Menu, Collection, IV, PV, CM, NC, Scan, CD, NCOP, NCED
                        # Only if they were NOT already handled by FilenameParser (which handles simple CM/PV/NC)
                        EXTRA_KEYWORDS = ['Event', 'Menu', 'Collection', 'IV', 'PV', 'CM', 'NC', 'Scan', 'CD', 'OAD', 'NCOP', 'NCED', 'SP']
                        filtered_files_for_llm = []
                        
                        for file_node in files_for_llm:
                            is_extra = False
                            for kw in EXTRA_KEYWORDS:
                                if kw.lower() in file_node.name.lower():
                                    is_extra = True
                                    break
                            
                            if is_extra:
                                # Move to Other folder
                                # Path: [Initial]/[Title]/Other/Season X/[OriginalName]
                                
                                # Determine Season
                                target_season = matched_season if matched_season is not None else (dir_info.season or 1)
                                
                                initial_folder = self._get_initial(best_candidate.name)
                                season_folder = f"Season {target_season:02d}"
                                
                                # Use 'Other' as the category folder
                                relative_structure = os.path.join(initial_folder, best_candidate.name, "Other", season_folder)
                                
                                destination_root = self.target_library_path if hasattr(self, 'target_library_path') and self.target_library_path else dir_path
                                
                                new_full_path = os.path.join(destination_root, relative_structure, file_node.name)
                                display_path_str = os.path.join(initial_folder, best_candidate.name, "Other", season_folder, file_node.name).replace("\\", "/")
                                
                                plan.append(RenameItem(
                                    original_path=os.path.join(dir_path, file_node.name),
                                    new_path=new_full_path,
                                    anime_info={
                                        "title": best_candidate.name,
                                        "year": best_candidate.year,
                                        "poster": f"{base_url}w500{poster_path}" if poster_path else None,
                                        "backdrop": f"{base_url}original{backdrop_path}" if backdrop_path else None,
                                        "tmdb_id": best_candidate.id,
                                        "season": target_season
                                    },
                                    display_path=display_path_str
                                ))
                                self.add_log(f"✓ 归档至 Other: {file_node.name} -> Other/{season_folder}/{file_node.name}", "success")
                            else:
                                filtered_files_for_llm.append(file_node)
                                
                        files_for_llm = filtered_files_for_llm
                        
                        # Handle files that regex failed to parse using LLM
                        if files_for_llm:
                            self.add_log(f"⚠ 正则解析失败 {len(files_for_llm)} 个文件，尝试使用 LLM 分析...", "warning")
                            try:
                                payload = AnimeNamingPayload(
                                    context=Context(),
                                    anime_candidates=AnimeCandidates(title=best_candidate.name, year=best_candidate.year),
                                    files=files_for_llm
                                )
                                
                                llm_results = await LLMEngine.analyze(payload)
                                
                                for res in llm_results.results:
                                    # Find matching file node for correct path
                                    original_file = next((f for f in files_for_llm if f.name == res.original_name), None)
                                    if not original_file:
                                        self.add_log(f"⚠ LLM 返回了未知的文件名: {res.original_name}", "error")
                                        continue

                                    # Use TMDB Info + LLM Parsed Season/Episode
                                    # Trust LLM season if it deviates? Or force dir_info season?
                                    # Let's verify: if LLM season is widely different, maybe warn?
                                    # For now, trust LLM parsed episode, but use dir_info season if available preference
                                    
                                    # Fix: res.season can be 0, check for None
                                    season_num = res.season if res.season is not None else (dir_info.season or 1)
                                    episode_num = res.episode
                                    
                                    
                                    new_filename = f"{best_candidate.name} - S{season_num:02d}E{episode_num:02d}.mkv"
                                    
                                    # [Modify] LLM Path Construction with Initial Grouping
                                    initial = self._get_initial(best_candidate.name)
                                    
                                    # Fallback Logic for folder structure
                                    if season_num == 0:
                                        # It matches S0 (Special/OVA)
                                        target_season = matched_season if matched_season else (dir_info.season or 1)
                                        season_folder = os.path.join("OVA", f"Season {target_season:02d}")
                                    else:
                                        season_folder = f"Season {season_num}"
                                        
                                    new_full_path = os.path.join(self.target_library_path, initial, best_candidate.name, season_folder, new_filename)
                                    plan.append(RenameItem(
                                        original_path=os.path.join(dir_path, original_file.name),
                                        new_path=new_full_path
                                    ))
                                    self.add_log(f"🤖 LLM 识别: {original_file.name} -> {new_filename}", "success")
                                    
                            except Exception as e:
                                self.add_log(f"✗ LLM 分析失败: {str(e)}", "error")
                                import traceback
                                traceback.print_exc()
                    else:
                        self.add_log(f"⚠ TMDB 未找到匹配: {dir_info.anime_title}", "warning")
                        self.add_log(f"跳过该目录的 {len(remaining_files)} 个文件")
                        
                except Exception as e:
                    self.add_log(f"⚠ TMDB 搜索失败: {str(e)}", "warning")
                    self.add_log(f"跳过该目录的 {len(remaining_files)} 个文件")
                # Process Subtitles for this directory
                # Process Subtitles for this directory
                self._process_subtitles(dir_path, subtitle_files, plan)

            else:
                # Low confidence or not single anime - skip for now
                self.add_log(f"⚠ 目录分析置信度较低或包含多部动漫，跳过 {len(remaining_files)} 个文件", "warning")

        self.add_log(f"扫描完成！生成 {len(plan)} 个重命名计划", "success")
        self.current_plan = plan
        return plan

    def get_current_plan(self) -> List[RenameItem]:
        """获取当前计划"""
        return self.current_plan

    def execute_plan(self, plan: List[RenameItem]):
        for item in plan:
            try:
                # Make sure dir exists (renaming might include moving folders)
                os.makedirs(os.path.dirname(item.new_path), exist_ok=True)
                
                shutil.move(item.original_path, item.new_path)
                item.status = "done"
                self.journal.append(item)
            except Exception as e:
                item.status = "error"
                item.log = str(e)
                # Stop on error? Or continue?
                # For safety, maybe stop?
    
    def rollback(self):
        for item in reversed(self.journal):
            if item.status == "done":
                try:
                    shutil.move(item.new_path, item.original_path)
                except Exception as e:
                    print(f"Rollback failed for {item.new_path}: {e}")
        self.journal.clear()

    def _match_best_season(self, seasons_info: List[dict], target_year: Optional[int], local_files_count: int, llm_suggested_season: Optional[int], llm_confidence: float = 0.0, query_alias: str = "") -> Tuple[Optional[int], float]:
        """
        智能匹配最佳季度，基于多重因素评分。
        Returns (season_number, score)
        """
        candidates_score = {}
        
        # 关键词检测 - 明确的季度标识
        season_keywords = {
            'kan': ['完', 'kan', 'final'],
            'zoku': ['続', 'zoku', 'second'],
            'san': ['参', 'san', 'third'],
            'kai': ['改', 'kai', 'rebuild']
        }

        for season in seasons_info:
            if season.get('season_number') == 0 and not isinstance(llm_suggested_season, int):
                continue

            s_num = season.get('season_number')
            s_name = season.get('name', '')
            score = 0
            
            # 1. 年份匹配 (+10)
            air_date = season.get('air_date')
            if air_date and target_year:
                try:
                    s_year = int(air_date.split('-')[0])
                    if abs(s_year - target_year) <= 1:
                        score += 10
                        if s_year == target_year:
                            score += 2  # 精确年份额外加分
                except:
                    pass
            
            # 2. 集数匹配 (+8)
            ep_count = season.get('episode_count')
            if ep_count and local_files_count > 0:
                diff = abs(ep_count - local_files_count)
                if diff == 0:
                    score += 8
                elif diff <= 2:  # 容错 ±2 集
                    score += 4
            
            # 3. 名称匹配 (+15 - 最强证据)
            if query_alias and s_name:
                query_lower = query_alias.lower()
                name_lower = s_name.lower()
                if len(s_name) > 2 and name_lower in query_lower:
                    score += 15
            
            # 4. LLM 匹配权重（根据置信度动态调整）
            if llm_suggested_season is not None and s_num == llm_suggested_season:
                if llm_confidence >= 0.9:
                    score += 15  # 极高置信度
                elif llm_confidence >= 0.8:
                    score += 10  # 高置信度
                elif llm_confidence >= 0.7:
                    score += 5   # 中等置信度
                else:
                    score += 3   # 低置信度
            
            # 5. 关键词加成 (+5)
            if query_alias:
                query_lower = query_alias.lower()
                for keyword_type, keywords in season_keywords.items():
                    for kw in keywords:
                        if kw in query_lower:
                            # 根据季度数匹配关键词
                            if (keyword_type == 'kan' and s_num == 3) or \
                               (keyword_type == 'zoku' and s_num == 2) or \
                               (keyword_type == 'san' and s_num == 3):
                                score += 5
                                break

            candidates_score[s_num] = score
        
        if not candidates_score:
            return None, 0.0
            
        best_season = max(candidates_score.items(), key=lambda x: x[1])
        return best_season[0], best_season[1]

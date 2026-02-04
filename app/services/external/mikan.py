
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Optional
from loguru import logger
import re
import html

class MikanService:
    BASE_URL = "https://mikanani.me"
    
    def search(self, keyword: str) -> List[dict]:
        """搜索番剧，返回结果列表"""
        url = f"{self.BASE_URL}/Home/Search"
        params = {"searchstr": keyword}
        
        try:
            # Mikan search page returns HTML
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            
            # This depends on Mikan's HTML structure.
            # Usually search results are in a list.
            # Updated structure check needed.
            # Example: .an-ul -> li -> 
            #   Img: .an-img
            #   Title: .an-text
            
            # Recent Mikan structure might list torrents directly if keyword matches many,
            # but usually it shows Bangumi list if mapped.
            # Let's target the Bangumi list structure often found in "/Home/Search"
            
            # Check for Bangumi list
            bangumi_list = soup.select(".an-ul li")
            for item in bangumi_list:
                 try:
                     # Robustly find the Bangumi link
                     link_tag = item.select_one("a[href*='/Home/Bangumi/']")
                     if not link_tag:
                         continue
                         
                     href = link_tag.get('href') # /Home/Bangumi/228
                     mikan_id = href.split("/")[-1]
                     
                     # Title might be on the a tag or inside a span/div
                     title = link_tag.get('title')
                     if not title:
                         # Try finding text element inside
                         text_el = item.select_one(".an-text") or link_tag
                         title = text_el.text.strip()
                     
                     # Cover image
                     cover_url = ""
                     
                     # Priority 1: .an-img (it's often a div with data-src)
                     an_img = item.select_one(".an-img")
                     if an_img:
                         cover_url = an_img.get('data-src') or an_img.get('src')
                     
                     # Priority 2: Any img tag
                     if not cover_url:
                         img = item.select_one("img")
                         if img:
                            cover_url = img.get('data-src') or img.get('src')
                            
                     # Priority 3: Any element with data-src
                     if not cover_url:
                         ds = item.select_one("[data-src]")
                         if ds:
                             cover_url = ds.get('data-src')

                     if cover_url and not cover_url.startswith("http"):
                         cover_url = f"{self.BASE_URL}{cover_url}"
                             
                     results.append({
                         "mikan_id": mikan_id,
                         "title": title,
                         "cover_url": cover_url
                     })
                 except Exception as e:
                     logger.warning(f"Error parsing mikan search item: {e}")
                     continue
            
            return results

        except Exception as e:
            logger.error(f"Failed to search mikan: {e}")
            return []

    def get_bangumi_detail(self, mikan_id: str) -> dict:
        """获取番剧详情，包括字幕组列表"""
        url = f"{self.BASE_URL}/Home/Bangumi/{mikan_id}"
        
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            
            # User reported needed to unescape HTML entities first
            raw_html = html.unescape(resp.text)
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Get Banner/Info (Optional)
            
            # Get Subgroups
            # Subgroups are usually listed in tabs or dropdowns
            # Structure: .subgroup-text (the subtitle group name)
            # data-subgroupid attribute on elements
            
            subgroups = []
            
            # Mikan structure: often tabs for subgroups
            # <a href="#" data-subgroupid="123" ...>Subgroup Name</a>
            
            # Wrapper for subgroups. 
            # Robust subgroup parsing strategy
            # Mikan's detail page lists subgroups in .subgroup-text divs.
            # Usually: <div class="subgroup-text" id="123"> <a ...>Name</a> ... </div>
            
            name_elements = soup.select(".subgroup-text")
            
            seen_ids = set()
            
            for el in name_elements:
                # 1. Try to get ID from element 'id' or 'data-subgroupid'
                sg_id = el.get('id')
                if not sg_id:
                     sg_id = el.get('data-subgroupid')
                
                if not sg_id:
                    continue
                
                # 2. Try to get Name
                # Usually in the first <a> tag with href pointing to /Home/PublishGroup
                name_link = el.select_one("a[href*='/Home/PublishGroup']")
                if name_link:
                    name = name_link.text.strip()
                else:
                    # Fallback: get text but exclude subscribe buttons/junk
                    # Usually the first line of text
                    name = el.text.split("\n")[0].strip()
                    if not name:
                         # Last resort, full text
                         name = el.text.strip()

                if not name:
                    continue

                if sg_id not in seen_ids:
                    subgroups.append({
                        "id": sg_id,
                        "name": name,
                        "latest_episode": "",
                        "latest_date": "",
                        "videos": []
                    })
                    seen_ids.add(sg_id)
            
            # Fallback for sidebar
            if not subgroups:
                 links = soup.select(".leftbar-nav .subgroup-name")
                 for link in links:
                     data_anchor = link.get('data-anchor')
                     if data_anchor and data_anchor.startswith('#'):
                         sg_id = data_anchor[1:]
                         name = link.text.strip()
                         if sg_id and name and sg_id not in seen_ids:
                             subgroups.append({
                                 "id": sg_id,
                                 "name": name,
                                 "latest_episode": "",
                                 "latest_date": "",
                                 "videos": []
                             })
                             seen_ids.add(sg_id)

            # --- Parse Video Tables to find latest episode and populate video list ---
            # Map name -> subgroup item for easier lookup
            # Using simple contains match as per debug strategy
            
            table_rows = soup.select("table.table-striped.tbl-border.fadeIn tbody tr")
            
            # Helper to extract episode number from title (simple regex)
            ep_pattern = re.compile(r'\[(\d{2})\]|第(\d{1,3})[话話集]| - (\d{1,3})(?: |$)', re.IGNORECASE)
            
            for row in table_rows:
                title_link = row.select_one(".magnet-link-wrap")
                if not title_link: continue
                title = title_link.text.strip()
                
                cols = row.select("td")
                pub_date = ""
                size = ""
                if len(cols) >= 4:
                    size = cols[2].text.strip()
                    pub_date = cols[3].text.strip()
                
                # Find matching subgroups
                for sg in subgroups:
                    if sg["name"] in title:
                        # Add video to list
                        sg["videos"].append({
                            "title": title,
                            "size": size,
                            "pub_date": pub_date
                        })

                        # Logic for latest episode (only if not found yet)
                        if not sg["latest_episode"]:
                            # Found a match!
                            # Extract episode number
                            ep_str = "Unknown"
                            match = ep_pattern.search(title)
                            if match:
                                # pattern groups: 1=[01], 2=第1话, 3= - 01
                                ep_str = next((g for g in match.groups() if g), "New")
                                # Add 'Ep ' prefix if just a number
                                if ep_str.isdigit():
                                    ep_str = f"Ep {ep_str}"
                            else:
                                # Try date
                                ep_str = pub_date.split(' ')[0] if pub_date else "Update"

                            sg["latest_episode"] = ep_str
                            sg["latest_date"] = pub_date
            
            # Also extract title just in case
            title = "Unknown"
            title_el = soup.select_one(".bangumi-title")
            if title_el:
                title = title_el.text.strip()
            
            # Extract cover from detail page
            cover_url = ""
            poster_el = soup.select_one(".bangumi-poster")
            if poster_el:
                style = poster_el.get("style", "")
                if "url('" in style:
                    cover_url = style.split("url('")[1].split("')")[0]
                elif "url(" in style:
                    cover_url = style.split("url(")[1].split(")")[0]
            
            # Fallback: if no poster style, look for img in bangumi-poster
            if not cover_url and poster_el:
                 img_in_poster = poster_el.select_one("img")
                 if img_in_poster:
                     cover_url = img_in_poster.get("src") or ""
            
            if cover_url and not cover_url.startswith("http"):
                 cover_url = f"{self.BASE_URL}{cover_url}"

            # Filter out subgroups with no videos (User Request)
            subgroups = [sg for sg in subgroups if sg["videos"]]

            return {
                "mikan_id": mikan_id,
                "title": title,
                "cover_url": cover_url,
                "subgroups": subgroups
            }

        except Exception as e:
            logger.error(f"Failed to get bangumi detail: {e}")
            return {}

    def get_rss_url(self, mikan_id: str, subgroup_id: str = None) -> str:
        """生成 RSS 订阅链接"""
        # https://mikanani.me/RSS/Bangumi?bangumiId=3405&subgroupid=615
        url = f"{self.BASE_URL}/RSS/Bangumi?bangumiId={mikan_id}"
        if subgroup_id:
            url += f"&subgroupid={subgroup_id}"
        return url

    def parse_rss(self, rss_url: str) -> List[dict]:
        """解析 RSS feed，返回条目列表"""
        try:
            logger.info(f"Fetching RSS: {rss_url}")
            # Use requests with timeout to prevent hanging
            resp = requests.get(rss_url, timeout=30)
            resp.raise_for_status()
            
            feed = feedparser.parse(resp.content)
            items = []
            
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"Feed parsing warning: {feed.bozo_exception}")
            
            for entry in feed.entries:
                torrent_url = None
                magnet = None
                
                # Check standard enclosure for torrent file
                for link in entry.get('links', []):
                    if link.get('type') == 'application/x-bittorrent':
                        torrent_url = link.get('href')
                        
                # Some feeds put magnet in link
                if entry.get('link', '').startswith("magnet:"):
                    magnet = entry.link
                    
                items.append({
                    "guid": entry.get('guid', entry.get('link')), # Fallback to link if guid missing
                    "title": entry.title,
                    "link": entry.link,
                    "torrent_url": torrent_url,
                    "magnet": magnet, 
                    # published_parsed returns time.struct_time
                    "pub_date": entry.get('published_parsed')
                })
            
            logger.info(f"Parsed {len(items)} items from RSS")
            return items
            
        except Exception as e:
            logger.error(f"Failed to parse RSS: {e}")
            return []

    def extract_magnet(self, item: dict) -> str:
        """从 RSS 条目中提取磁力链接"""
        # Placeholder if we need to extract from description or fetch page
        pass

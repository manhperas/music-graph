"""Award extraction from Wikipedia artist pages"""

import json
import os
import re
import time
from typing import List, Dict, Optional, Set
import wikipediaapi
import mwparserfromhell
import requests
import pandas as pd

# Import utilities from parent directory
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_collection.utils import logger, rate_limit, log_progress, clean_text


class AwardExtractor:
    """Extract awards from Wikipedia artist pages"""
    
    # Major awards to focus on
    MAJOR_AWARDS = {
        'grammy': {
            'patterns': [
                r'grammy\s+(?:award|awards|music\s+awards?)?',
                r'grammy\s+nomination',
                r'grammy\s+win',
            ],
            'ceremony': 'Grammy Awards',
            'aliases': ['grammy', 'grammy awards', 'grammys']
        },
        'billboard': {
            'patterns': [
                r'billboard\s+(?:music\s+)?awards?',
                r'billboard\s+music\s+award',
                r'billboard\s+nomination',
            ],
            'ceremony': 'Billboard Music Awards',
            'aliases': ['billboard', 'billboard music awards', 'bma']
        },
        'mtv': {
            'patterns': [
                r'mtv\s+(?:video\s+music\s+)?awards?',
                r'mtv\s+vma',
                r'mtv\s+music\s+award',
                r'mtv\s+nomination',
            ],
            'ceremony': 'MTV Video Music Awards',
            'aliases': ['mtv', 'mtv video music awards', 'vma', 'mtv vma']
        },
        'brit': {
            'patterns': [
                r'brit\s+awards?',
                r'brit\s+award',
                r'british\s+record\s+industry\s+awards?',
            ],
            'ceremony': 'Brit Awards',
            'aliases': ['brit', 'brit awards', 'british awards']
        },
        'ama': {
            'patterns': [
                r'american\s+music\s+awards?',
                r'ama\s+(?:awards?|nomination)',
                r'ama\s+win',
            ],
            'ceremony': 'American Music Awards',
            'aliases': ['ama', 'american music awards', 'american music award']
        }
    }
    
    def __init__(self, language: str = 'vi'):
        """Initialize award extractor"""
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='MusicNetworkProject/1.0 (test@example.com)',
            language=language
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MusicNetworkProject/1.0 (test@example.com)'
        })
        self.extracted_awards: Dict[str, List[Dict]] = {}  # artist_name -> [awards]
        
    def _extract_infobox(self, page_title: str) -> str:
        """Extract infobox wikitext using MediaWiki API"""
        try:
            url = f"https://{self.wiki.language}.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'prop': 'revisions',
                'rvprop': 'content',
                'rvslots': 'main',
                'titles': page_title,
                'format': 'json',
                'formatversion': 2
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', [])
            if not pages:
                return ""
            
            content = pages[0].get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
            
            # Parse wikitext to find infobox
            wikicode = mwparserfromhell.parse(content)
            for template in wikicode.filter_templates():
                template_name = str(template.name).strip().lower()
                if 'infobox' in template_name or 'hộp thông tin' in template_name:
                    return str(template)
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting infobox for {page_title}: {e}")
            return ""
    
    def _extract_awards_from_infobox(self, infobox_text: str) -> List[Dict]:
        """Extract awards from artist infobox"""
        awards = []
        if not infobox_text:
            return awards
        
        try:
            wikicode = mwparserfromhell.parse(infobox_text)
            templates = wikicode.filter_templates()
            
            if not templates:
                return awards
            
            template = templates[0]
            award_patterns = ['award', 'awards', 'giải thưởng', 'nominations']
            
            for param in template.params:
                param_name = str(param.name).strip().lower()
                param_value = str(param.value).strip()
                
                if any(pattern in param_name for pattern in award_patterns):
                    # Parse awards from infobox
                    parsed_awards = self._parse_award_text(param_value)
                    awards.extend(parsed_awards)
        
        except Exception as e:
            logger.debug(f"Error extracting awards from infobox: {e}")
        
        return awards
    
    def _parse_award_text(self, award_text: str) -> List[Dict]:
        """Parse award text into structured award data"""
        awards = []
        if not award_text:
            return awards
        
        # Clean wiki markup
        award_text = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', award_text)
        award_text = re.sub(r"'''?([^']+)'''?", r'\1', award_text)
        award_text = re.sub(r'<[^>]+>', '', award_text)
        award_text = re.sub(r'<ref[^>]*>.*?</ref>', '', award_text, flags=re.DOTALL)
        award_text = clean_text(award_text)
        
        # Split by common separators
        lines = re.split(r'\n|•|;|\||<br\s*/?>', award_text)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to match major awards
            award = self._parse_award_line(line)
            if award:
                awards.append(award)
        
        return awards
    
    def _parse_award_line(self, line: str) -> Optional[Dict]:
        """Parse a single award line into structured data"""
        if not line or len(line.strip()) < 3:
            return None
        
        line_lower = line.lower()
        
        # Check if line contains any major award
        award_type = None
        ceremony = None
        
        for award_key, award_info in self.MAJOR_AWARDS.items():
            for pattern in award_info['patterns']:
                if re.search(pattern, line_lower, re.IGNORECASE):
                    award_type = award_key
                    ceremony = award_info['ceremony']
                    break
            if award_type:
                break
        
        if not award_type:
            # Not a major award, skip
            return None
        
        # Extract year (4-digit year pattern)
        year = None
        year_match = re.search(r'\b(19|20)\d{2}\b', line)
        if year_match:
            year = int(year_match.group())
        
        # If no year found, try to extract from Vietnamese patterns
        if not year:
            # Vietnamese year patterns: "năm 2020", "2020", "từ 2020"
            year_patterns = [
                r'năm\s+(19|20)\d{2}',
                r'(?:^|\s)(19|20)\d{2}(?:\s|$)',
                r'từ\s+(19|20)\d{2}',
            ]
            for pattern in year_patterns:
                year_match = re.search(pattern, line, re.IGNORECASE)
                if year_match:
                    year_str = year_match.group(1) if year_match.group(1) else year_match.group(0)
                    if len(year_str) == 4:
                        year = int(year_str)
                    elif len(year_str) == 2:
                        # Try to infer full year
                        full_year = int('20' + year_str) if int(year_str) < 50 else int('19' + year_str)
                        year = full_year
                    break
        
        # Extract category (between award name and year, or after "for")
        category = None
        category_patterns = [
            r'(?:for|cho|với)\s+([^0-9]+?)(?:\s+\d{4}|\s*$)',  # "for Best Album 2020"
            r'(?:best|tốt nhất|giải|award)\s+([^0-9]+?)(?:\s+\d{4}|\s*$)',  # "Best Album 2020"
            r'(?:album|song|artist|record|video)\s+of\s+the\s+year',  # "Album of the Year"
        ]
        
        for pattern in category_patterns:
            cat_match = re.search(pattern, line, re.IGNORECASE)
            if cat_match:
                category = clean_text(cat_match.group(1))
                # Clean up category
                category = re.sub(r'^(for|cho|với|best|tốt nhất|giải|award)\s+', '', category, flags=re.IGNORECASE)
                category = clean_text(category)
                break
        
        # If no category found, try to extract from common patterns
        if not category:
            # Look for common category keywords
            category_keywords = ['album', 'song', 'artist', 'record', 'video', 'single', 'performance']
            for keyword in category_keywords:
                if keyword in line_lower:
                    # Try to extract full category phrase
                    cat_match = re.search(rf'({keyword}[^0-9]+?)(?:\s+\d{{4}}|\s*$)', line, re.IGNORECASE)
                    if cat_match:
                        category = clean_text(cat_match.group(1))
                        break
            
            # Default category if still not found
            if not category:
                category = 'General'
        
        # Extract status (won vs nominated)
        status = 'nominated'  # Default
        won_patterns = [
            r'\bwon\b',
            r'\bwin\b',
            r'\bwinner\b',
            r'\bđoạt\b',
            r'\bthắng\b',
            r'\bgiành\b',
        ]
        nominated_patterns = [
            r'\bnominated\b',
            r'\bnomination\b',
            r'\bđề cử\b',
            r'\bcử\b',
        ]
        
        for pattern in won_patterns:
            if re.search(pattern, line_lower, re.IGNORECASE):
                status = 'won'
                break
        
        if status == 'nominated':
            for pattern in nominated_patterns:
                if re.search(pattern, line_lower, re.IGNORECASE):
                    status = 'nominated'
                    break
        
        # Clean up category
        category = clean_text(category)
        if len(category) > 100:
            category = category[:100]
        
        # Create award object
        award = {
            'ceremony': ceremony,
            'category': category,
            'year': year,
            'status': status,
            'raw_text': line[:200]  # Keep original text for reference
        }
        
        return award
    
    def _extract_awards_section(self, page_text: str) -> List[Dict]:
        """Extract awards from 'Awards and nominations' section"""
        awards = []
        
        if not page_text:
            return awards
        
        # Find Awards and nominations section
        # Vietnamese: "Giải thưởng và đề cử", "Giải thưởng"
        # English: "Awards and nominations", "Awards"
        section_patterns = [
            r'==\s*(?:Awards\s+and\s+nominations|Giải thưởng và đề cử|Giải thưởng|Awards)\s*==',
            r'===\s*(?:Awards\s+and\s+nominations|Giải thưởng và đề cử|Giải thưởng|Awards)\s*===',
            r'==\s*(?:Award|Giải)\s*==',
            r'===\s*(?:Award|Giải)\s*===',
        ]
        
        section_start = -1
        for pattern in section_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                section_start = match.end()
                break
        
        # Also try to find any section mentioning awards
        if section_start == -1:
            all_section_patterns = [
                r'==\s*([^=]+?)\s*==',
                r'===\s*([^=]+?)\s*===',
            ]
            
            for pattern in all_section_patterns:
                matches = list(re.finditer(pattern, page_text, re.IGNORECASE))
                for match in matches:
                    section_title = match.group(1).strip().lower()
                    if any(keyword in section_title for keyword in ['giải', 'award', 'nomination', 'đề cử']):
                        section_start = match.end()
                        logger.debug(f"    → Found potential award section: {match.group(1)}")
                        break
                if section_start != -1:
                    break
        
        if section_start == -1:
            logger.debug(f"    → Không tìm thấy awards section")
            return awards
        
        logger.debug(f"    → Đã tìm thấy awards section tại vị trí {section_start}")
        
        # Extract content until next section (next ==)
        section_end_match = re.search(r'\n==', page_text[section_start:])
        if section_end_match:
            section_text = page_text[section_start:section_start + section_end_match.start()]
        else:
            section_text = page_text[section_start:section_start + 10000]  # Limit to 10000 chars
        
        logger.debug(f"    → Section text: {len(section_text)} chars")
        
        # Parse awards from section
        parsed_awards = self._parse_awards_section_content(section_text)
        awards.extend(parsed_awards)
        logger.debug(f"    → Parsed {len(parsed_awards)} awards từ section")
        
        return awards
    
    def _parse_awards_section_content(self, content: str) -> List[Dict]:
        """Parse awards section content"""
        awards = []
        
        if not content:
            return awards
        
        # First, try to parse table format (common in Vietnamese Wikipedia)
        table_awards = self._parse_wiki_table_awards(content)
        if table_awards:
            awards.extend(table_awards)
            logger.debug(f"    → Extracted {len(table_awards)} awards từ table format")
        
        # Also parse line-by-line format
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip headers, references, etc.
            if line.startswith('==') or line.startswith('!'):
                continue
            
            # Skip empty lines and references
            if re.match(r'^[\s\-\*\|]*$', line) or line.startswith('<ref'):
                continue
            
            # Skip table rows (already parsed above)
            if line.startswith('|') and '|' in line[1:]:
                continue
            
            # Parse award line
            award = self._parse_award_line(line)
            if award:
                awards.append(award)
        
        return awards
    
    def _parse_wiki_table_awards(self, content: str) -> List[Dict]:
        """Parse awards from Wikipedia table format (| format)"""
        awards = []
        
        if not content:
            return awards
        
        # Find table rows: lines starting with | and containing multiple |
        lines = content.split('\n')
        current_year = None
        
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('|'):
                continue
            
            # Skip table headers
            if line.startswith('!') or line.startswith('|!'):
                continue
            
            # Parse table row: | award | category | year |
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            
            if len(cells) < 2:
                continue
            
            # Try to extract year from first cell or context
            year = None
            ceremony = None
            category = None
            
            # Check each cell for award information
            for i, cell in enumerate(cells):
                cell_clean = cell
                # Clean wiki markup
                cell_clean = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', cell_clean)
                cell_clean = re.sub(r"'''?", '', cell_clean)
                cell_clean = clean_text(cell_clean)
                
                # Check if cell contains year
                year_match = re.search(r'\b(19|20)\d{2}\b', cell_clean)
                if year_match:
                    year = int(year_match.group())
                    current_year = year  # Update context year
                
                # Check if cell contains award ceremony
                for award_key, award_info in self.MAJOR_AWARDS.items():
                    for pattern in award_info['patterns']:
                        if re.search(pattern, cell_clean, re.IGNORECASE):
                            ceremony = award_info['ceremony']
                            break
                    if ceremony:
                        break
                
                # Category is usually in second or third cell
                if i == 1 and not ceremony and not category:
                    # This might be the category
                    category = cell_clean
                elif i == 2 and not category:
                    category = cell_clean
            
            # If we found ceremony but no category, try to extract from remaining cells
            if ceremony and not category:
                for cell in cells:
                    cell_clean = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', cell)
                    cell_clean = re.sub(r"'''?", '', cell_clean)
                    cell_clean = clean_text(cell_clean)
                    
                    # Skip if it's the ceremony name itself
                    if any(pattern in cell_clean.lower() for pattern in ['grammy', 'mtv', 'brit', 'billboard', 'ama']):
                        continue
                    
                    # Skip if it's just a year
                    if re.match(r'^\d{4}$', cell_clean):
                        continue
                    
                    # Skip table markup artifacts
                    if any(artifact in cell_clean.lower() for artifact in ['rowspan', 'colspan', 'style=', 'class=', 'align=']):
                        continue
                    
                    # Skip if it's empty or too short
                    if not cell_clean or len(cell_clean) < 3:
                        continue
                    
                    # This might be the category
                    category = cell_clean
                    break
            
            # If no year found, use context year
            if not year and current_year:
                year = current_year
            
            # Create award if we have ceremony
            if ceremony:
                if not category:
                    category = 'General'
                
                # Skip if category is a table artifact
                if any(artifact in category.lower() for artifact in ['rowspan', 'colspan', 'style=', 'class=', 'align=']):
                    continue
                
                award = {
                    'ceremony': ceremony,
                    'category': category,
                    'year': year,
                    'status': 'nominated',  # Default
                    'raw_text': line[:200]
                }
                awards.append(award)
        
        return awards
    
    def _load_seed_artists(self, seed_path: str = "config/seed_artists.json") -> List[str]:
        """Load seed artists from JSON file"""
        try:
            if os.path.exists(seed_path):
                with open(seed_path, 'r', encoding='utf-8') as f:
                    seed_data = json.load(f)
                    seed_list = seed_data.get('seed_artists', [])
                    logger.info(f"Loaded {len(seed_list)} seed artists from {seed_path}")
                    return seed_list
            else:
                logger.warning(f"Seed file not found: {seed_path}")
                return []
        except Exception as e:
            logger.error(f"Error loading seed artists: {e}")
            return []
    
    def _search_wikipedia_page(self, artist_name: str) -> Optional[str]:
        """Search for Wikipedia page with variations if exact match fails"""
        # Try exact match first
        page = self.wiki.page(artist_name)
        if page.exists():
            return artist_name
        
        # Try variations
        variations = [
            f"{artist_name} (singer)",
            f"{artist_name} (musician)",
            f"{artist_name} (artist)",
            artist_name.title(),
            artist_name.lower(),
        ]
        
        for variation in variations:
            page = self.wiki.page(variation)
            if page.exists():
                logger.info(f"  → Found page với variation: '{variation}'")
                return variation
        
        # Try search API
        try:
            url = f"https://{self.wiki.language}.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': artist_name,
                'srlimit': 3,
                'format': 'json',
                'formatversion': 2
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get('query', {}).get('search', [])
            if search_results:
                # Try first result
                first_result = search_results[0].get('title', '')
                if first_result:
                    page = self.wiki.page(first_result)
                    if page.exists():
                        logger.info(f"  → Found page via search: '{first_result}'")
                        return first_result
        except Exception as e:
            logger.debug(f"  Search API error: {e}")
        
        return None
    
    @rate_limit(0.5)
    def extract_awards_from_artist(self, artist_name: str) -> List[Dict]:
        """Extract awards from an artist page"""
        try:
            logger.info(f"  Tìm kiếm trên Wikipedia tiếng Việt: '{artist_name}'")
            
            # Try to find page (with variations if needed)
            logger.debug(f"    → Đang tìm trang Wikipedia...")
            actual_page_name = self._search_wikipedia_page(artist_name)
            
            if not actual_page_name:
                logger.warning(f"  ✗ Không tìm thấy trang Wikipedia cho: '{artist_name}'")
                return []
            
            # Use the actual page name found
            logger.debug(f"    → Đang load trang: '{actual_page_name}'")
            page = self.wiki.page(actual_page_name)
            
            if not page.exists():
                logger.warning(f"  ✗ Trang không tồn tại: '{actual_page_name}'")
                return []
            
            logger.info(f"  ✓ Tìm thấy trang: '{page.title}'")
            logger.debug(f"    URL: {page.fullurl}")
            
            awards = []
            
            # Method 1: Extract from infobox
            logger.debug(f"    → Method 1: Đang extract từ infobox...")
            infobox = self._extract_infobox(actual_page_name)
            if infobox:
                infobox_awards = self._extract_awards_from_infobox(infobox)
                awards.extend(infobox_awards)
                logger.info(f"    ✓ Extracted {len(infobox_awards)} awards từ infobox")
            else:
                logger.debug(f"    ✗ Không tìm thấy infobox")
            
            # Method 2: Extract from Awards and nominations section
            logger.debug(f"    → Method 2: Đang extract từ Awards section...")
            page_text = page.text if hasattr(page, 'text') else page.summary
            if page_text:
                section_awards = self._extract_awards_section(page_text)
                awards.extend(section_awards)
                logger.info(f"    ✓ Extracted {len(section_awards)} awards từ awards section")
            else:
                logger.debug(f"    ✗ Không có page text")
            
            # Also get full wikitext for better parsing
            logger.debug(f"    → Method 3: Đang extract từ full wikitext...")
            try:
                url = f"https://{self.wiki.language}.wikipedia.org/w/api.php"
                params = {
                    'action': 'query',
                    'prop': 'revisions',
                    'rvprop': 'content',
                    'rvslots': 'main',
                    'titles': actual_page_name,
                    'format': 'json',
                    'formatversion': 2
                }
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                pages = data.get('query', {}).get('pages', [])
                if pages:
                    wikitext = pages[0].get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
                    
                    # Parse awards from wikitext more comprehensively
                    wikitext_awards = self._extract_awards_section(wikitext)
                    awards.extend(wikitext_awards)
                    logger.info(f"    ✓ Extracted {len(wikitext_awards)} awards từ wikitext awards section")
                    
                    # Also extract from infobox if not already done
                    if not infobox:
                        infobox = self._extract_infobox(actual_page_name)
                        if infobox:
                            infobox_awards = self._extract_awards_from_infobox(infobox)
                            awards.extend(infobox_awards)
                            logger.info(f"    ✓ Extracted {len(infobox_awards)} awards từ wikitext infobox")
            except Exception as e:
                logger.debug(f"    ✗ Error extracting from wikitext: {e}")
            
            # Deduplicate awards by ceremony, category, and year
            logger.debug(f"    → Đang deduplicate awards (tổng {len(awards)} awards)...")
            unique_awards = []
            seen_awards = set()
            
            for award in awards:
                # Create unique key
                key = (
                    award.get('ceremony', ''),
                    award.get('category', ''),
                    award.get('year', 0),
                    award.get('status', '')
                )
                
                if key not in seen_awards:
                    seen_awards.add(key)
                    unique_awards.append(award)
            
            logger.debug(f"    → Sau deduplicate: {len(unique_awards)} unique awards")
            
            if unique_awards:
                logger.info(f"  ✓ Tìm thấy {len(unique_awards)} awards từ '{page.title}'")
            else:
                logger.warning(f"  ✗ Trang tồn tại nhưng không có major awards: '{page.title}'")
                logger.debug(f"    → Có thể trang không có awards section hoặc không có major awards")
            
            return unique_awards
            
        except Exception as e:
            logger.error(f"  ✗ Error extracting awards from {artist_name}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def extract_awards_from_seed_artists(self, seed_artists: Optional[List[str]] = None,
                                         max_artists: Optional[int] = None) -> Dict[str, List[Dict]]:
        """Extract awards from seed artists
        
        Args:
            seed_artists: List of artist names to process. If None, loads from config
            max_artists: Maximum number of artists to process
        """
        if seed_artists is None:
            seed_artists = self._load_seed_artists()
        
        if not seed_artists:
            logger.warning("No seed artists found. Cannot extract awards.")
            return {}
        
        logger.info(f"Starting award extraction from {len(seed_artists)} seed artists...")
        
        if max_artists:
            seed_artists = seed_artists[:max_artists]
        
        logger.info(f"  → Sẽ extract từ {len(seed_artists)} artists")
        
        results = {}
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        for i, artist_name in enumerate(seed_artists, 1):
            logger.info(f"[{i}/{len(seed_artists)}] Extracting awards from: {artist_name}")
            
            awards = self.extract_awards_from_artist(artist_name)
            
            if awards:
                results[artist_name] = awards
                successful += 1
                logger.info(f"  ✓ Found {len(awards)} awards")
            else:
                failed += 1
                logger.warning(f"  ✗ No awards found")
            
            # Progress update every 5 artists
            if i % 5 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = avg_time * (len(seed_artists) - i)
                log_progress(i, len(seed_artists), "Extracting awards")
                logger.info(f"  Progress: {successful} successful, {failed} failed")
                logger.info(f"  Time: {elapsed/60:.1f}m elapsed, ~{remaining/60:.1f}m remaining")
        
        logger.info("=" * 60)
        logger.info("AWARD EXTRACTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total artists processed: {len(seed_artists)}")
        logger.info(f"Successful: {successful} ({successful/len(seed_artists)*100:.1f}%)")
        logger.info(f"Failed: {failed} ({failed/len(seed_artists)*100:.1f}%)")
        logger.info(f"Total awards extracted: {sum(len(awards) for awards in results.values())}")
        
        if successful > 0:
            avg_awards = sum(len(awards) for awards in results.values()) / successful
            logger.info(f"Average awards per successful artist: {avg_awards:.1f}")
        
        # Award breakdown by ceremony
        ceremony_counts = {}
        for artist_awards in results.values():
            for award in artist_awards:
                ceremony = award.get('ceremony', 'Unknown')
                ceremony_counts[ceremony] = ceremony_counts.get(ceremony, 0) + 1
        
        logger.info("")
        logger.info("Awards by ceremony:")
        for ceremony, count in sorted(ceremony_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {ceremony}: {count}")
        
        if failed > 0:
            logger.warning("")
            logger.warning("Lý do có thể fail:")
            logger.warning("  1. Artist page không tồn tại trên Wikipedia tiếng Việt")
            logger.warning("  2. Artist page tồn tại nhưng không có awards section")
            logger.warning("  3. Không có major awards (chỉ có minor awards)")
            logger.warning("")
        
        return results
    
    def save_awards(self, awards_data: Dict[str, List[Dict]], output_path: str):
        """Save extracted awards to JSON file"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(awards_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved awards data to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving awards: {e}")
            raise


def normalize_award_name(ceremony: str) -> str:
    """Normalize award ceremony name (e.g., 'Grammy Awards' → 'Grammy')"""
    if not ceremony:
        return ""
    
    # Normalization mapping
    normalization_map = {
        'grammy awards': 'Grammy',
        'billboard music awards': 'Billboard',
        'mtv video music awards': 'MTV',
        'brit awards': 'Brit',
        'american music awards': 'AMA',
    }
    
    ceremony_lower = ceremony.lower().strip()
    return normalization_map.get(ceremony_lower, ceremony)


def normalize_award_category(category: str) -> str:
    """Normalize award category name"""
    if not category:
        return "General"
    
    # Clean wiki markup first: [[text|display]] -> display, [[text]] -> text
    category = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', category)
    # Remove remaining wiki markup
    category = re.sub(r'\|.*$', '', category)  # Remove everything after |
    category = re.sub(r'\[\[|\]\]', '', category)  # Remove remaining brackets
    category = re.sub(r"'''?", '', category)  # Remove bold markers
    
    # Remove table markup artifacts
    category = re.sub(r'rowspan\s*=\s*["\']?\d+["\']?', '', category, flags=re.IGNORECASE)
    category = re.sub(r'colspan\s*=\s*["\']?\d+["\']?', '', category, flags=re.IGNORECASE)
    category = re.sub(r'style\s*=\s*["\'][^"\']*["\']', '', category, flags=re.IGNORECASE)
    category = re.sub(r'class\s*=\s*["\'][^"\']*["\']', '', category, flags=re.IGNORECASE)
    
    # Clean and normalize category
    category = clean_text(category)
    
    # If category is empty or just artifacts after cleaning, return General
    if not category or len(category.strip()) < 3 or category.lower().strip() in ['rowspan', 'colspan']:
        return "General"
    
    # Vietnamese to English translations for common categories
    vietnamese_to_english = {
        'album của năm': 'Album of the Year',
        'bài hát của năm': 'Song of the Year',
        'nghệ sĩ của năm': 'Artist of the Year',
        'thu âm của năm': 'Record of the Year',
        'video của năm': 'Video of the Year',
        'album giọng pop xuất sắc nhất': 'Best Pop Vocal Album',
        'trình diễn solo giọng pop xuất sắc nhất': 'Best Pop Solo Performance',
        'nghệ sĩ mới xuất sắc nhất': 'Best New Artist',
        'best pop video': 'Best Pop Video',
        'best pop': 'Best Pop',
    }
    
    category_lower = category.lower().strip()
    # Check Vietnamese translations first
    for vi_cat, en_cat in vietnamese_to_english.items():
        if vi_cat in category_lower:
            return en_cat
    
    # Common category patterns
    category_patterns = {
        r'best\s+album.*': 'Best Album',
        r'best\s+song.*': 'Best Song',
        r'best\s+artist.*': 'Best Artist',
        r'best\s+record.*': 'Best Record',
        r'best\s+video.*': 'Best Video',
        r'best\s+performance.*': 'Best Performance',
        r'best\s+new\s+artist.*': 'Best New Artist',
        r'album\s+of\s+the\s+year': 'Album of the Year',
        r'song\s+of\s+the\s+year': 'Song of the Year',
        r'artist\s+of\s+the\s+year': 'Artist of the Year',
        r'record\s+of\s+the\s+year': 'Record of the Year',
        r'video\s+of\s+the\s+year': 'Video of the Year',
        r'album\s+của\s+năm': 'Album of the Year',
        r'bài\s+hát\s+của\s+năm': 'Song of the Year',
        r'nghệ\s+sĩ\s+của\s+năm': 'Artist of the Year',
    }
    
    for pattern, normalized in category_patterns.items():
        if re.search(pattern, category_lower):
            return normalized
    
    # Capitalize first letter if needed
    if category and category[0].islower():
        category = category[0].upper() + category[1:]
    
    return category if category else "General"


def validate_award_data(award: Dict, allow_no_year: bool = True) -> bool:
    """Validate award data quality
    
    Args:
        award: Award data dictionary
        allow_no_year: If True, allow awards without year (default: True for Vietnamese Wikipedia)
    """
    # Must have ceremony
    if not award.get('ceremony'):
        return False
    
    # Year validation (optional for Vietnamese Wikipedia)
    year = award.get('year')
    if year is not None:
        if not isinstance(year, int):
            return False
        if year < 1950 or year > 2050:
            return False
    
    # If year is required but missing
    if not allow_no_year and not year:
        return False
    
    # Must have category
    if not award.get('category'):
        return False
    
    return True


def create_award_nodes_csv(
    awards_file: str = "data/processed/awards.json",
    output_file: str = "data/processed/awards.csv"
) -> pd.DataFrame:
    """Create Award nodes CSV from extracted awards data
    
    Args:
        awards_file: Path to awards JSON file (artist -> list of awards)
        output_file: Path to output awards CSV file
    
    Returns:
        DataFrame with award nodes
    """
    logger.info("=" * 60)
    logger.info("CREATING AWARD NODES CSV")
    logger.info("=" * 60)
    
    # Load awards data
    logger.info(f"Loading awards from {awards_file}...")
    try:
        with open(awards_file, 'r', encoding='utf-8') as f:
            awards_data = json.load(f)
        logger.info(f"Loaded awards from {len(awards_data)} artists")
    except Exception as e:
        logger.error(f"Error loading awards file: {e}")
        return pd.DataFrame()
    
    # Process awards: normalize, deduplicate, and create nodes
    award_nodes = []
    award_key_map = {}  # (ceremony, category, year) -> award_node_data
    
    logger.info("Processing awards...")
    
    invalid_awards = 0
    valid_awards = 0
    
    for artist_name, awards in awards_data.items():
        for award in awards:
            # Validate award data (allow no year for Vietnamese Wikipedia)
            if not validate_award_data(award, allow_no_year=True):
                invalid_awards += 1
                logger.debug(f"Invalid award data: {award}")
                continue
            
            valid_awards += 1
            
            # Normalize ceremony name
            ceremony = normalize_award_name(award.get('ceremony', ''))
            
            # Normalize category (clean wiki markup first)
            category_raw = award.get('category', '')
            category = normalize_award_category(category_raw)
            
            # Get year (may be None for Vietnamese Wikipedia)
            year = award.get('year')
            
            # If no year, try to infer from context or use a default
            # For now, we'll allow None but group by (ceremony, category) if year is None
            if year is None:
                # Use a placeholder year for grouping, but mark as unknown
                award_key = (ceremony, category, None)
            else:
                award_key = (ceremony, category, year)
            
            if award_key not in award_key_map:
                # Create award name: "Ceremony - Category (Year)" or "Ceremony - Category" if no year
                if year:
                    award_name = f"{ceremony} - {category} ({year})"
                else:
                    award_name = f"{ceremony} - {category}"
                
                # Create award node
                award_node = {
                    'name': award_name,
                    'ceremony': ceremony,
                    'category': category,
                    'year': year if year else '',  # Empty string for CSV if None
                }
                
                award_key_map[award_key] = award_node
            else:
                # Award already exists (same ceremony, category, year)
                # This shouldn't happen if deduplication worked, but log it
                logger.debug(f"Duplicate award key: {award_key}")
    
    # Convert to list of award nodes
    logger.info("Converting to award nodes...")
    
    for award_key, award_data in award_key_map.items():
        award_nodes.append(award_data)
    
    # Create DataFrame
    df = pd.DataFrame(award_nodes)
    
    # Add unique ID
    if not df.empty:
        df.insert(0, 'id', range(len(df)))
        # Sort by ceremony, year, category for better organization
        df = df.sort_values(['ceremony', 'year', 'category'])
        df = df.reset_index(drop=True)
        df['id'] = range(len(df))
    
    # Report statistics
    logger.info("=" * 60)
    logger.info("AWARD NODES CREATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total valid awards processed: {valid_awards}")
    logger.info(f"Invalid awards skipped: {invalid_awards}")
    logger.info(f"Total unique award nodes: {len(df)}")
    
    if not df.empty:
        logger.info("")
        logger.info("Awards by ceremony:")
        ceremony_counts = df['ceremony'].value_counts()
        for ceremony, count in ceremony_counts.items():
            logger.info(f"  {ceremony}: {count}")
        
        logger.info("")
        logger.info("Awards by year range:")
        if 'year' in df.columns:
            # Filter out empty strings and convert to numeric
            years = df['year'].replace('', pd.NA).dropna()
            if len(years) > 0:
                # Convert to numeric, handling empty strings
                years_numeric = pd.to_numeric(years, errors='coerce').dropna()
                if len(years_numeric) > 0:
                    logger.info(f"  Earliest: {int(years_numeric.min())}")
                    logger.info(f"  Latest: {int(years_numeric.max())}")
                    logger.info(f"  Average: {years_numeric.mean():.1f}")
                else:
                    logger.info(f"  No valid years found")
            else:
                logger.info(f"  No years in awards data")
        
        logger.info("")
        logger.info("Top categories:")
        category_counts = df['category'].value_counts().head(10)
        for category, count in category_counts.items():
            logger.info(f"  {category}: {count}")
    
    # Save to CSV
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info("")
        logger.info(f"✓ Saved {len(df)} award nodes to {output_file}")
    except Exception as e:
        logger.error(f"Error saving award nodes CSV: {e}")
        raise
    
    return df


def extract_awards_from_seed_artists_file(
    seed_file: str = "config/seed_artists.json",
    output_file: str = "data/processed/awards.json",
    max_artists: Optional[int] = None
) -> Dict[str, List[Dict]]:
    """Extract awards from seed artists listed in a JSON file
    
    Args:
        seed_file: Path to seed artists JSON file
        output_file: Path to output awards JSON file
        max_artists: Maximum number of artists to process
    """
    logger.info(f"Loading seed artists from {seed_file}...")
    
    extractor = AwardExtractor()
    awards_data = extractor.extract_awards_from_seed_artists(
        max_artists=max_artists
    )
    
    # Save results
    extractor.save_awards(awards_data, output_file)
    
    return awards_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract awards from Wikipedia artist pages')
    parser.add_argument(
        '--seed-file',
        type=str,
        default='config/seed_artists.json',
        help='Path to seed artists JSON file'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='data/processed/awards.json',
        help='Path to output awards JSON file'
    )
    parser.add_argument(
        '--awards-csv',
        type=str,
        default='data/processed/awards.csv',
        help='Path to output awards CSV file'
    )
    parser.add_argument(
        '--max-artists',
        type=int,
        default=None,
        help='Maximum number of artists to process (for testing)'
    )
    parser.add_argument(
        '--create-csv',
        action='store_true',
        help='Create awards CSV from existing awards JSON file'
    )
    
    args = parser.parse_args()
    
    if args.create_csv:
        # Create CSV from existing awards JSON
        create_award_nodes_csv(
            awards_file=args.output_file,
            output_file=args.awards_csv
        )
    else:
        # Extract awards from seed artists
        extract_awards_from_seed_artists_file(
            seed_file=args.seed_file,
            output_file=args.output_file,
            max_artists=args.max_artists
        )


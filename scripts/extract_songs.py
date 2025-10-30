"""Song extraction from Wikipedia album pages"""

import json
import os
import re
import time
from typing import List, Dict, Optional
import wikipediaapi
import mwparserfromhell
import requests
import pandas as pd
from unidecode import unidecode

# Import utilities from parent directory
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_collection.utils import logger, rate_limit, log_progress, clean_text


class SongExtractor:
    """Extract songs from Wikipedia album pages"""
    
    def __init__(self, language: str = 'vi'):
        """Initialize song extractor"""
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='MusicNetworkProject/1.0 (test@example.com)',
            language=language
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MusicNetworkProject/1.0 (test@example.com)'
        })
        self.extracted_songs: Dict[str, List[Dict]] = {}  # album_name -> [songs]
        
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
    
    def _extract_tracks_from_infobox(self, infobox_text: str) -> List[Dict]:
        """Extract tracks from album infobox"""
        songs = []
        if not infobox_text:
            return songs
        
        try:
            wikicode = mwparserfromhell.parse(infobox_text)
            templates = wikicode.filter_templates()
            
            if not templates:
                return songs
            
            template = templates[0]
            track_patterns = ['tracks', 'track', 'tracklist', 'danh sách bài hát', 'bài hát']
            
            for param in template.params:
                param_name = str(param.name).strip().lower()
                param_value = str(param.value).strip()
                
                if any(pattern in param_name for pattern in track_patterns):
                    # Parse track list from infobox
                    parsed_songs = self._parse_track_list(param_value)
                    songs.extend(parsed_songs)
        
        except Exception as e:
            logger.debug(f"Error extracting tracks from infobox: {e}")
        
        return songs
    
    def _parse_track_list(self, track_text: str) -> List[Dict]:
        """Parse a track listing text into structured song data"""
        songs = []
        if not track_text:
            return songs
        
        try:
            # First, try to parse wiki templates (flat list, hlist, etc.)
            wikicode = mwparserfromhell.parse(track_text)
            templates = wikicode.filter_templates()
            
            if templates:
                # Extract from templates
                for template in templates:
                    template_name = str(template.name).strip().lower()
                    if 'flatlist' in template_name or 'hlist' in template_name:
                        # Extract items from flat list template
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                song = self._parse_song_line(param_value)
                                if song:
                                    songs.append(song)
            
            # Also parse raw text
            # Split by newlines, bullets, numbers
            lines = re.split(r'\n|•|\d+\.', track_text)
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                song = self._parse_song_line(line)
                if song:
                    songs.append(song)
        
        except Exception as e:
            logger.debug(f"Error parsing track list: {e}")
        
        return songs
    
    def _parse_song_line(self, line: str) -> Optional[Dict]:
        """Parse a single song line into structured data"""
        if not line or len(line.strip()) < 2:
            return None
        
        # Clean wiki markup
        line = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', line)
        line = re.sub(r"'''?([^']+)'''?", r'\1', line)
        line = re.sub(r'<[^>]+>', '', line)
        line = re.sub(r'<ref[^>]*>.*?</ref>', '', line, flags=re.DOTALL)
        line = re.sub(r'\{\{[^}]+\}\}', '', line)
        line = clean_text(line)
        
        # Extract track number
        track_number = None
        track_match = re.match(r'^(\d+)\.?\s+(.+)', line)
        if track_match:
            track_number = int(track_match.group(1))
            line = track_match.group(2).strip()
        
        # Extract duration (format: "3:45", "4:12", etc.)
        duration = None
        duration_patterns = [
            r'(\d{1,2}:\d{2})',  # "3:45"
            r'\((\d{1,2}:\d{2})\)',  # "(3:45)"
            r'\[(\d{1,2}:\d{2})\]',  # "[3:45]"
        ]
        for pattern in duration_patterns:
            duration_match = re.search(pattern, line)
            if duration_match:
                duration = duration_match.group(1)
                # Remove duration from title
                line = re.sub(pattern, '', line).strip()
                break
        
        # Extract featured artists (Vietnamese: "với", "ft.", "feat.", "featuring")
        featured_artists = []
        title = line
        
        # Pattern 1: "(featuring Artist)" or "(với Artist)"
        feat_pattern1 = r'\(([^)]*(?:với|ft\.|feat\.|featuring)[^)]+)\)'
        feat_matches = re.finditer(feat_pattern1, line, re.IGNORECASE)
        for feat_match in feat_matches:
            feat_text = feat_match.group(1)
            # Clean featured artist text
            feat_text = re.sub(r'^(với|ft\.|feat\.|featuring)\s+', '', feat_text, flags=re.IGNORECASE)
            feat_text = clean_text(feat_text)
            
            # Split multiple featured artists
            feat_artists = re.split(r'[,;&]|\s+và\s+|\s+and\s+', feat_text)
            for artist in feat_artists:
                artist = clean_text(artist)
                if artist and len(artist) > 1:
                    featured_artists.append(artist)
            
            # Remove featured part from title
            title = re.sub(re.escape(feat_match.group(0)), '', title).strip()
        
        # Pattern 2: "feat. Artist" or "với Artist" (without parentheses)
        feat_pattern2 = r'\s+(với|ft\.|feat\.|featuring)\s+([A-ZĂÂÊÔƠƯĐ][^\)]+?)(?:\s|$|\(|\))'
        feat_match2 = re.search(feat_pattern2, title, re.IGNORECASE)
        if feat_match2:
            feat_text = feat_match2.group(2)
            feat_text = clean_text(feat_text)
            
            # Split multiple featured artists
            feat_artists = re.split(r'[,;&]|\s+và\s+|\s+and\s+', feat_text)
            for artist in feat_artists:
                artist = clean_text(artist)
                if artist and len(artist) > 1:
                    featured_artists.append(artist)
            
            # Remove featured part from title
            title = re.sub(feat_pattern2, '', title).strip()
        
        # Clean title
        title = clean_text(title)
        
        # Remove trailing punctuation from title
        title = re.sub(r'^[\s\-\.]+|[\s\-\.]+$', '', title)
        
        # Validate song title
        if not title or len(title) < 2 or len(title) > 200:
            return None
        
        # Filter out false positives
        false_positives = [
            'track listing', 'danh sách bài hát', 'bài hát', 'songs',
            'total', 'tổng', 'bonus', 'bonus track', 'hidden track',
            'bản tiêu chuẩn', 'tiêu chuẩn', 'standard', 'standard version',
            'sản xuất', 'producer', 'producers', 'production',
            'intro', 'outro', 'interlude', 'skit',
            'act', 'act 1', 'act 2', 'act 3',
            'hợp tác', 'featuring', 'feat', 'ft',
            'ngoại trừ', 'except', 'trừ', 'excluding',
            'có chú thích', 'note', 'notes', 'ghi chú',
            'tải kỹ thuật số', 'digital download', 'digital',
            'cave in', 'cave', 'young', 'thiessen'  # Common noise words
        ]
        if any(fp in title.lower() for fp in false_positives):
            return None
        
        # Filter out titles that are too short or look like metadata
        if len(title) < 3:
            return None
        
        # Filter out titles that are all uppercase (often headers)
        if title.isupper() and len(title) > 10:
            return None
        
        # Filter out titles that are just numbers or single characters
        if re.match(r'^[\d\s#]+$', title):
            return None
        
        song = {
            'title': title,
            'track_number': track_number,
            'duration': duration,
            'featured_artists': featured_artists
        }
        
        return song
    
    def _extract_track_listing_section(self, page_text: str) -> List[Dict]:
        """Extract songs from Track listing section"""
        songs = []
        
        if not page_text:
            return songs
        
        # Find Track listing section (Vietnamese: "Danh sách bài hát", "Danh sách track")
        # English: "Track listing", "Track list"
        section_patterns = [
            r'==\s*(?:Track listing|Track list|Danh sách bài hát|Danh sách track|Danh sách|Tracks)\s*==',
            r'===\s*(?:Track listing|Track list|Danh sách bài hát|Danh sách track|Danh sách|Tracks)\s*===',
            r'==\s*(?:Track|Bài hát|Songs)\s*==',  # More general patterns
            r'===\s*(?:Track|Bài hát|Songs)\s*===',
        ]
        
        section_start = -1
        for pattern in section_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                section_start = match.end()
                break
        
        # Also try to extract from any section that mentions songs/tracks
        # Look for sections that might contain track listings
        if section_start == -1:
            # Try to find any section that might contain songs
            all_section_patterns = [
                r'==\s*([^=]+?)\s*==',
                r'===\s*([^=]+?)\s*===',
            ]
            
            for pattern in all_section_patterns:
                matches = list(re.finditer(pattern, page_text, re.IGNORECASE))
                for match in matches:
                    section_title = match.group(1).strip().lower()
                    # Check if section title suggests it contains tracks
                    if any(keyword in section_title for keyword in ['bài', 'song', 'track', 'danh sách', 'list']):
                        section_start = match.end()
                        logger.debug(f"    → Found potential track section: {match.group(1)}")
                        break
                if section_start != -1:
                    break
        
        # Extract content until next section (next ==)
        if section_start == -1:
            logger.debug(f"    → Không tìm thấy track listing section")
            return songs
        
        logger.debug(f"    → Đã tìm thấy section tại vị trí {section_start}")
        section_end_match = re.search(r'\n==', page_text[section_start:])
        if section_end_match:
            section_text = page_text[section_start:section_start + section_end_match.start()]
            logger.debug(f"    → Section text: {len(section_text)} chars")
        else:
            section_text = page_text[section_start:section_start + 5000]  # Limit to 5000 chars
            logger.debug(f"    → Section text (limited): {len(section_text)} chars")
        
        # Parse track listing
        logger.debug(f"    → Đang parse track listing...")
        parsed_songs = self._parse_track_listing_content(section_text)
        songs.extend(parsed_songs)
        logger.debug(f"    → Parsed {len(parsed_songs)} songs từ section")
        
        return songs
    
    def _parse_track_listing_content(self, content: str) -> List[Dict]:
        """Parse track listing section content"""
        songs = []
        
        if not content:
            return songs
        
        # First, try to parse wiki tables (common in track listings)
        try:
            wikicode = mwparserfromhell.parse(content)
            
            # Parse inline templates
            templates = wikicode.filter_templates()
            for template in templates:
                template_name = str(template.name).strip().lower()
                if 'track' in template_name or 'bài hát' in template_name:
                    # Extract track data from template
                    for param in template.params:
                        param_value = str(param.value).strip()
                        song = self._parse_song_line(param_value)
                        if song:
                            songs.append(song)
        
        except Exception as e:
            logger.debug(f"Error parsing track listing content: {e}")
        
        # Fallback: Parse raw text lines
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip headers, references, etc.
            if line.startswith('==') or line.startswith('!'):
                continue
            
            # Handle wiki table rows: | 1. | Song Title | 3:45 | Artist |
            if line.startswith('|'):
                # Extract content from table cells
                cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove first and last empty
                if len(cells) >= 2:
                    # Usually: track number, title, duration, featured artist
                    song_text = cells[1] if len(cells) > 1 else cells[0]
                    if song_text:
                        song = self._parse_song_line(song_text)
                        if song:
                            # Try to get track number from first cell
                            if cells[0] and re.match(r'^\d+', cells[0]):
                                track_match = re.match(r'^(\d+)', cells[0])
                                if track_match:
                                    song['track_number'] = int(track_match.group(1))
                            # Try to get duration from third cell
                            if len(cells) > 2 and cells[2]:
                                duration_match = re.search(r'(\d{1,2}:\d{2})', cells[2])
                                if duration_match:
                                    song['duration'] = duration_match.group(1)
                            songs.append(song)
                continue
            
            # Skip empty lines and references
            if re.match(r'^[\s\-\*\|]*$', line) or line.startswith('<ref'):
                continue
            
            # Parse song line
            song = self._parse_song_line(line)
            if song:
                songs.append(song)
        
        return songs
    
    def _parse_wiki_table(self, table_content: str) -> List[Dict]:
        """Parse wiki table content for track listings"""
        songs = []
        
        if not table_content:
            return songs
        
        # Extract table rows
        rows = re.findall(r'\|[^\|]+\|', table_content)
        
        for row in rows:
            # Parse row cells
            cells = [cell.strip() for cell in row.split('|')[1:-1]]
            
            if len(cells) >= 2:
                # Extract song data from cells
                song_text = cells[1] if len(cells) > 1 else cells[0]
                if song_text:
                    song = self._parse_song_line(song_text)
                    if song:
                        # Extract track number from first cell
                        if cells[0] and re.match(r'^\d+', cells[0]):
                            track_match = re.match(r'^(\d+)', cells[0])
                            if track_match:
                                song['track_number'] = int(track_match.group(1))
                        
                        # Extract duration from duration cell (usually third column)
                        if len(cells) >= 3 and cells[2]:
                            duration_match = re.search(r'(\d{1,2}:\d{2})', cells[2])
                            if duration_match:
                                song['duration'] = duration_match.group(1)
                        
                        songs.append(song)
        
        return songs
    
    def _search_wikipedia_page(self, album_name: str) -> Optional[str]:
        """Search for Wikipedia page with variations if exact match fails"""
        # Try exact match first
        page = self.wiki.page(album_name)
        if page.exists():
            return album_name
        
        # Try variations
        variations = [
            f"{album_name} (album)",
            f"{album_name} (album nhạc)",
            f"Album {album_name}",
            f"Đĩa nhạc {album_name}",
            album_name.title(),  # Title case
            album_name.lower(),  # Lowercase
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
                'srsearch': album_name,
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
    
    @rate_limit(0.5)  # Giảm từ 1.0s xuống 0.5s để tăng tốc độ
    def extract_songs_from_album(self, album_name: str) -> List[Dict]:
        """Extract songs from an album page with improved logging and fallback search"""
        try:
            logger.info(f"  Tìm kiếm trên Wikipedia tiếng Việt: '{album_name}'")
            
            # Try to find page (with variations if needed)
            logger.debug(f"    → Đang tìm trang Wikipedia...")
            actual_page_name = self._search_wikipedia_page(album_name)
            
            if not actual_page_name:
                logger.warning(f"  ✗ Không tìm thấy trang Wikipedia cho: '{album_name}'")
                logger.debug(f"    URL thử: https://vi.wikipedia.org/wiki/{album_name.replace(' ', '_')}")
                return []
            
            # Use the actual page name found
            logger.debug(f"    → Đang load trang: '{actual_page_name}'")
            page = self.wiki.page(actual_page_name)
            
            if not page.exists():
                logger.warning(f"  ✗ Trang không tồn tại: '{actual_page_name}'")
                return []
            
            logger.info(f"  ✓ Tìm thấy trang: '{page.title}'")
            logger.debug(f"    URL: {page.fullurl}")
            
            songs = []
            
            # Method 1: Extract from infobox
            logger.debug(f"    → Method 1: Đang extract từ infobox...")
            infobox = self._extract_infobox(actual_page_name)
            if infobox:
                infobox_songs = self._extract_tracks_from_infobox(infobox)
                songs.extend(infobox_songs)
                logger.info(f"    ✓ Extracted {len(infobox_songs)} songs từ infobox")
            else:
                logger.debug(f"    ✗ Không tìm thấy infobox")
            
            # Method 2: Extract from Track listing section
            logger.debug(f"    → Method 2: Đang extract từ Track listing section...")
            page_text = page.text if hasattr(page, 'text') else page.summary
            if page_text:
                section_songs = self._extract_track_listing_section(page_text)
                songs.extend(section_songs)
                logger.info(f"    ✓ Extracted {len(section_songs)} songs từ track listing section")
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
                
                logger.debug(f"    → Đang request wikitext từ API...")
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                pages = data.get('query', {}).get('pages', [])
                if pages:
                    logger.debug(f"    → Đang parse wikitext ({len(pages[0].get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', ''))} chars)...")
                    wikitext = pages[0].get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
                    
                    # Parse track listing from wikitext more comprehensively
                    wikitext_songs = self._extract_track_listing_section(wikitext)
                    songs.extend(wikitext_songs)
                    logger.info(f"    ✓ Extracted {len(wikitext_songs)} songs từ wikitext track listing")
                    
                    # Also try to extract from any table-like structures in wikitext
                    logger.debug(f"    → Đang tìm songs từ table patterns...")
                    # Look for patterns like: |1||"Song Title"||3:45||Artist|
                    table_patterns = [
                        r'\|\s*\d+\s*\|\|[^|]*\|\|([^|]+)\|\|',  # |1||Song||
                        r'\|\s*\d+\s*\|\s*([^|]+)\s*\|',  # |1|Song|
                        r'#\s*([A-ZĂÂÊÔƠƯĐ][^(\n]{2,50})',  # # Song Title
                        r'\d+\.\s*([A-ZĂÂÊÔƠƯĐ][^(\n]{2,50})',  # 1. Song Title
                    ]
                    
                    pattern_songs_count = 0
                    for i, pattern in enumerate(table_patterns, 1):
                        matches = re.finditer(pattern, wikitext, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            song_text = match.group(1).strip()
                            if song_text:
                                song = self._parse_song_line(song_text)
                                if song:
                                    songs.append(song)
                                    pattern_songs_count += 1
                                    if pattern_songs_count <= 3:  # Log first 3
                                        logger.debug(f"    → Pattern {i}: Tìm thấy '{song_text[:40]}'")
                    
                    if pattern_songs_count > 0:
                        logger.info(f"    ✓ Extracted {pattern_songs_count} songs từ table patterns")
            except Exception as e:
                logger.debug(f"    ✗ Error extracting from wikitext: {e}")
            
            # Deduplicate songs by title
            logger.debug(f"    → Đang deduplicate songs (tổng {len(songs)} songs)...")
            unique_songs = []
            seen_titles = set()
            
            for song in songs:
                title_lower = song['title'].lower().strip()
                if title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    unique_songs.append(song)
            
            logger.debug(f"    → Sau deduplicate: {len(unique_songs)} unique songs")
            
            if unique_songs:
                logger.info(f"  ✓ Tìm thấy {len(unique_songs)} songs từ '{page.title}'")
            else:
                logger.warning(f"  ✗ Trang tồn tại nhưng không có songs: '{page.title}'")
                logger.debug(f"    → Có thể trang không có track listing hoặc format không chuẩn")
            
            return unique_songs
            
        except Exception as e:
            logger.error(f"  ✗ Error extracting songs from {album_name}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def extract_songs_from_albums(self, albums: List[str], max_albums: Optional[int] = None, 
                                   skip_existing: bool = True, existing_songs: Dict = None) -> Dict[str, List[Dict]]:
        """Extract songs from multiple albums
        
        Args:
            albums: List of album names to extract
            max_albums: Maximum number of albums to process
            skip_existing: If True, skip albums that already have songs in existing_songs
            existing_songs: Dict of existing songs data to skip
        """
        logger.info(f"Starting song extraction from {len(albums)} albums...")
        
        if max_albums:
            albums = albums[:max_albums]
        
        # Skip albums that already have songs
        if skip_existing and existing_songs:
            albums_to_process = [a for a in albums if a not in existing_songs or not existing_songs.get(a)]
            skipped = len(albums) - len(albums_to_process)
            if skipped > 0:
                logger.info(f"  → Skipping {skipped} albums đã có songs (dùng skip_existing=True)")
            albums = albums_to_process
        
        if not albums:
            logger.info("  → Tất cả albums đã có songs, không cần extract thêm")
            return existing_songs or {}
        
        logger.info(f"  → Sẽ extract từ {len(albums)} albums mới")
        
        results = existing_songs.copy() if existing_songs else {}
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        for i, album_name in enumerate(albums, 1):
            logger.info(f"[{i}/{len(albums)}] Extracting songs from: {album_name}")
            
            songs = self.extract_songs_from_album(album_name)
            
            if songs:
                results[album_name] = songs
                successful += 1
                logger.info(f"  ✓ Found {len(songs)} songs")
            else:
                failed += 1
                # Note: Detailed reasons are logged in extract_songs_from_album()
                logger.warning(f"  ✗ No songs found")
            
            # Progress update every 10 albums với time estimate
            if i % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = avg_time * (len(albums) - i)
                log_progress(i, len(albums), "Extracting songs")
                logger.info(f"  Progress: {successful} successful, {failed} failed")
                logger.info(f"  Time: {elapsed/60:.1f}m elapsed, ~{remaining/60:.1f}m remaining")
        
        logger.info("=" * 60)
        logger.info("SONG EXTRACTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total albums processed: {len(albums)}")
        logger.info(f"Successful: {successful} ({successful/len(albums)*100:.1f}%)")
        logger.info(f"Failed: {failed} ({failed/len(albums)*100:.1f}%)")
        logger.info(f"Total songs extracted: {sum(len(songs) for songs in results.values())}")
        
        if successful > 0:
            avg_songs = sum(len(songs) for songs in results.values()) / successful
            logger.info(f"Average songs per successful album: {avg_songs:.1f}")
        
        if failed > 0:
            logger.warning("")
            logger.warning("Lý do có thể fail:")
            logger.warning("  1. Album page không tồn tại trên Wikipedia tiếng Việt")
            logger.warning("  2. Album page tồn tại nhưng không có track listing")
            logger.warning("  3. Format track listing không chuẩn (không parse được)")
            logger.warning("")
            logger.warning("Check logs ở trên để xem chi tiết cho từng album.")
        
        return results
    
    def save_songs(self, songs_data: Dict[str, List[Dict]], output_path: str):
        """Save extracted songs to JSON file"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(songs_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved songs data to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving songs: {e}")
            raise


def normalize_song_title(title: str) -> str:
    """Normalize song title for deduplication"""
    if not title:
        return ""
    
    # Remove accents and special characters for comparison
    normalized = unidecode(title.lower())
    
    # Remove common suffixes that don't affect uniqueness
    suffixes = [
        r'\s+\(remix\)$',
        r'\s+\(remaster\)$',
        r'\s+\(remastered\)$',
        r'\s+\(bonus track\)$',
        r'\s+\(bonus\)$',
        r'\s+\(hidden track\)$',
        r'\s+\(demo\)$',
        r'\s+\(live\)$',
        r'\s+\(acoustic\)$',
    ]
    
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
    
    # Remove special characters except spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Normalize whitespace
    normalized = " ".join(normalized.split())
    
    return normalized


def create_song_nodes_csv(
    songs_file: str = "data/processed/songs.json",
    albums_file: str = "data/processed/albums.json",
    output_file: str = "data/processed/songs.csv"
) -> pd.DataFrame:
    """Create Song nodes CSV from extracted songs data"""
    logger.info("=" * 60)
    logger.info("CREATING SONG NODES CSV")
    logger.info("=" * 60)
    
    # Load songs data
    logger.info(f"Loading songs from {songs_file}...")
    try:
        with open(songs_file, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)
        logger.info(f"Loaded songs from {len(songs_data)} albums")
    except Exception as e:
        logger.error(f"Error loading songs file: {e}")
        return pd.DataFrame()
    
    # Load albums data to create album_id mapping
    logger.info(f"Loading albums from {albums_file}...")
    try:
        with open(albums_file, 'r', encoding='utf-8') as f:
            albums_data = json.load(f)
        
        # Create album_name -> album_id mapping
        # Match the pattern used in builder.py: album_id = f"album_{album_idx}"
        # Note: builder.py only creates album nodes for albums with 2+ artists
        # So we need to track which albums will actually get nodes
        album_id_map = {}
        album_idx = 0
        for album_name in sorted(albums_data.keys()):
            artist_ids = albums_data[album_name]
            # Only create album_id for albums with 2+ artists (matching builder.py logic)
            if len(artist_ids) >= 2:
                album_id_map[album_name] = f"album_{album_idx}"
                album_idx += 1
            else:
                # Single-artist albums don't get nodes in builder.py
                # But we still want to track songs from them
                album_id_map[album_name] = None
        
        logger.info(f"Created mapping for {len(album_id_map)} albums")
    except Exception as e:
        logger.error(f"Error loading albums file: {e}")
        return pd.DataFrame()
    
    # Process songs: normalize, deduplicate, and create nodes
    song_nodes = []
    song_title_map = {}  # normalized_title -> song_node_data
    orphan_songs = []  # Songs without matching albums
    
    logger.info("Processing songs...")
    
    for album_name, songs in songs_data.items():
        # Get album_id
        album_id = album_id_map.get(album_name)
        
        if not album_id:
            logger.debug(f"Album not found in mapping: {album_name}")
            # Still process songs but mark as orphan
            album_id = None
        
        for song in songs:
            title = song.get('title', '').strip()
            if not title or len(title) < 2:
                continue
            
            # Normalize title for deduplication
            normalized_title = normalize_song_title(title)
            
            if not normalized_title:
                continue
            
            # Extract featured artists
            featured_artists = song.get('featured_artists', [])
            if not isinstance(featured_artists, list):
                featured_artists = []
            
            # Create featured artists string
            featured_artists_str = "; ".join(featured_artists) if featured_artists else ""
            
            # Get duration and track_number
            duration = song.get('duration', '')
            track_number = song.get('track_number')
            
            # Handle deduplication: same song across albums
            if normalized_title in song_title_map:
                # Song already exists - update with additional album info if needed
                existing_song = song_title_map[normalized_title]
                
                # Add album_id to list if not already present
                album_ids = existing_song.get('album_ids', [])
                if album_id and album_id not in album_ids:
                    album_ids.append(album_id)
                    existing_song['album_ids'] = album_ids
                
                # Merge featured artists
                existing_featured = existing_song.get('featured_artists', [])
                for feat in featured_artists:
                    if feat not in existing_featured:
                        existing_featured.append(feat)
                existing_song['featured_artists'] = existing_featured
                
                # Update duration/track_number if missing in existing
                if not existing_song.get('duration') and duration:
                    existing_song['duration'] = duration
                if not existing_song.get('track_number') and track_number:
                    existing_song['track_number'] = track_number
            else:
                # New song - create entry
                song_node = {
                    'title': title,
                    'normalized_title': normalized_title,
                    'duration': duration if duration else '',
                    'track_number': track_number if track_number else '',
                    'album_ids': [album_id] if album_id else [],
                    'featured_artists': featured_artists,
                    'featured_artists_str': featured_artists_str
                }
                
                song_title_map[normalized_title] = song_node
                
                if not album_id:
                    orphan_songs.append(title)
    
    # Convert to list of song nodes
    logger.info("Converting to song nodes...")
    
    for normalized_title, song_data in song_title_map.items():
        # For now, use first album_id as primary (can be extended later)
        # In future, we might want to create multiple song nodes or relationships
        album_ids = song_data['album_ids']
        # Filter out None values
        valid_album_ids = [aid for aid in album_ids if aid is not None]
        primary_album_id = valid_album_ids[0] if valid_album_ids else ''
        
        # Create song node
        track_num = song_data.get('track_number')
        song_node = {
            'title': song_data['title'],
            'duration': song_data.get('duration', ''),
            'track_number': str(track_num) if track_num is not None else '',
            'album_id': primary_album_id,
            'featured_artists': song_data.get('featured_artists_str', ''),
            'album_count': len(valid_album_ids)  # Track how many albums this song appears on
        }
        
        song_nodes.append(song_node)
    
    # Create DataFrame
    df = pd.DataFrame(song_nodes)
    
    # Add unique ID
    if not df.empty:
        df.insert(0, 'id', range(len(df)))
    
    # Report statistics
    logger.info("=" * 60)
    logger.info("SONG NODES CREATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total unique songs: {len(df)}")
    if not df.empty:
        logger.info(f"Songs with duration: {df['duration'].astype(str).str.len().gt(0).sum()}")
        logger.info(f"Songs with track_number: {df['track_number'].astype(str).str.len().gt(0).sum()}")
        logger.info(f"Songs with featured artists: {df['featured_artists'].astype(str).str.len().gt(0).sum()}")
        logger.info(f"Songs appearing on multiple albums: {(df['album_count'] > 1).sum()}")
    logger.info(f"Orphan songs (no album): {len(orphan_songs)}")
    
    if orphan_songs:
        logger.warning(f"Found {len(orphan_songs)} orphan songs without matching albums")
        logger.debug(f"Sample orphan songs: {orphan_songs[:5]}")
    
    # Save to CSV
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} song nodes to {output_file}")
    except Exception as e:
        logger.error(f"Error saving song nodes CSV: {e}")
        raise
    
    return df


def extract_songs_from_albums_file(
    albums_file: str = "data/processed/albums.json",
    output_file: str = "data/processed/songs.json",
    max_albums: Optional[int] = None,
    skip_existing: bool = True
) -> Dict[str, List[Dict]]:
    """Extract songs from albums listed in a JSON file
    
    Args:
        albums_file: Path to albums JSON file
        output_file: Path to output songs JSON file
        max_albums: Maximum number of albums to process
        skip_existing: If True, skip albums that already have songs in output_file
    """
    logger.info(f"Loading albums from {albums_file}...")
    
    try:
        with open(albums_file, 'r', encoding='utf-8') as f:
            albums_data = json.load(f)
        
        # Extract album names (keys of the dictionary)
        album_names = list(albums_data.keys())
        logger.info(f"Found {len(album_names)} albums")
        
    except Exception as e:
        logger.error(f"Error loading albums file: {e}")
        return {}
    
    # Load existing songs if skip_existing is True
    existing_songs = {}
    if skip_existing and os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_songs = json.load(f)
            logger.info(f"  → Found existing songs.json với {len(existing_songs)} albums")
            albums_with_songs = sum(1 for v in existing_songs.values() if v)
            logger.info(f"  → Albums với songs: {albums_with_songs}")
        except Exception as e:
            logger.warning(f"  → Could not load existing songs.json: {e}")
            existing_songs = {}
    
    # Extract songs
    extractor = SongExtractor()
    songs_data = extractor.extract_songs_from_albums(
        album_names, 
        max_albums=max_albums,
        skip_existing=skip_existing,
        existing_songs=existing_songs if skip_existing else None
    )
    
    # Save results
    extractor.save_songs(songs_data, output_file)
    
    return songs_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract songs from Wikipedia album pages')
    parser.add_argument(
        '--albums-file',
        type=str,
        default='data/processed/albums.json',
        help='Path to albums JSON file'
    )
    parser.add_argument(
        '--songs-file',
        type=str,
        default='data/processed/songs.json',
        help='Path to input songs JSON file (for CSV creation)'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='data/processed/songs.json',
        help='Path to output songs JSON file'
    )
    parser.add_argument(
        '--songs-csv',
        type=str,
        default='data/processed/songs.csv',
        help='Path to output songs CSV file'
    )
    parser.add_argument(
        '--max-albums',
        type=int,
        default=None,
        help='Maximum number of albums to process (for testing)'
    )
    parser.add_argument(
        '--create-csv',
        action='store_true',
        help='Create songs CSV from existing songs JSON file'
    )
    
    args = parser.parse_args()
    
    if args.create_csv:
        # Create CSV from existing songs JSON
        create_song_nodes_csv(
            songs_file=args.songs_file,
            albums_file=args.albums_file,
            output_file=args.songs_csv
        )
    else:
        # Extract songs from albums
        extract_songs_from_albums_file(
            albums_file=args.albums_file,
            output_file=args.output_file,
            max_albums=args.max_albums
        )


"""Parser for Wikipedia infobox data"""

import json
import re
from typing import Dict, List, Optional, Any
import mwparserfromhell
from data_collection.utils import logger, clean_text


class InfoboxParser:
    """Parse Wikipedia infobox templates to extract structured data"""
    
    def __init__(self):
        self.genre_patterns = [
            'thể loại', 'genre', 'loại nhạc', 'thể_loại'
        ]
        self.instrument_patterns = [
            'nhạc cụ', 'instruments', 'instrument', 'nhạc_cụ'
        ]
        self.years_patterns = [
            'năm hoạt động', 'years active', 'years_active', 'năm_hoạt_động'
        ]
        self.album_patterns = [
            'album', 'albums', 'discography', 'đĩa nhạc'
        ]
        self.label_patterns = [
            'label', 'labels', 'record label', 'record_label', 'nhãn đĩa', 'nhãn_đĩa'
        ]
    
    def parse_infobox(self, infobox_text: str) -> Dict[str, Any]:
        """Parse infobox wikitext and extract fields"""
        if not infobox_text:
            return {}
        
        try:
            wikicode = mwparserfromhell.parse(infobox_text)
            templates = wikicode.filter_templates()
            
            if not templates:
                return {}
            
            template = templates[0]
            data = {
                'genres': [],
                'instruments': [],
                'active_years': '',
                'albums': [],
                'labels': []
            }
            
            for param in template.params:
                param_name = str(param.name).strip().lower()
                param_value = str(param.value).strip()
                
                # Extract genres
                if any(pattern in param_name for pattern in self.genre_patterns):
                    data['genres'] = self._parse_list_field(param_value)
                
                # Extract instruments
                elif any(pattern in param_name for pattern in self.instrument_patterns):
                    data['instruments'] = self._parse_list_field(param_value)
                
                # Extract active years
                elif any(pattern in param_name for pattern in self.years_patterns):
                    data['active_years'] = clean_text(param_value)
                
                # Extract albums (with improved parsing)
                elif any(pattern in param_name for pattern in self.album_patterns):
                    albums = self._parse_album_field(param_value)
                    data['albums'] = [{'title': album} for album in albums]
                
                # Extract record labels
                elif any(pattern in param_name for pattern in self.label_patterns):
                    data['labels'] = self._parse_list_field(param_value)
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing infobox: {e}")
            return {}
    
    def _parse_list_field(self, field_value: str) -> List[str]:
        """Parse a field that contains a list of values"""
        if not field_value:
            return []
        
        # First, try to parse wiki templates (flat list, hlist, etc.)
        try:
            wikicode = mwparserfromhell.parse(field_value)
            templates = wikicode.filter_templates()
            
            # If we have templates, extract items from them
            if templates:
                items = []
                for template in templates:
                    template_name = str(template.name).strip().lower()
                    # Handle flat list and hlist templates (flatlist, flat list, hlist)
                    if 'flatlist' in template_name or 'flat list' in template_name or 'hlist' in template_name:
                        # Extract all parameters (both named and positional)
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                items.append(param_value)
                        # Also check if template has body content (items after pipe)
                        # Flat list templates often have items as body content
                        template_str = str(template)
                        # Extract content after the pipe in {{template|content}}
                        body_match = re.search(r'\|\s*(.*)', template_str, re.DOTALL)
                        if body_match:
                            body_content = body_match.group(1)
                            # Remove closing braces
                            body_content = re.sub(r'\}\}$', '', body_content)
                            # Split by newlines and extract list items
                            lines = body_content.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and (line.startswith('*') or line.startswith('|')):
                                    # Remove asterisk/pipe and wiki link formatting
                                    item = re.sub(r'^[\*\|\s]+', '', line)
                                    if item and item not in items:
                                        items.append(item)
                    
                    # Handle other templates by extracting their content
                    else:
                        # Extract all parameter values
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                items.append(param_value)
                
                # If we extracted items from templates, use them
                if items:
                    field_value = '\n'.join(items)
        except Exception:
            # If template parsing fails, continue with original value
            pass
        
        # Parse wiki links: [[Text|Display]] -> Display, [[Text]] -> Text
        field_value = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', field_value)
        
        # Remove bold/italic markup: '''text''' -> text
        field_value = re.sub(r"'''?([^']+)'''?", r'\1', field_value)
        
        # Remove HTML tags
        field_value = re.sub(r'<[^>]+>', '', field_value)
        
        # Remove wiki template calls that weren't parsed (like {{ref}})
        field_value = re.sub(r'\{\{[^}]+\}\}', '', field_value)
        
        # Remove reference tags: <ref>...</ref>
        field_value = re.sub(r'<ref[^>]*>.*?</ref>', '', field_value, flags=re.DOTALL)
        
        # Remove standalone braces and pipes that are artifacts
        field_value = re.sub(r'^\s*[{}|]+\s*', '', field_value)
        field_value = re.sub(r'\s*[{}|]+\s*$', '', field_value)
        
        # Split by common separators
        # Use multiple patterns: comma, semicolon, newline, bullet, <br>, pipe
        items = re.split(r'[,;\n•|]|<br\s*/?>', field_value)
        
        # Clean and filter items
        cleaned_items = []
        for item in items:
            # Remove leading/trailing whitespace and artifacts
            item = item.strip()
            
            # Remove leading asterisks, braces, pipes
            item = re.sub(r'^[\*\s{}\|]+', '', item)
            item = re.sub(r'[\*\s{}\|]+$', '', item)
            
            # Remove any remaining template artifacts
            item = re.sub(r'\{\{|\}\}', '', item)
            
            # Clean text
            item = clean_text(item)
            
            # Normalize genre names
            item = self._normalize_genre(item)
            
            # Filter valid items
            if item and len(item) > 1 and len(item) < 100:
                # Skip items that are just artifacts
                artifact_patterns = ['}}', '{{', '|', '*', '']
                if item not in artifact_patterns:
                    cleaned_items.append(item)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in cleaned_items:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                unique_items.append(item)
        
        return unique_items[:10]  # Limit to 10 items
    
    def _normalize_genre(self, genre: str) -> str:
        """Normalize genre name"""
        if not genre:
            return ""
        
        genre = genre.strip()
        
        # Common genre normalizations
        normalizations = {
            'r&b': 'R&B',
            'r & b': 'R&B',
            'r and b': 'R&B',
            'nhạc pop': 'pop',
            'nhạc rock': 'rock',
            'nhạc soul': 'soul',
            'nhạc dance': 'dance',
            'nhạc hip hop': 'hip hop',
            'nhạc rap': 'rap',
            'nhạc country': 'country',
            'nhạc jazz': 'jazz',
            'nhạc blues': 'blues',
            'nhạc electronic': 'electronic',
            'nhạc folk': 'folk',
            'nhạc alternative': 'alternative',
            'dance-pop': 'dance pop',
            'pop-rock': 'pop rock',
            'rock-pop': 'rock pop',
            'hip-hop': 'hip hop',
            'hip hop': 'hip hop',
            'r&b đương đại': 'contemporary R&B',
            'r&b contemporary': 'contemporary R&B',
            'contemporary r&b': 'contemporary R&B',
            'blue-eyed soul': 'blue eyed soul',
            'funk-pop': 'funk pop',
            'acoustic rock': 'acoustic rock',
            'blues rock': 'blues rock',
            'pop dân gian': 'folk pop',
            'pop folk': 'folk pop',
        }
        
        genre_lower = genre.lower()
        if genre_lower in normalizations:
            return normalizations[genre_lower]
        
        # Capitalize properly (first letter uppercase, rest lowercase, except acronyms)
        # Handle common patterns
        if genre_lower.startswith('r&b'):
            return 'R&B' + genre[3:] if len(genre) > 3 else 'R&B'
        
        # Capitalize first letter of each word, but keep common acronyms as-is
        words = genre.split()
        normalized_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower in ['r&b', 'pop', 'r&b', 'edm', 'idm']:
                normalized_words.append(word.upper() if word.isupper() else word_lower)
            else:
                normalized_words.append(word.capitalize())
        
        return ' '.join(normalized_words)
    
    def _parse_album_field(self, field_value: str) -> List[str]:
        """Parse album field specifically with improved extraction patterns"""
        if not field_value:
            return []
        
        # First, try to parse wiki templates (flat list, hlist, etc.)
        try:
            wikicode = mwparserfromhell.parse(field_value)
            templates = wikicode.filter_templates()
            
            # If we have templates, extract items from them
            if templates:
                items = []
                for template in templates:
                    template_name = str(template.name).strip().lower()
                    # Handle flat list and hlist templates
                    if 'flatlist' in template_name or 'flat list' in template_name or 'hlist' in template_name:
                        # Extract all parameters (both named and positional)
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                items.append(param_value)
                        # Extract body content
                        template_str = str(template)
                        body_match = re.search(r'\|\s*(.*)', template_str, re.DOTALL)
                        if body_match:
                            body_content = body_match.group(1)
                            body_content = re.sub(r'\}\}$', '', body_content)
                            lines = body_content.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and (line.startswith('*') or line.startswith('|')):
                                    item = re.sub(r'^[\*\|\s]+', '', line)
                                    if item and item not in items:
                                        items.append(item)
                    else:
                        # Extract parameter values from other templates
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                items.append(param_value)
                
                if items:
                    field_value = '\n'.join(items)
        except Exception:
            pass
        
        # Parse wiki links: [[Text|Display]] -> Display, [[Text]] -> Text
        field_value = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', field_value)
        
        # Remove bold/italic markup: '''text''' -> text
        field_value = re.sub(r"'''?([^']+)'''?", r'\1', field_value)
        
        # Remove HTML tags
        field_value = re.sub(r'<[^>]+>', '', field_value)
        
        # Remove wiki template calls that weren't parsed
        field_value = re.sub(r'\{\{[^}]+\}\}', '', field_value)
        
        # Remove reference tags: <ref>...</ref>
        field_value = re.sub(r'<ref[^>]*>.*?</ref>', '', field_value, flags=re.DOTALL)
        
        # Remove standalone braces and pipes that are artifacts
        field_value = re.sub(r'^\s*[{}|]+\s*', '', field_value)
        field_value = re.sub(r'\s*[{}|]+\s*$', '', field_value)
        
        # Improved splitting patterns for albums
        # Handle: comma, semicolon, newline, bullet, <br>, pipe, and common Vietnamese separators
        items = re.split(r'[,;\n•|]|<br\s*/?>|\s*–\s*|\s*—\s*|\s*-\s*(?=[A-ZĂÂÊÔƠƯĐ])', field_value)
        
        # Clean and filter items
        cleaned_items = []
        for item in items:
            # Remove leading/trailing whitespace and artifacts
            item = item.strip()
            
            # Remove leading asterisks, braces, pipes
            item = re.sub(r'^[\*\s{}\|]+', '', item)
            item = re.sub(r'[\*\s{}\|]+$', '', item)
            
            # Remove any remaining template artifacts
            item = re.sub(r'\{\{|\}\}', '', item)
            
            # Remove year patterns at the end: (2008), (2013), etc.
            item = re.sub(r'\s*\(\d{4}\)\s*$', '', item)
            
            # Clean text
            item = clean_text(item)
            
            # Filter valid items (basic check - full validation happens later)
            if item and len(item) > 1 and len(item) < 200:
                # Skip items that are just artifacts
                artifact_patterns = ['}}', '{{', '|', '*', '']
                if item not in artifact_patterns:
                    cleaned_items.append(item)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in cleaned_items:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                unique_items.append(item)
        
        return unique_items[:30]  # Limit to 30 albums (more than genres)
    
    def _validate_album_name(self, album_name: str) -> bool:
        """Validate album name and filter out bad entries"""
        if not album_name:
            return False
        
        album_name = album_name.strip()
        
        # Basic length checks
        if len(album_name) <= 1:
            return False
        
        if len(album_name) < 4:
            return False
        
        if len(album_name) > 200:
            return False
        
        # Filter out numbers only
        if album_name.isdigit():
            return False
        
        # Filter out year-only patterns: (2008), (2013), etc.
        if re.match(r'^\(\d{4}\)$', album_name):
            return False
        
        # Filter out common false positives
        false_positives = [
            'yes', 'no', 'all', 'one', 'two', 'three', 'four', 'five',
            'six', 'seven', 'eight', 'nine', 'ten', 'ref', 'web',
            'review', 'citation', 'billboard', 'magic', 'week',
            'list', 'index', 'title', 'name', 'album', 'song'
        ]
        if album_name.lower() in false_positives:
            return False
        
        # Filter out names that start with special characters (incomplete extractions)
        if album_name[0] in ['(', '[', '{', '/', '\\', '-', '_', '|', '*']:
            return False
        
        # Filter out names that end with incomplete characters
        if album_name[-1] in ['(', '[', '{', '/', '\\', '|', '*']:
            return False
        
        # Filter out wiki markup artifacts
        if '}}' in album_name or '{{' in album_name or '</ref>' in album_name:
            return False
        
        # Filter out Vietnamese bad patterns
        vietnamese_bad_patterns = [
            r'^đầu tay\s',  # "đầu tay ArtistName" - means "debut of ArtistName"
            r'^tư\s',  # "tư Red" - incomplete extraction
            r'^ng\s',  # Partial Vietnamese word
            r'^của\s',  # "của ArtistName" - means "of ArtistName"
            r'^được\s',  # "được ArtistName" - means "by ArtistName"
            r'^là\s',  # "là ArtistName" - means "is ArtistName"
            r'^có\s',  # "có ArtistName" - means "has ArtistName"
            r'^trong\s',  # "trong ArtistName" - means "in ArtistName"
            r'^với\s',  # "với ArtistName" - means "with ArtistName"
            r'^theo\s',  # "theo ArtistName" - means "according to ArtistName"
            r'^từ\s',  # "từ ArtistName" - means "from ArtistName"
            r'nh tên',  # Partial text
            r'a cô',  # Partial text
            r'ng tên',  # Partial text
            r'tên cô',  # Partial text
            r'^\s*album\s+của\s',  # "album của ArtistName"
            r'^\s*đĩa nhạc\s+của\s',  # "đĩa nhạc của ArtistName"
        ]
        for pattern in vietnamese_bad_patterns:
            if re.search(pattern, album_name, re.IGNORECASE):
                return False
        
        # Filter out incomplete English patterns
        incomplete_patterns = [
            r'^to\s[A-Z][a-z]+$',  # "to ArtistName"
            r'^a\s[A-Z][a-z]+$',  # "a ArtistName"
            r'^an\s[A-Z][a-z]+$',  # "an ArtistName"
            r'^the\s[A-Z][a-z]+$',  # "the ArtistName" (single word after)
            r'^by\s[A-Z]',  # "by ArtistName"
            r'^of\s[A-Z]',  # "of ArtistName"
            r'^from\s[A-Z]',  # "from ArtistName"
            r'^with\s[A-Z]',  # "with ArtistName"
            r'^album\s+by\s',  # "album by ArtistName"
            r'^album\s+of\s',  # "album of ArtistName"
            r'^song\s+by\s',  # "song by ArtistName"
            r'^single\s+by\s',  # "single by ArtistName"
        ]
        for pattern in incomplete_patterns:
            if re.match(pattern, album_name, re.IGNORECASE):
                return False
        
        # Filter out generic words that aren't specific enough (single word)
        generic_words = [
            'book', 'chapter', 'part', 'section', 'volume', 'edition',
            'version', 'demo', 'remix', 'edit', 'mix', 'cut', 'single',
            'album', 'ep', 'lp', 'cd', 'tape', 'record'
        ]
        words = album_name.lower().split()
        if len(words) == 1 and words[0] in generic_words:
            return False
        
        # Filter out single-word album names that are too short
        if len(words) == 1 and len(album_name) < 8:
            return False
        
        # Filter out album names that are too generic/common
        overly_common = [
            'celebration', 'greatest hits', 'best of', 'collection',
            'anthology', 'greatest hits album', 'best of album'
        ]
        if album_name.lower() in overly_common:
            return False
        
        # Filter out artist names that end up as album names (common patterns)
        # Check if it looks like an artist name followed by description
        if re.search(r'\s+\(album\s+(của|by|of)', album_name, re.IGNORECASE):
            return False
        
        # Filter out incomplete extractions that contain only common words
        only_common_words = ['the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for']
        if len(words) <= 2 and all(word.lower() in only_common_words for word in words):
            return False
        
        return True
    
    def parse_artist(self, artist_data: Dict) -> Dict[str, Any]:
        """Parse a single artist's data"""
        infobox_text = artist_data.get('infobox', '')
        parsed_infobox = self.parse_infobox(infobox_text)
        
        # Get albums from raw data if available, otherwise from infobox
        raw_albums = artist_data.get('albums', [])
        infobox_albums = parsed_infobox.get('albums', [])
        
        # Combine albums from both sources with validation
        all_albums = []
        album_titles = set()
        
        # Add albums from raw data (already extracted by scraper)
        for album in raw_albums:
            if isinstance(album, str):
                album_title = album.strip()
            elif isinstance(album, dict):
                album_title = album.get('title', '').strip()
            else:
                continue
            
            # Validate album name before adding
            if album_title and self._validate_album_name(album_title):
                album_title_lower = album_title.lower()
                if album_title_lower not in album_titles:
                    album_titles.add(album_title_lower)
                    all_albums.append({'title': album_title})
        
        # Add albums from infobox
        for album in infobox_albums:
            if isinstance(album, dict):
                album_title = album.get('title', '').strip()
            elif isinstance(album, str):
                album_title = album.strip()
            else:
                continue
            
            # Validate album name before adding
            if album_title and self._validate_album_name(album_title):
                album_title_lower = album_title.lower()
                if album_title_lower not in album_titles:
                    album_titles.add(album_title_lower)
                    all_albums.append({'title': album_title})
        
        return {
            'name': artist_data.get('title', ''),
            'url': artist_data.get('url', ''),
            'summary': artist_data.get('summary', ''),
            'genres': parsed_infobox.get('genres', []),
            'instruments': parsed_infobox.get('instruments', []),
            'active_years': parsed_infobox.get('active_years', ''),
            'albums': all_albums,
            'labels': parsed_infobox.get('labels', [])
        }
    
    def parse_all(self, input_path: str = "data/raw/artists.json") -> List[Dict]:
        """Parse all artists from raw data file"""
        logger.info(f"Parsing artists from {input_path}...")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                artists = json.load(f)
            
            parsed_artists = []
            for i, artist in enumerate(artists, 1):
                try:
                    parsed = self.parse_artist(artist)
                    parsed_artists.append(parsed)
                    
                    if i % 100 == 0:
                        logger.info(f"Parsed {i}/{len(artists)} artists")
                        
                except Exception as e:
                    logger.error(f"Error parsing artist {artist.get('title', 'unknown')}: {e}")
            
            logger.info(f"Successfully parsed {len(parsed_artists)} artists")
            return parsed_artists
            
        except Exception as e:
            logger.error(f"Error loading artists from {input_path}: {e}")
            return []


def parse_all(input_path: str = "data/raw/artists.json", 
              output_path: str = "data/processed/parsed_artists.json") -> int:
    """Main function to parse all artist data"""
    import os
    
    parser = InfoboxParser()
    parsed_artists = parser.parse_all(input_path)
    
    # Save parsed data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_artists, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved parsed data to {output_path}")
    return len(parsed_artists)


if __name__ == "__main__":
    parse_all()



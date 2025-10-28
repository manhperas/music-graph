"""Wikipedia scraper for collecting artist data"""

import json
import os
import re
from typing import List, Dict, Set, Optional
import wikipediaapi
import mwparserfromhell
import requests
from .utils import logger, rate_limit, log_progress, clean_text


class WikipediaScraper:
    """Scraper for Wikipedia Vietnamese pages of pop artists"""
    
    def __init__(self, config_path: str = "config/wikipedia_config.json"):
        """Initialize scraper with configuration"""
        self.config = self._load_config(config_path)
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='MusicNetworkProject/1.0 (test@example.com)',
            language=self.config.get('language', 'vi')
        )
        self.session = requests.Session()
        # Add User-Agent header to session
        self.session.headers.update({
            'User-Agent': 'MusicNetworkProject/1.0 (test@example.com)'
        })
        self.collected_artists: Set[str] = set()
        self.seed_artists: List[str] = []
        self.album_pool: Set[str] = set()  # Track albums found
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {
                "categories": ["Danh sách nghệ sĩ nhạc pop Mỹ", "Nhạc pop Anh"],
                "max_artists": 1000,
                "language": "vi",
                "rate_limit_delay": 1.0,
                "recursive_depth": 3
            }
    
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
                logger.warning(f"Seed file not found: {seed_path}, continuing without seed")
                return []
        except Exception as e:
            logger.error(f"Error loading seed artists: {e}")
            return []
    
    def _extract_albums_from_infobox(self, infobox_text: str) -> List[str]:
        """Extract album names from infobox wikitext"""
        albums = []
        if not infobox_text:
            return albums
        
        try:
            wikicode = mwparserfromhell.parse(infobox_text)
            templates = wikicode.filter_templates()
            
            if not templates:
                return albums
            
            template = templates[0]
            album_patterns = ['album', 'albums', 'discography', 'đĩa nhạc']
            
            for param in template.params:
                param_name = str(param.name).strip().lower()
                param_value = str(param.value).strip()
                
                if any(pattern in param_name for pattern in album_patterns):
                    # Parse album list
                    album_items = re.split(r'[,;\n•]|<br\s*/?>|\{\{[^\}]+\}\}', param_value)
                    for item in album_items:
                        # Clean wiki markup
                        item = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', item)
                        item = re.sub(r"'''?([^']+)'''?", r'\1', item)
                        item = re.sub(r'<[^>]+>', '', item)
                        item = clean_text(item)
                        
                        if item and len(item) > 1 and len(item) < 100:
                            albums.append(item)
        
        except Exception as e:
            logger.debug(f"Error extracting albums: {e}")
        
        return albums[:20]  # Limit to 20 albums
    
    def _extract_albums_from_text(self, text: str, summary: str) -> List[str]:
        """Extract album names from text content using regex patterns"""
        albums = []
        combined_text = f"{summary} {text[:2000]}"  # Use summary + first 2000 chars
        
        # Pattern to match album names with years: "album Title (YYYY)"
        # Also matches: "Title (YYYY)" where Title is capitalized
        patterns = [
            r'album\s+([A-Z][^(\n]+?)\s*\((\d{4})\)',  # "album Title (YYYY)"
            r'([A-Z][A-Za-z\s&]+?)\s*\((\d{4})\)',      # "Title (YYYY)" 
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, combined_text)
            for match in matches:
                album_name = match.group(1).strip()
                # Clean the album name
                album_name = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', album_name)
                album_name = re.sub(r"'''?([^']+)'''?", r'\1', album_name)
                album_name = clean_text(album_name)
                
                # Filter out common false positives
                if (album_name and 
                    len(album_name) > 1 and 
                    len(album_name) < 100 and
                    not any(word in album_name.lower() for word in ['phát hành', 'năm', 'phòng thu', 'thứ'])):
                    albums.append(album_name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_albums = []
        for album in albums:
            if album not in seen:
                seen.add(album)
                unique_albums.append(album)
        
        return unique_albums[:15]  # Limit to 15 albums
    
    @rate_limit(1.0)
    def get_category_members(self, category_name: str, depth: int = 0) -> List[str]:
        """Get all members of a Wikipedia category recursively"""
        members = []
        
        if depth > self.config.get('recursive_depth', 3):
            return members
        
        try:
            cat = self.wiki.page(f"Category:{category_name}")
            
            if not cat.exists():
                logger.warning(f"Category does not exist: {category_name}")
                return members
            
            # Get direct members (articles)
            for member_title in cat.categorymembers.keys():
                member = cat.categorymembers[member_title]
                
                if member.ns == wikipediaapi.Namespace.MAIN:  # Article page
                    members.append(member.title)
                elif member.ns == wikipediaapi.Namespace.CATEGORY and depth < self.config.get('recursive_depth', 3):
                    # Recursively get subcategory members
                    sub_members = self.get_category_members(
                        member.title.replace("Thể loại:", "").replace("Category:", ""),
                        depth + 1
                    )
                    members.extend(sub_members)
            
            logger.info(f"Found {len(members)} members in category: {category_name} (depth: {depth})")
            
        except Exception as e:
            logger.error(f"Error getting category members for {category_name}: {e}")
        
        return members
    
    @rate_limit(1.0)
    def fetch_artist_data(self, artist_name: str) -> Optional[Dict]:
        """Fetch artist page and extract data"""
        try:
            page = self.wiki.page(artist_name)
            
            if not page.exists():
                logger.warning(f"Page does not exist: {artist_name}")
                return None
            
            # Get page text
            text = page.text if hasattr(page, 'text') else page.summary
            
            # Get infobox using MediaWiki API
            infobox = self._extract_infobox(artist_name)
            
            data = {
                "title": artist_name,
                "url": page.fullurl,
                "summary": clean_text(page.summary) if hasattr(page, 'summary') else "",
                "text": clean_text(text[:5000]),  # Limit text length
                "infobox": infobox
            }
            
            logger.debug(f"Fetched data for: {artist_name}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching artist data for {artist_name}: {e}")
            return None
    
    def _extract_infobox(self, page_title: str) -> str:
        """Extract infobox wikitext using MediaWiki API"""
        try:
            url = f"https://vi.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'prop': 'revisions',
                'rvprop': 'content',
                'rvslots': 'main',
                'titles': page_title,
                'format': 'json',
                'formatversion': 2
            }
            
            # Use session with User-Agent header
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
            logger.error(f"Error extracting infobox for {page_title}: {e}")
            return ""
    
    def collect_artists(self) -> List[Dict]:
        """Collect artist data using hybrid approach: seed + snowball + category"""
        logger.info("Starting artist data collection with snowball sampling...")
        
        all_artists = []
        artist_names = set()
        max_artists = self.config.get('max_artists', 1000)
        
        # STEP 1: Load and collect seed artists
        logger.info("=" * 60)
        logger.info("STEP 1: COLLECTING SEED ARTISTS")
        logger.info("=" * 60)
        
        self.seed_artists = self._load_seed_artists()
        
        seed_count = 0
        for artist_name in self.seed_artists:
            if len(all_artists) >= max_artists:
                break
            
            artist_data = self.fetch_artist_data(artist_name)
            if artist_data:
                all_artists.append(artist_data)
                artist_names.add(artist_name)
                self.collected_artists.add(artist_name)
                
                # Extract albums from seed artist (try both infobox and text)
                albums = self._extract_albums_from_infobox(artist_data.get('infobox', ''))
                if not albums:  # Fallback to text extraction if infobox has no albums
                    albums = self._extract_albums_from_text(
                        artist_data.get('text', ''), 
                        artist_data.get('summary', '')
                    )
                self.album_pool.update(albums)
                seed_count += 1
        
        logger.info(f"✓ Collected {seed_count} seed artists")
        logger.info(f"✓ Found {len(self.album_pool)} unique albums from seed artists")
        
        # STEP 2: Collect from categories (Snowball sampling via category)
        logger.info("=" * 60)
        logger.info("STEP 2: COLLECTING FROM CATEGORIES (SNOWBALL SAMPLING)")
        logger.info("=" * 60)
        
        category_artists = set()
        for category in self.config.get('categories', []):
            logger.info(f"Processing category: {category}")
            members = self.get_category_members(category)
            
            for member in members:
                if member not in artist_names:
                    category_artists.add(member)
        
        logger.info(f"Found {len(category_artists)} artists from categories")
        
        # Fetch category artists
        category_count = 0
        category_list = list(category_artists)
        
        for i, artist_name in enumerate(category_list, 1):
            if len(all_artists) >= max_artists:
                break
            
            artist_data = self.fetch_artist_data(artist_name)
            if artist_data:
                all_artists.append(artist_data)
                artist_names.add(artist_name)
                self.collected_artists.add(artist_name)
                
                # Extract albums for snowball tracking (try both infobox and text)
                albums = self._extract_albums_from_infobox(artist_data.get('infobox', ''))
                if not albums:  # Fallback to text extraction if infobox has no albums
                    albums = self._extract_albums_from_text(
                        artist_data.get('text', ''), 
                        artist_data.get('summary', '')
                    )
                self.album_pool.update(albums)
                category_count += 1
            
            if i % 10 == 0:
                log_progress(i, len(category_list), "Collecting from categories")
        
        logger.info(f"✓ Collected {category_count} artists from categories")
        
        # Final summary
        logger.info("=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total artists collected: {len(all_artists)}")
        logger.info(f"  - Seed artists: {seed_count}")
        logger.info(f"  - Category artists: {category_count}")
        logger.info(f"Total albums found: {len(self.album_pool)}")
        
        return all_artists
    
    def save_data(self, artists: List[Dict], output_path: str = "data/raw/artists.json"):
        """Save collected artist data to JSON file"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(artists, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(artists)} artists to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise


def scrape_all(config_path: str = "config/wikipedia_config.json", 
               output_path: str = "data/raw/artists.json"):
    """Main function to scrape all artist data"""
    scraper = WikipediaScraper(config_path)
    artists = scraper.collect_artists()
    scraper.save_data(artists, output_path)
    return len(artists)


if __name__ == "__main__":
    scrape_all()



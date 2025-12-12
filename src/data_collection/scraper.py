import json
import os
import re
from typing import List, Dict, Set, Optional
import wikipediaapi
import mwparserfromhell
import requests
from .utils import logger, rate_limit, log_progress, clean_text

class WikipediaScraper:

    def __init__(self, config_path: str='config/wikipedia_config.json'):
        self.config = self._load_config(config_path)
        self.wiki = wikipediaapi.Wikipedia(user_agent='MusicNetworkProject/1.0 (test@example.com)', language=self.config.get('language', 'vi'))
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MusicNetworkProject/1.0 (test@example.com)'})
        self.collected_artists: Set[str] = set()
        self.seed_artists: List[str] = []
        self.album_pool: Set[str] = set()

    def _load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f'Loaded configuration from {config_path}')
            return config
        except Exception as e:
            logger.error(f'Error loading config: {e}')
            return {'categories': ['Danh sách nghệ sĩ nhạc pop Mỹ', 'Nhạc pop Anh'], 'max_artists': 1000, 'language': 'vi', 'rate_limit_delay': 1.0, 'recursive_depth': 3}

    def _load_seed_artists(self, seed_path: str='config/seed_artists.json') -> List[str]:
        try:
            if os.path.exists(seed_path):
                with open(seed_path, 'r', encoding='utf-8') as f:
                    seed_data = json.load(f)
                    seed_list = seed_data.get('seed_artists', [])
                    logger.info(f'Loaded {len(seed_list)} seed artists from {seed_path}')
                    return seed_list
            else:
                logger.warning(f'Seed file not found: {seed_path}, continuing without seed')
                return []
        except Exception as e:
            logger.error(f'Error loading seed artists: {e}')
            return []

    def _extract_albums_from_infobox(self, infobox_text: str) -> List[str]:
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
                if any((pattern in param_name for pattern in album_patterns)):
                    album_items = re.split('[,;\\n•]|<br\\s*/?>|\\{\\{[^\\}]+\\}\\}', param_value)
                    for item in album_items:
                        item = re.sub('\\[\\[([^\\]|]+\\|)?([^\\]]+)\\]\\]', '\\2', item)
                        item = re.sub("'''?([^']+)'''?", '\\1', item)
                        item = re.sub('<[^>]+>', '', item)
                        item = clean_text(item)
                        if item and len(item) > 1 and (len(item) < 100):
                            albums.append(item)
        except Exception as e:
            logger.debug(f'Error extracting albums: {e}')
        return albums[:20]

    def _extract_albums_from_text(self, text: str, summary: str) -> List[str]:
        albums = []
        combined_text = f'{summary} {text[:5000]}'
        patterns = ['album\\s+([A-ZĂÂÊÔƠƯĐ][^(\\n]{2,50}?)\\s*\\((\\d{4})\\)', '([A-ZĂÂÊÔƠƯĐ][A-Za-zĂâÊôƠơƯđ\\s&\\\'\\"]{2,50}?)\\s*\\((\\d{4})\\)', 'Album:\\s*([A-ZĂÂÊÔƠƯĐ][^:\\n]{2,50})', 'Đĩa nhạc:\\s*([A-ZĂÂÊÔƠƯĐ][^:\\n]{2,50})', '\\[\\[([A-ZĂÂÊÔƠƯĐ][A-Za-zĂâÊôƠơƯđ\\s&\\\'\\"\\d]{2,50})\\]\\](?:\\s*\\((\\d{4})\\))?']
        for pattern in patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                album_name = match.group(1).strip()
                album_name = re.sub('\\[\\[([^\\]|]+\\|)?([^\\]]+)\\]\\]', '\\2', album_name)
                album_name = re.sub("'''?([^']+)'''?", '\\1', album_name)
                album_name = re.sub('<[^>]+>', '', album_name)
                album_name = clean_text(album_name)
                false_positives = ['phát hành', 'năm', 'phòng thu', 'thứ', 'bài hát', 'single', 'đĩa đơn', 'ep', 'album', 'song', 'track', 'bản thu', 'ghi âm', 'tháng', 'ngày', 'tuần']
                if album_name and len(album_name) > 2 and (len(album_name) < 100) and (not any((word in album_name.lower() for word in false_positives))) and (not album_name.isdigit()):
                    albums.append(album_name)
        seen = set()
        unique_albums = []
        for album in albums:
            normalized = album.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_albums.append(album)
        return unique_albums[:30]

    @rate_limit(1.0)
    def get_category_members(self, category_name: str, depth: int=0) -> List[str]:
        members = []
        if depth > self.config.get('recursive_depth', 3):
            return members
        try:
            cat = self.wiki.page(f'Category:{category_name}')
            if not cat.exists():
                logger.warning(f'Category does not exist: {category_name}')
                return members
            for member_title in cat.categorymembers.keys():
                member = cat.categorymembers[member_title]
                if member.ns == wikipediaapi.Namespace.MAIN:
                    members.append(member.title)
                elif member.ns == wikipediaapi.Namespace.CATEGORY and depth < self.config.get('recursive_depth', 3):
                    sub_members = self.get_category_members(member.title.replace('Thể loại:', '').replace('Category:', ''), depth + 1)
                    members.extend(sub_members)
            logger.info(f'Found {len(members)} members in category: {category_name} (depth: {depth})')
        except Exception as e:
            logger.error(f'Error getting category members for {category_name}: {e}')
        return members

    @rate_limit(1.0)
    def fetch_artist_data(self, artist_name: str) -> Optional[Dict]:
        try:
            page = self.wiki.page(artist_name)
            if not page.exists():
                logger.warning(f'Page does not exist: {artist_name}')
                return None
            text = page.text if hasattr(page, 'text') else page.summary
            summary = page.summary if hasattr(page, 'summary') else ''
            infobox = self._extract_infobox(artist_name)
            albums_from_infobox = self._extract_albums_from_infobox(infobox)
            albums_from_text = self._extract_albums_from_text(text, summary)
            all_albums = list(set(albums_from_infobox + albums_from_text))
            data = {'title': artist_name, 'url': page.fullurl, 'summary': clean_text(summary), 'text': clean_text(text[:5000]), 'infobox': infobox, 'albums': all_albums}
            logger.debug(f'Fetched data for: {artist_name}, found {len(all_albums)} albums')
            return data
        except Exception as e:
            logger.error(f'Error fetching artist data for {artist_name}: {e}')
            return None

    def _extract_infobox(self, page_title: str) -> str:
        try:
            url = f'https://vi.wikipedia.org/w/api.php'
            params = {'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main', 'titles': page_title, 'format': 'json', 'formatversion': 2}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            pages = data.get('query', {}).get('pages', [])
            if not pages:
                return ''
            content = pages[0].get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
            wikicode = mwparserfromhell.parse(content)
            for template in wikicode.filter_templates():
                template_name = str(template.name).strip().lower()
                if 'infobox' in template_name or 'hộp thông tin' in template_name:
                    return str(template)
            return ''
        except Exception as e:
            logger.error(f'Error extracting infobox for {page_title}: {e}')
            return ''

    def _extract_collaborators_from_album(self, album_name: str) -> List[str]:
        try:
            page = self.wiki.page(album_name)
            if not page.exists():
                return []
            infobox = self._extract_infobox(album_name)
            collaborators = []
            if infobox:
                wikicode = mwparserfromhell.parse(infobox)
                templates = wikicode.filter_templates()
                if templates:
                    template = templates[0]
                    param_patterns = ['artist', 'featuring', 'released_by', 'nghệ sĩ']
                    for param in template.params:
                        param_name = str(param.name).strip().lower()
                        param_value = str(param.value).strip()
                        if any((pattern in param_name for pattern in param_patterns)):
                            artists = re.split('[,;&]|<br\\s*/?>', param_value)
                            for artist in artists:
                                artist = clean_text(artist)
                                if artist and len(artist) > 1:
                                    collaborators.append(artist)
            text = page.text if hasattr(page, 'text') else page.summary
            feat_pattern = "(?:featuring|với|và)\\s+([A-Z][A-Za-z\\s&\\']+)"
            matches = re.finditer(feat_pattern, text[:2000], re.IGNORECASE)
            for match in matches:
                artist = clean_text(match.group(1))
                if artist and len(artist) > 1:
                    collaborators.append(artist)
            return list(set(collaborators))[:10]
        except Exception as e:
            logger.debug(f'Error extracting collaborators from album {album_name}: {e}')
            return []

    def _snowball_expand(self, seed_artists: List[str], depth: int=2, max_artists: int=500) -> List[str]:
        collected = set(seed_artists)
        logger.info(f'Starting simplified snowball expansion from {len(seed_artists)} seed artists...')
        logger.info('Using category-based sampling to find related artists')
        all_category_artists = set()
        for category in self.config.get('categories', []):
            try:
                cat = self.wiki.page(f'Category:{category}')
                if not cat.exists():
                    continue
                members = list(cat.categorymembers.keys())[:200]
                for member_title in members:
                    member = cat.categorymembers[member_title]
                    if member.ns == wikipediaapi.Namespace.MAIN:
                        artist_name = member.title
                        if artist_name not in seed_artists:
                            all_category_artists.add(artist_name)
            except Exception as e:
                logger.debug(f'Error searching category {category}: {e}')
                continue
        logger.info(f'Found {len(all_category_artists)} artists from categories')
        sampled_artists = list(all_category_artists)[:max_artists]
        logger.info(f'Sampled {len(sampled_artists)} artists for snowball expansion')
        return sampled_artists

    def collect_artists(self) -> List[Dict]:
        logger.info('Starting artist data collection with SEED-FIRST approach...')
        all_artists = []
        artist_names = set()
        max_artists = self.config.get('max_artists', 1000)
        snowball_count = 0
        category_count = 0
        logger.info('=' * 60)
        logger.info('STEP 1: LOADING SEED ARTISTS')
        logger.info('=' * 60)
        self.seed_artists = self._load_seed_artists()
        if not self.seed_artists:
            logger.warning('No seed artists found. Falling back to category-based collection.')
            return self._collect_from_categories_only()
        logger.info('=' * 60)
        logger.info('STEP 2: FETCHING SEED ARTISTS DATA (HIGH PRIORITY)')
        logger.info('=' * 60)
        seed_count = 0
        for i, artist_name in enumerate(self.seed_artists, 1):
            logger.info(f'[{i}/{len(self.seed_artists)}] Fetching seed artist: {artist_name}')
            artist_data = self.fetch_artist_data(artist_name)
            if artist_data:
                all_artists.append(artist_data)
                artist_names.add(artist_name)
                self.collected_artists.add(artist_name)
                albums = self._extract_albums_from_infobox(artist_data.get('infobox', ''))
                if not albums:
                    albums = self._extract_albums_from_text(artist_data.get('text', ''), artist_data.get('summary', ''))
                self.album_pool.update(albums)
                seed_count += 1
                logger.info(f'  ✓ Found {len(albums)} albums')
            else:
                logger.warning(f'  ✗ Failed to fetch data for {artist_name}')
        logger.info(f'✓ Collected {seed_count}/{len(self.seed_artists)} seed artists')
        logger.info(f'✓ Total albums in pool: {len(self.album_pool)}')
        if len(all_artists) < max_artists:
            logger.info('=' * 60)
            logger.info('STEP 3: SNOWBALL EXPANSION FROM SEED ARTISTS')
            logger.info('=' * 60)
            snowball_artists = self._snowball_expand(seed_artists=self.seed_artists, depth=2, max_artists=min(max_artists - len(all_artists), 300))
            logger.info(f'✓ Snowball sampling found {len(snowball_artists)} potential artists')
            for artist_name in snowball_artists:
                if len(all_artists) >= max_artists:
                    break
                if artist_name in artist_names:
                    continue
                artist_data = self.fetch_artist_data(artist_name)
                if artist_data:
                    all_artists.append(artist_data)
                    artist_names.add(artist_name)
                    self.collected_artists.add(artist_name)
                    albums = self._extract_albums_from_infobox(artist_data.get('infobox', ''))
                    if not albums:
                        albums = self._extract_albums_from_text(artist_data.get('text', ''), artist_data.get('summary', ''))
                    self.album_pool.update(albums)
                    snowball_count += 1
                if snowball_count % 10 == 0:
                    log_progress(snowball_count, len(snowball_artists), 'Fetching snowball artists')
            logger.info(f'✓ Fetched data for {snowball_count} snowball artists')
        if len(all_artists) < max_artists:
            logger.info('=' * 60)
            logger.info('STEP 4: CATEGORY FALLBACK (to reach target)')
            logger.info('=' * 60)
            remaining = max_artists - len(all_artists)
            category_artists = set()
            for category in self.config.get('categories', []):
                logger.info(f'Processing category: {category}')
                members = self.get_category_members(category)
                for member in members:
                    if member not in artist_names:
                        category_artists.add(member)
            logger.info(f'Found {len(category_artists)} artists from categories')
            category_list = list(category_artists)[:remaining]
            for i, artist_name in enumerate(category_list, 1):
                if len(all_artists) >= max_artists:
                    break
                artist_data = self.fetch_artist_data(artist_name)
                if artist_data:
                    all_artists.append(artist_data)
                    artist_names.add(artist_name)
                    self.collected_artists.add(artist_name)
                    albums = self._extract_albums_from_infobox(artist_data.get('infobox', ''))
                    if not albums:
                        albums = self._extract_albums_from_text(artist_data.get('text', ''), artist_data.get('summary', ''))
                    self.album_pool.update(albums)
                    category_count += 1
                if i % 10 == 0:
                    log_progress(i, len(category_list), 'Collecting from categories')
            logger.info(f'✓ Collected {category_count} artists from categories')
        logger.info('=' * 60)
        logger.info('COLLECTION SUMMARY')
        logger.info('=' * 60)
        logger.info(f'Total artists collected: {len(all_artists)}')
        logger.info(f'  - Seed artists (priority): {seed_count}')
        logger.info(f'  - Snowball expansion: {snowball_count}')
        logger.info(f'  - Category fallback: {(category_count if len(all_artists) < max_artists else 0)}')
        logger.info(f'Total albums found: {len(self.album_pool)}')
        logger.info(f'Seed artists in final collection: {sum((1 for name in artist_names if name in self.seed_artists))}/{len(self.seed_artists)}')
        return all_artists

    def _collect_from_categories_only(self) -> List[Dict]:
        all_artists = []
        artist_names = set()
        max_artists = self.config.get('max_artists', 1000)
        category_artists = set()
        for category in self.config.get('categories', []):
            logger.info(f'Processing category: {category}')
            members = self.get_category_members(category)
            for member in members:
                if member not in artist_names:
                    category_artists.add(member)
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
                albums = self._extract_albums_from_infobox(artist_data.get('infobox', ''))
                if not albums:
                    albums = self._extract_albums_from_text(artist_data.get('text', ''), artist_data.get('summary', ''))
                self.album_pool.update(albums)
                category_count += 1
            if i % 10 == 0:
                log_progress(i, len(category_list), 'Collecting from categories')
        logger.info(f'✓ Collected {category_count} artists from categories')
        return all_artists

    def save_data(self, artists: List[Dict], output_path: str='data/raw/artists.json'):
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(artists, f, ensure_ascii=False, indent=2)
            logger.info(f'Saved {len(artists)} artists to {output_path}')
        except Exception as e:
            logger.error(f'Error saving data: {e}')
            raise

def scrape_all(config_path: str='config/wikipedia_config.json', output_path: str='data/raw/artists.json'):
    scraper = WikipediaScraper(config_path)
    artists = scraper.collect_artists()
    scraper.save_data(artists, output_path)
    return len(artists)
if __name__ == '__main__':
    scrape_all()

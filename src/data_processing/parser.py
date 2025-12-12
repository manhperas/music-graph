import json
import re
from typing import Dict, List, Optional, Any
import mwparserfromhell
from data_collection.utils import logger, clean_text

class InfoboxParser:

    def __init__(self):
        self.genre_patterns = ['thể loại', 'genre', 'loại nhạc', 'thể_loại']
        self.instrument_patterns = ['nhạc cụ', 'instruments', 'instrument', 'nhạc_cụ']
        self.years_patterns = ['năm hoạt động', 'years active', 'years_active', 'năm_hoạt_động']
        self.album_patterns = ['album', 'albums', 'discography', 'đĩa nhạc']
        self.label_patterns = ['label', 'labels', 'record label', 'record_label', 'nhãn đĩa', 'nhãn_đĩa']

    def parse_infobox(self, infobox_text: str) -> Dict[str, Any]:
        if not infobox_text:
            return {}
        try:
            wikicode = mwparserfromhell.parse(infobox_text)
            templates = wikicode.filter_templates()
            if not templates:
                return {}
            template = templates[0]
            data = {'genres': [], 'instruments': [], 'active_years': '', 'albums': [], 'labels': []}
            for param in template.params:
                param_name = str(param.name).strip().lower()
                param_value = str(param.value).strip()
                if any((pattern in param_name for pattern in self.genre_patterns)):
                    data['genres'] = self._parse_list_field(param_value)
                elif any((pattern in param_name for pattern in self.instrument_patterns)):
                    data['instruments'] = self._parse_list_field(param_value)
                elif any((pattern in param_name for pattern in self.years_patterns)):
                    data['active_years'] = clean_text(param_value)
                elif any((pattern in param_name for pattern in self.album_patterns)):
                    albums = self._parse_album_field(param_value)
                    data['albums'] = [{'title': album} for album in albums]
                elif any((pattern in param_name for pattern in self.label_patterns)):
                    data['labels'] = self._parse_list_field(param_value)
            return data
        except Exception as e:
            logger.error(f'Error parsing infobox: {e}')
            return {}

    def _parse_list_field(self, field_value: str) -> List[str]:
        if not field_value:
            return []
        try:
            wikicode = mwparserfromhell.parse(field_value)
            templates = wikicode.filter_templates()
            if templates:
                items = []
                for template in templates:
                    template_name = str(template.name).strip().lower()
                    if 'flatlist' in template_name or 'flat list' in template_name or 'hlist' in template_name:
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                items.append(param_value)
                        template_str = str(template)
                        body_match = re.search('\\|\\s*(.*)', template_str, re.DOTALL)
                        if body_match:
                            body_content = body_match.group(1)
                            body_content = re.sub('\\}\\}$', '', body_content)
                            lines = body_content.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and (line.startswith('*') or line.startswith('|')):
                                    item = re.sub('^[\\*\\|\\s]+', '', line)
                                    if item and item not in items:
                                        items.append(item)
                    else:
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                items.append(param_value)
                if items:
                    field_value = '\n'.join(items)
        except Exception:
            pass
        field_value = re.sub('\\[\\[([^\\]|]+\\|)?([^\\]]+)\\]\\]', '\\2', field_value)
        field_value = re.sub("'''?([^']+)'''?", '\\1', field_value)
        field_value = re.sub('<[^>]+>', '', field_value)
        field_value = re.sub('\\{\\{[^}]+\\}\\}', '', field_value)
        field_value = re.sub('<ref[^>]*>.*?</ref>', '', field_value, flags=re.DOTALL)
        field_value = re.sub('^\\s*[{}|]+\\s*', '', field_value)
        field_value = re.sub('\\s*[{}|]+\\s*$', '', field_value)
        items = re.split('[,;\\n•|]|<br\\s*/?>', field_value)
        cleaned_items = []
        for item in items:
            item = item.strip()
            item = re.sub('^[\\*\\s{}\\|]+', '', item)
            item = re.sub('[\\*\\s{}\\|]+$', '', item)
            item = re.sub('\\{\\{|\\}\\}', '', item)
            item = clean_text(item)
            item = self._normalize_genre(item)
            if item and len(item) > 1 and (len(item) < 100):
                artifact_patterns = ['}}', '{{', '|', '*', '']
                if item not in artifact_patterns:
                    cleaned_items.append(item)
        seen = set()
        unique_items = []
        for item in cleaned_items:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                unique_items.append(item)
        return unique_items[:10]

    def _normalize_genre(self, genre: str) -> str:
        if not genre:
            return ''
        genre = genre.strip()
        normalizations = {'r&b': 'R&B', 'r & b': 'R&B', 'r and b': 'R&B', 'nhạc pop': 'pop', 'nhạc rock': 'rock', 'nhạc soul': 'soul', 'nhạc dance': 'dance', 'nhạc hip hop': 'hip hop', 'nhạc rap': 'rap', 'nhạc country': 'country', 'nhạc jazz': 'jazz', 'nhạc blues': 'blues', 'nhạc electronic': 'electronic', 'nhạc folk': 'folk', 'nhạc alternative': 'alternative', 'dance-pop': 'dance pop', 'pop-rock': 'pop rock', 'rock-pop': 'rock pop', 'hip-hop': 'hip hop', 'hip hop': 'hip hop', 'r&b đương đại': 'contemporary R&B', 'r&b contemporary': 'contemporary R&B', 'contemporary r&b': 'contemporary R&B', 'blue-eyed soul': 'blue eyed soul', 'funk-pop': 'funk pop', 'acoustic rock': 'acoustic rock', 'blues rock': 'blues rock', 'pop dân gian': 'folk pop', 'pop folk': 'folk pop'}
        genre_lower = genre.lower()
        if genre_lower in normalizations:
            return normalizations[genre_lower]
        if genre_lower.startswith('r&b'):
            return 'R&B' + genre[3:] if len(genre) > 3 else 'R&B'
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
        if not field_value:
            return []
        try:
            wikicode = mwparserfromhell.parse(field_value)
            templates = wikicode.filter_templates()
            if templates:
                items = []
                for template in templates:
                    template_name = str(template.name).strip().lower()
                    if 'flatlist' in template_name or 'flat list' in template_name or 'hlist' in template_name:
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                items.append(param_value)
                        template_str = str(template)
                        body_match = re.search('\\|\\s*(.*)', template_str, re.DOTALL)
                        if body_match:
                            body_content = body_match.group(1)
                            body_content = re.sub('\\}\\}$', '', body_content)
                            lines = body_content.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and (line.startswith('*') or line.startswith('|')):
                                    item = re.sub('^[\\*\\|\\s]+', '', line)
                                    if item and item not in items:
                                        items.append(item)
                    else:
                        for param in template.params:
                            param_value = str(param.value).strip()
                            if param_value:
                                items.append(param_value)
                if items:
                    field_value = '\n'.join(items)
        except Exception:
            pass
        field_value = re.sub('\\[\\[([^\\]|]+\\|)?([^\\]]+)\\]\\]', '\\2', field_value)
        field_value = re.sub("'''?([^']+)'''?", '\\1', field_value)
        field_value = re.sub('<[^>]+>', '', field_value)
        field_value = re.sub('\\{\\{[^}]+\\}\\}', '', field_value)
        field_value = re.sub('<ref[^>]*>.*?</ref>', '', field_value, flags=re.DOTALL)
        field_value = re.sub('^\\s*[{}|]+\\s*', '', field_value)
        field_value = re.sub('\\s*[{}|]+\\s*$', '', field_value)
        items = re.split('[,;\\n•|]|<br\\s*/?>|\\s*–\\s*|\\s*—\\s*|\\s*-\\s*(?=[A-ZĂÂÊÔƠƯĐ])', field_value)
        cleaned_items = []
        for item in items:
            item = item.strip()
            item = re.sub('^[\\*\\s{}\\|]+', '', item)
            item = re.sub('[\\*\\s{}\\|]+$', '', item)
            item = re.sub('\\{\\{|\\}\\}', '', item)
            item = re.sub('\\s*\\(\\d{4}\\)\\s*$', '', item)
            item = clean_text(item)
            if item and len(item) > 1 and (len(item) < 200):
                artifact_patterns = ['}}', '{{', '|', '*', '']
                if item not in artifact_patterns:
                    cleaned_items.append(item)
        seen = set()
        unique_items = []
        for item in cleaned_items:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                unique_items.append(item)
        return unique_items[:30]

    def _validate_album_name(self, album_name: str) -> bool:
        if not album_name:
            return False
        album_name = album_name.strip()
        if len(album_name) <= 1:
            return False
        if len(album_name) < 4:
            return False
        if len(album_name) > 200:
            return False
        if album_name.isdigit():
            return False
        if re.match('^\\(\\d{4}\\)$', album_name):
            return False
        false_positives = ['yes', 'no', 'all', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'ref', 'web', 'review', 'citation', 'billboard', 'magic', 'week', 'list', 'index', 'title', 'name', 'album', 'song']
        if album_name.lower() in false_positives:
            return False
        if album_name[0] in ['(', '[', '{', '/', '\\', '-', '_', '|', '*']:
            return False
        if album_name[-1] in ['(', '[', '{', '/', '\\', '|', '*']:
            return False
        if '}}' in album_name or '{{' in album_name or '</ref>' in album_name:
            return False
        vietnamese_bad_patterns = ['^đầu tay\\s', '^tư\\s', '^ng\\s', '^của\\s', '^được\\s', '^là\\s', '^có\\s', '^trong\\s', '^với\\s', '^theo\\s', '^từ\\s', 'nh tên', 'a cô', 'ng tên', 'tên cô', '^\\s*album\\s+của\\s', '^\\s*đĩa nhạc\\s+của\\s']
        for pattern in vietnamese_bad_patterns:
            if re.search(pattern, album_name, re.IGNORECASE):
                return False
        incomplete_patterns = ['^to\\s[A-Z][a-z]+$', '^a\\s[A-Z][a-z]+$', '^an\\s[A-Z][a-z]+$', '^the\\s[A-Z][a-z]+$', '^by\\s[A-Z]', '^of\\s[A-Z]', '^from\\s[A-Z]', '^with\\s[A-Z]', '^album\\s+by\\s', '^album\\s+of\\s', '^song\\s+by\\s', '^single\\s+by\\s']
        for pattern in incomplete_patterns:
            if re.match(pattern, album_name, re.IGNORECASE):
                return False
        generic_words = ['book', 'chapter', 'part', 'section', 'volume', 'edition', 'version', 'demo', 'remix', 'edit', 'mix', 'cut', 'single', 'album', 'ep', 'lp', 'cd', 'tape', 'record']
        words = album_name.lower().split()
        if len(words) == 1 and words[0] in generic_words:
            return False
        if len(words) == 1 and len(album_name) < 8:
            return False
        overly_common = ['celebration', 'greatest hits', 'best of', 'collection', 'anthology', 'greatest hits album', 'best of album']
        if album_name.lower() in overly_common:
            return False
        if re.search('\\s+\\(album\\s+(của|by|of)', album_name, re.IGNORECASE):
            return False
        only_common_words = ['the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for']
        if len(words) <= 2 and all((word.lower() in only_common_words for word in words)):
            return False
        return True

    def parse_artist(self, artist_data: Dict) -> Dict[str, Any]:
        infobox_text = artist_data.get('infobox', '')
        parsed_infobox = self.parse_infobox(infobox_text)
        raw_albums = artist_data.get('albums', [])
        infobox_albums = parsed_infobox.get('albums', [])
        all_albums = []
        album_titles = set()
        for album in raw_albums:
            if isinstance(album, str):
                album_title = album.strip()
            elif isinstance(album, dict):
                album_title = album.get('title', '').strip()
            else:
                continue
            if album_title and self._validate_album_name(album_title):
                album_title_lower = album_title.lower()
                if album_title_lower not in album_titles:
                    album_titles.add(album_title_lower)
                    all_albums.append({'title': album_title})
        for album in infobox_albums:
            if isinstance(album, dict):
                album_title = album.get('title', '').strip()
            elif isinstance(album, str):
                album_title = album.strip()
            else:
                continue
            if album_title and self._validate_album_name(album_title):
                album_title_lower = album_title.lower()
                if album_title_lower not in album_titles:
                    album_titles.add(album_title_lower)
                    all_albums.append({'title': album_title})
        return {'name': artist_data.get('title', ''), 'url': artist_data.get('url', ''), 'summary': artist_data.get('summary', ''), 'genres': parsed_infobox.get('genres', []), 'instruments': parsed_infobox.get('instruments', []), 'active_years': parsed_infobox.get('active_years', ''), 'albums': all_albums, 'labels': parsed_infobox.get('labels', [])}

    def parse_all(self, input_path: str='data/raw/artists.json') -> List[Dict]:
        logger.info(f'Parsing artists from {input_path}...')
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                artists = json.load(f)
            parsed_artists = []
            for i, artist in enumerate(artists, 1):
                try:
                    parsed = self.parse_artist(artist)
                    parsed_artists.append(parsed)
                    if i % 100 == 0:
                        logger.info(f'Parsed {i}/{len(artists)} artists')
                except Exception as e:
                    logger.error(f'Error parsing artist {artist.get('title', 'unknown')}: {e}')
            logger.info(f'Successfully parsed {len(parsed_artists)} artists')
            return parsed_artists
        except Exception as e:
            logger.error(f'Error loading artists from {input_path}: {e}')
            return []

def parse_all(input_path: str='data/raw/artists.json', output_path: str='data/processed/parsed_artists.json') -> int:
    import os
    parser = InfoboxParser()
    parsed_artists = parser.parse_all(input_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_artists, f, ensure_ascii=False, indent=2)
    logger.info(f'Saved parsed data to {output_path}')
    return len(parsed_artists)
if __name__ == '__main__':
    parse_all()

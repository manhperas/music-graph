import json
import os
import re
from typing import List, Dict
import pandas as pd
from unidecode import unidecode
from data_collection.utils import logger

class DataCleaner:

    def __init__(self):
        self.pop_keywords = ['pop', 'nhạc pop', 'dance', 'r&b', 'soul']

    def load_parsed_data(self, input_path: str) -> pd.DataFrame:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            logger.info(f'Loaded {len(df)} artists from {input_path}')
            return df
        except Exception as e:
            logger.error(f'Error loading parsed data: {e}')
            return pd.DataFrame()

    def normalize_name(self, name: str) -> str:
        if not name:
            return ''
        name = name.strip()
        name = ' '.join(name.split())
        return name

    def normalize_label(self, label: str) -> str:
        if not label:
            return ''
        label = label.strip()
        label = ' '.join(label.split())
        suffixes = ['\\s*\\(record label\\)', '\\s*\\(label\\)', '\\s*\\(company\\)', '\\s*\\(music\\)', '\\s*\\(records\\)', '\\s*\\(record company\\)']
        for suffix in suffixes:
            label = re.sub(suffix, '', label, flags=re.IGNORECASE)
        label = label.strip('.,;:()[]{}')
        return label

    def create_similarity_key(self, name: str) -> str:
        if not name:
            return ''
        normalized = unidecode(name.lower())
        suffixes = ['\\s*\\(band\\)', '\\s*\\(singer\\)', '\\s*\\(artist\\)', '\\s*\\(musician\\)', '\\s*\\(group\\)', '\\s*\\(solo\\)', '\\s*\\(vocalist\\)', '\\s*\\(vocal\\)']
        for suffix in suffixes:
            normalized = re.sub(suffix, '', normalized)
        normalized = re.sub('[^\\w\\s]', '', normalized)
        normalized = ' '.join(normalized.split())
        return normalized

    def is_artist_name(self, name: str) -> bool:
        if not name:
            return False
        false_patterns = ['(album của', '(bài hát của', '(song của', '(single của', '(song by', '(album by', '(single by']
        for pattern in false_patterns:
            if pattern in name.lower():
                return False
        return True

    def is_pop_related(self, genres: List[str]) -> bool:
        if not genres:
            return True
        genres_text = ' '.join(genres).lower()
        return any((keyword in genres_text for keyword in self.pop_keywords))

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info('Cleaning artist data...')
        initial_count = len(df)
        df['name'] = df['name'].apply(self.normalize_name)
        df['similarity_key'] = df['name'].apply(self.create_similarity_key)
        exact_dupes = len(df) - len(df.drop_duplicates(subset=['name'], keep='first'))
        df = df.drop_duplicates(subset=['name'], keep='first')
        logger.info(f'Removed {exact_dupes} exact duplicates')
        before_similarity = len(df)
        df = df.drop_duplicates(subset=['similarity_key'], keep='first')
        similarity_dupes = before_similarity - len(df)
        if similarity_dupes > 0:
            logger.info(f'Removed {similarity_dupes} similarity-based duplicates')
        df = df[df['name'].str.len() > 0]
        before_filter = len(df)
        df['is_artist'] = df['name'].apply(self.is_artist_name)
        df = df[df['is_artist'] == True]
        logger.info(f'Removed {before_filter - len(df)} non-artist entries (songs/albums)')
        df['name_normalized'] = df['name'].apply(lambda x: unidecode(x).lower())
        df['is_pop'] = df['genres'].apply(self.is_pop_related)
        pop_count = df['is_pop'].sum()
        logger.info(f'Found {pop_count} pop-related artists out of {len(df)}')
        if pop_count < len(df) * 0.3:
            logger.warning('Pop filter would remove too many artists, keeping all')
            df['is_pop'] = True
        df = df[df['is_pop'] == True]
        df = df.drop(columns=['similarity_key'], errors='ignore')
        df['genres_str'] = df['genres'].apply(lambda x: '; '.join(x) if isinstance(x, list) else '')
        df['instruments_str'] = df['instruments'].apply(lambda x: '; '.join(x) if isinstance(x, list) else '')
        if 'labels' not in df.columns:
            df['labels'] = df.apply(lambda x: [], axis=1)

        def normalize_labels(labels):
            if not labels or not isinstance(labels, list):
                return ''
            normalized_labels = [self.normalize_label(label) for label in labels if label]
            normalized_labels = [label for label in normalized_labels if label]
            return '; '.join(normalized_labels)
        df['labels_str'] = df['labels'].apply(normalize_labels)
        logger.info(f'Cleaned data: {len(df)} artists remaining')
        logger.info(f'Total duplicates removed: {initial_count - len(df)}')
        return df

    def create_nodes_csv(self, df: pd.DataFrame, output_path: str):
        nodes_df = df[['name', 'genres_str', 'instruments_str', 'labels_str', 'active_years', 'url']].copy()
        nodes_df.columns = ['name', 'genres', 'instruments', 'labels', 'active_years', 'url']
        nodes_df.insert(0, 'id', range(len(nodes_df)))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        nodes_df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f'Saved {len(nodes_df)} nodes to {output_path}')

    def _validate_album_name(self, album_name: str) -> bool:
        if not album_name:
            return False
        album_name = album_name.strip()
        if len(album_name) < 4:
            return False
        if re.match('^[a-z]\\s+', album_name):
            return False
        vietnamese_incomplete = ['^nh\\s+', '^ng\\s+', '^của\\s+', '^trên\\s+', '^c\\s+', '^y\\s+', '^p\\s+', '^a\\s+[A-Z]', '^u\\s+tay\\s+']
        for pattern in vietnamese_incomplete:
            if re.match(pattern, album_name, re.IGNORECASE):
                return False
        if len(album_name) < 4:
            return False
        return True

    def extract_albums(self, df: pd.DataFrame) -> Dict:
        album_map = {}
        artist_id_map = {row['name']: idx for idx, row in df.iterrows()}
        skipped_count = 0
        for idx, row in df.iterrows():
            albums = row.get('albums', [])
            artist_name = row['name']
            artist_id = artist_id_map.get(artist_name, idx)
            if isinstance(albums, list):
                for album in albums:
                    if isinstance(album, dict):
                        album_title = album.get('title', '')
                    else:
                        album_title = str(album)
                    if album_title:
                        album_title = album_title.strip()
                        if not self._validate_album_name(album_title):
                            skipped_count += 1
                            continue
                        if album_title not in album_map:
                            album_map[album_title] = []
                        album_map[album_title].append(artist_id)
        logger.info(f'Extracted {len(album_map)} unique albums')
        if skipped_count > 0:
            logger.info(f'Skipped {skipped_count} invalid album names (parsing artifacts)')
        return album_map

    def save_albums_json(self, album_map: Dict, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(album_map, f, ensure_ascii=False, indent=2)
        logger.info(f'Saved album mapping to {output_path}')

def clean_all(input_path: str='data/processed/parsed_artists.json', nodes_output: str='data/processed/nodes.csv', albums_output: str='data/processed/albums.json') -> int:
    cleaner = DataCleaner()
    df = cleaner.load_parsed_data(input_path)
    if df.empty:
        logger.error('No data to clean')
        return 0
    df = cleaner.clean_dataframe(df)
    cleaner.create_nodes_csv(df, nodes_output)
    album_map = cleaner.extract_albums(df)
    cleaner.save_albums_json(album_map, albums_output)
    return len(df)
if __name__ == '__main__':
    clean_all()

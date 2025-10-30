"""Data cleaning and normalization module"""

import json
import os
import re
from typing import List, Dict
import pandas as pd
from unidecode import unidecode
from data_collection.utils import logger


class DataCleaner:
    """Clean and normalize artist data"""
    
    def __init__(self):
        self.pop_keywords = ['pop', 'nhạc pop', 'dance', 'r&b', 'soul']
    
    def load_parsed_data(self, input_path: str) -> pd.DataFrame:
        """Load parsed artist data into DataFrame"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            logger.info(f"Loaded {len(df)} artists from {input_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading parsed data: {e}")
            return pd.DataFrame()
    
    def normalize_name(self, name: str) -> str:
        """Normalize artist name for display"""
        if not name:
            return ""
        
        # Keep original name but clean it
        name = name.strip()
        
        # Remove extra whitespace
        name = " ".join(name.split())
        
        return name
    
    def normalize_label(self, label: str) -> str:
        """Normalize record label name"""
        if not label:
            return ""
        
        # Clean and normalize label name
        label = label.strip()
        
        # Remove extra whitespace
        label = " ".join(label.split())
        
        # Remove common suffixes that don't affect uniqueness
        suffixes = [
            r'\s*\(record label\)', r'\s*\(label\)', r'\s*\(company\)',
            r'\s*\(music\)', r'\s*\(records\)', r'\s*\(record company\)'
        ]
        for suffix in suffixes:
            label = re.sub(suffix, '', label, flags=re.IGNORECASE)
        
        # Remove leading/trailing special characters
        label = label.strip('.,;:()[]{}')
        
        return label
    
    def create_similarity_key(self, name: str) -> str:
        """Create a normalized key for duplicate detection"""
        if not name:
            return ""
        
        # Remove accents and special characters
        normalized = unidecode(name.lower())
        
        # Remove common suffixes that don't affect uniqueness
        suffixes = [
            r'\s*\(band\)', r'\s*\(singer\)', r'\s*\(artist\)',
            r'\s*\(musician\)', r'\s*\(group\)', r'\s*\(solo\)',
            r'\s*\(vocalist\)', r'\s*\(vocal\)'
        ]
        for suffix in suffixes:
            normalized = re.sub(suffix, '', normalized)
        
        # Remove special characters except spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Normalize whitespace
        normalized = " ".join(normalized.split())
        
        return normalized
    
    def is_artist_name(self, name: str) -> bool:
        """Check if name is actually an artist (not a song/album)"""
        if not name:
            return False
        
        # Filter out songs and albums with patterns like:
        # - "(album của ...)"
        # - "(bài hát của ...)"
        # - "(song của ...)"
        # - "(single của ...)"
        false_patterns = [
            '(album của',
            '(bài hát của',
            '(song của',
            '(single của',
            '(song by',
            '(album by',
            '(single by'
        ]
        
        for pattern in false_patterns:
            if pattern in name.lower():
                return False
        
        return True
    
    def is_pop_related(self, genres: List[str]) -> bool:
        """Check if artist is pop-related based on genres"""
        if not genres:
            return True  # Include artists without genre info
        
        genres_text = " ".join(genres).lower()
        return any(keyword in genres_text for keyword in self.pop_keywords)
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and filter the DataFrame"""
        logger.info("Cleaning artist data...")
        
        initial_count = len(df)
        
        # Normalize names first
        df['name'] = df['name'].apply(self.normalize_name)
        
        # Create similarity key for advanced duplicate detection
        df['similarity_key'] = df['name'].apply(self.create_similarity_key)
        
        # Remove duplicates based on exact name
        exact_dupes = len(df) - len(df.drop_duplicates(subset=['name'], keep='first'))
        df = df.drop_duplicates(subset=['name'], keep='first')
        logger.info(f"Removed {exact_dupes} exact duplicates")
        
        # Advanced duplicate detection using similarity key
        before_similarity = len(df)
        df = df.drop_duplicates(subset=['similarity_key'], keep='first')
        similarity_dupes = before_similarity - len(df)
        if similarity_dupes > 0:
            logger.info(f"Removed {similarity_dupes} similarity-based duplicates")
        
        # Filter out empty names
        df = df[df['name'].str.len() > 0]
        
        # Filter out songs/albums that are not actual artists
        before_filter = len(df)
        df['is_artist'] = df['name'].apply(self.is_artist_name)
        df = df[df['is_artist'] == True]
        logger.info(f"Removed {before_filter - len(df)} non-artist entries (songs/albums)")
        
        # Add normalized name for matching
        df['name_normalized'] = df['name'].apply(lambda x: unidecode(x).lower())
        
        # Filter pop-related artists
        df['is_pop'] = df['genres'].apply(self.is_pop_related)
        pop_count = df['is_pop'].sum()
        logger.info(f"Found {pop_count} pop-related artists out of {len(df)}")
        
        # Keep all artists if filtering would reduce count too much
        if pop_count < len(df) * 0.3:
            logger.warning("Pop filter would remove too many artists, keeping all")
            df['is_pop'] = True
        
        df = df[df['is_pop'] == True]
        
        # Drop similarity_key column (no longer needed)
        df = df.drop(columns=['similarity_key'], errors='ignore')
        
        # Convert list fields to strings for CSV export
        df['genres_str'] = df['genres'].apply(lambda x: "; ".join(x) if isinstance(x, list) else "")
        df['instruments_str'] = df['instruments'].apply(lambda x: "; ".join(x) if isinstance(x, list) else "")
        
        # Ensure labels column exists (if missing, create with empty lists)
        if 'labels' not in df.columns:
            df['labels'] = df.apply(lambda x: [], axis=1)
        
        # Normalize and convert labels to string format
        def normalize_labels(labels):
            if not labels or not isinstance(labels, list):
                return ""
            normalized_labels = [self.normalize_label(label) for label in labels if label]
            # Filter out empty labels after normalization
            normalized_labels = [label for label in normalized_labels if label]
            return "; ".join(normalized_labels)
        
        df['labels_str'] = df['labels'].apply(normalize_labels)
        
        logger.info(f"Cleaned data: {len(df)} artists remaining")
        logger.info(f"Total duplicates removed: {initial_count - len(df)}")
        return df
    
    def create_nodes_csv(self, df: pd.DataFrame, output_path: str):
        """Create nodes CSV for graph import"""
        nodes_df = df[['name', 'genres_str', 'instruments_str', 'labels_str', 'active_years', 'url']].copy()
        nodes_df.columns = ['name', 'genres', 'instruments', 'labels', 'active_years', 'url']
        
        # Add unique ID
        nodes_df.insert(0, 'id', range(len(nodes_df)))
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        nodes_df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Saved {len(nodes_df)} nodes to {output_path}")
    
    def _validate_album_name(self, album_name: str) -> bool:
        """Validate album name to filter out parsing artifacts"""
        if not album_name:
            return False
        
        album_name = album_name.strip()
        
        # Basic length checks
        if len(album_name) < 4:
            return False
        
        # Filter out names starting with single lowercase letter + space (parsing artifacts)
        # Examples: "n trên Pop Chronicles", "u tay Hybrid Theory", "c Sweetener"
        if re.match(r'^[a-z]\s+', album_name):
            return False
        
        # Filter out names starting with Vietnamese incomplete words
        # Examples: "nh ", "ng ", "của ", "trên "
        vietnamese_incomplete = [r'^nh\s+', r'^ng\s+', r'^của\s+', r'^trên\s+', 
                                r'^c\s+', r'^y\s+', r'^p\s+', r'^a\s+[A-Z]', r'^u\s+tay\s+']
        for pattern in vietnamese_incomplete:
            if re.match(pattern, album_name, re.IGNORECASE):
                return False
        
        # Filter out names that are too short after cleaning
        if len(album_name) < 4:
            return False
        
        return True
    
    def extract_albums(self, df: pd.DataFrame) -> Dict:
        """Extract album information and create artist-album relationships"""
        album_map = {}  # album_name -> [artist_ids]
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
                        # Normalize album title
                        album_title = album_title.strip()
                        
                        # Validate album name
                        if not self._validate_album_name(album_title):
                            skipped_count += 1
                            continue
                        
                        if album_title not in album_map:
                            album_map[album_title] = []
                        album_map[album_title].append(artist_id)
        
        logger.info(f"Extracted {len(album_map)} unique albums")
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} invalid album names (parsing artifacts)")
        return album_map
    
    def save_albums_json(self, album_map: Dict, output_path: str):
        """Save album mapping to JSON"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(album_map, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved album mapping to {output_path}")


def clean_all(input_path: str = "data/processed/parsed_artists.json",
              nodes_output: str = "data/processed/nodes.csv",
              albums_output: str = "data/processed/albums.json") -> int:
    """Main function to clean and process all data"""
    cleaner = DataCleaner()
    
    # Load and clean data
    df = cleaner.load_parsed_data(input_path)
    if df.empty:
        logger.error("No data to clean")
        return 0
    
    df = cleaner.clean_dataframe(df)
    
    # Create nodes CSV
    cleaner.create_nodes_csv(df, nodes_output)
    
    # Extract and save albums
    album_map = cleaner.extract_albums(df)
    cleaner.save_albums_json(album_map, albums_output)
    
    return len(df)


if __name__ == "__main__":
    clean_all()



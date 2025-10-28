"""Data cleaning and normalization module"""

import json
import os
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
        """Normalize artist name"""
        if not name:
            return ""
        
        # Keep original name but clean it
        name = name.strip()
        
        # Remove extra whitespace
        name = " ".join(name.split())
        
        return name
    
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
        
        # Remove duplicates based on name
        df = df.drop_duplicates(subset=['name'], keep='first')
        logger.info(f"Removed {initial_count - len(df)} duplicates")
        
        # Normalize names
        df['name'] = df['name'].apply(self.normalize_name)
        
        # Filter out empty names
        df = df[df['name'].str.len() > 0]
        
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
        
        # Convert list fields to strings for CSV export
        df['genres_str'] = df['genres'].apply(lambda x: "; ".join(x) if isinstance(x, list) else "")
        df['instruments_str'] = df['instruments'].apply(lambda x: "; ".join(x) if isinstance(x, list) else "")
        
        logger.info(f"Cleaned data: {len(df)} artists remaining")
        return df
    
    def create_nodes_csv(self, df: pd.DataFrame, output_path: str):
        """Create nodes CSV for graph import"""
        nodes_df = df[['name', 'genres_str', 'instruments_str', 'active_years', 'url']].copy()
        nodes_df.columns = ['name', 'genres', 'instruments', 'active_years', 'url']
        
        # Add unique ID
        nodes_df.insert(0, 'id', range(len(nodes_df)))
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        nodes_df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Saved {len(nodes_df)} nodes to {output_path}")
    
    def extract_albums(self, df: pd.DataFrame) -> Dict:
        """Extract album information and create artist-album relationships"""
        album_map = {}  # album_name -> [artist_ids]
        artist_id_map = {row['name']: idx for idx, row in df.iterrows()}
        
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
                    
                    if album_title and len(album_title) > 1:
                        # Normalize album title
                        album_title = album_title.strip()
                        
                        if album_title not in album_map:
                            album_map[album_title] = []
                        album_map[album_title].append(artist_id)
        
        logger.info(f"Extracted {len(album_map)} unique albums")
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



#!/usr/bin/env python3
"""
Task 3.1: Extract Unique Genres
Task 3.2: Create HAS_GENRE Relationships
Load parsed artists, extract all genres, normalize, deduplicate, and create Genre nodes CSV
Then create HAS_GENRE relationships: Artist → Genre and Album → Genre
"""

import json
import re
import os
import sys
from pathlib import Path
from typing import List, Set, Dict, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import logging

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GenreExtractor:
    """Extract and normalize unique genres from parsed artists"""
    
    def __init__(self):
        self.genre_stats = defaultdict(int)
        
        # Genre normalization mappings (from parser.py)
        self.genre_normalizations = {
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
    
    def load_parsed_artists(self, input_path: str) -> List[Dict]:
        """Load parsed artists from JSON file"""
        logger.info(f"Loading parsed artists from {input_path}...")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                artists = json.load(f)
            
            logger.info(f"✓ Loaded {len(artists)} artists")
            return artists
            
        except FileNotFoundError:
            logger.error(f"✗ File not found: {input_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"✗ Invalid JSON in {input_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"✗ Error loading artists: {e}")
            raise
    
    def extract_all_genres(self, artists: List[Dict]) -> List[str]:
        """Extract all genres from artists"""
        logger.info("Extracting genres from all artists...")
        
        all_genres = []
        artists_with_genres = 0
        
        for artist in artists:
            genres = artist.get('genres', [])
            if genres and isinstance(genres, list):
                artists_with_genres += 1
                for genre in genres:
                    if genre:  # Skip empty strings
                        all_genres.append(genre)
        
        logger.info(f"✓ Extracted {len(all_genres)} genre entries from {artists_with_genres} artists")
        return all_genres
    
    def validate_genre(self, genre: str) -> bool:
        """Validate that a genre string is actually a valid genre name"""
        if not genre:
            return False
        
        genre = genre.strip()
        
        # Basic length checks
        if len(genre) < 2:
            return False
        
        if len(genre) > 100:
            return False
        
        # Filter out URLs
        if genre.startswith('http://') or genre.startswith('https://'):
            return False
        
        if 'http' in genre.lower() or 'www.' in genre.lower():
            return False
        
        # Filter out dates (YYYY-MM-DD, YYYY, DD Month YYYY, etc.)
        if re.match(r'^\d{4}(-\d{2}-\d{2})?$', genre):
            return False
        
        # Filter out Vietnamese date patterns: "20 Tháng 3 Năm 2017", "Ngày 20 Tháng 12 Năm 2017"
        if re.search(r'(Tháng|Năm|Ngày).*\d{4}', genre, re.IGNORECASE):
            return False
        
        # Filter out date patterns: "1 February 2009", "16 June 2011"
        if re.search(r'^\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', genre, re.IGNORECASE):
            return False
        
        # Filter out common artifacts
        artifacts = ['}}', '{{', '|', '*', '', 'Dead', 'Https://']
        if genre in artifacts:
            return False
        
        # Filter out names that start with special characters (incomplete extractions)
        if genre[0] in ['(', '[', '{', '/', '\\', '-', '_', '|', '*']:
            return False
        
        # Filter out names that end with incomplete characters
        if genre[-1] in ['(', '[', '{', '/', '\\', '|', '*']:
            return False
        
        # Filter out wiki markup artifacts
        if '}}' in genre or '{{' in genre or '</ref>' in genre:
            return False
        
        # Filter out Vietnamese common words that are not genres
        vietnamese_non_genres = [
            'Tháng', 'Năm', 'ngày', 'Https://www',
            'Https://', 'Rolling Stone', 'Dead'
        ]
        if genre in vietnamese_non_genres:
            return False
        
        # Filter out English common words that are not genres
        english_non_genres = [
            'Dead', 'Review', 'Citation', 'Reference', 'Link',
            'Source', 'Year', 'Date', 'Month', 'Day'
        ]
        if genre in english_non_genres:
            return False
        
        # Filter out names that look like article titles or references
        if 'Is ' in genre and 'Redefining' in genre:
            return False
        
        # Filter out article titles and references
        article_patterns = [
            r'^The .+ Of .+',  # "The Unlikely Resurgence Of Rap Rock"
            r'^.+: .+',  # "Blue-eyed Soul: Encyclopedia Of Modern Music"
            r'Is .+ Redefining',  # Article titles
            r'\.com$',  # URLs/domains
            r'\.org$',
            r'Pitchfork',
            r'Rolling Stone',
            r'The Sunday Times',
        ]
        for pattern in article_patterns:
            if re.search(pattern, genre, re.IGNORECASE):
                return False
        
        # Filter out genres that are too long (likely article titles)
        if len(genre) > 50:
            return False
        
        # Filter out single words that are too short or too generic
        words = genre.split()  # Keep original case for title checking
        words_lower = [w.lower() for w in words]
        
        if len(words) == 1:
            # Single word genres should be at least 3 characters
            if len(genre) < 3:
                return False
            # Filter out common non-genre single words
            non_genre_words = ['dan', 'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for']
            if genre.lower() in non_genre_words:
                return False
        
        # Filter out known non-genre entries (blacklist)
        non_genre_blacklist = ['bethonie', 'butler', 'washington post', 'washington', 'post']
        if genre.lower() in non_genre_blacklist:
            return False
        
        # Filter out names that look like people or places (capitalized words that aren't genres)
        # Common patterns: "Washington Post", "Bethonie", "Butler"
        if len(words) == 2 and words[0][0].isupper() and words[1][0].isupper():
            # Check if it looks like a proper noun (both words capitalized)
            # Exclude known genre patterns
            known_genre_patterns = ['Blue Eyed', 'Hip Hop', 'Pop Rock', 'Rock Pop', 'Folk Pop', 
                                   'Funk Pop', 'Soul Pop', 'Jazz Pop', 'Rock Soul', 'Pop Soul']
            # Check if it matches any known genre pattern (case-insensitive)
            genre_lower_check = genre.lower()
            is_known_genre = any(pattern.lower() in genre_lower_check for pattern in known_genre_patterns)
            if not is_known_genre:
                # Additional check: if both words are common English words, it's likely not a genre
                common_words = ['washington', 'post', 'bethonie', 'butler', 'john', 'smith', 'davis', 
                               'times', 'sunday', 'rolling', 'stone', 'pitchfork']
                # Check if it matches known non-genre patterns
                if any(word.lower() in common_words for word in words):
                    # But allow if it's part of a known genre pattern
                    if not is_known_genre:
                        return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-ZÀ-ỹ]', genre):
            return False
        
        return True
    
    def normalize_genre(self, genre: str) -> str:
        """Normalize genre name"""
        if not genre:
            return ""
        
        genre = genre.strip()
        
        # Remove concatenated words first: "pop Rockpoprock" -> "pop Rock poprock"
        genre = re.sub(r'([a-z])([A-Z])', r'\1 \2', genre)
        
        # Remove bullet points and special separators
        genre = re.sub(r'[·•]', ' ', genre)
        genre = ' '.join(genre.split())  # Normalize whitespace
        
        # Apply normalization mappings
        genre_lower = genre.lower()
        if genre_lower in self.genre_normalizations:
            genre = self.genre_normalizations[genre_lower]
        
        # Handle R&B patterns
        if genre_lower.startswith('r&b'):
            genre = 'R&B' + genre[3:] if len(genre) > 3 else 'R&B'
        
        # Capitalize properly: each word gets proper capitalization
        words = genre.split()
        normalized_words = []
        for word in words:
            word_lower = word.lower()
            # Keep common acronyms lowercase ONLY if they're standalone
            # But capitalize "pop" if it's part of a compound genre like "pop Rock"
            if len(words) == 1 and word_lower in ['r&b', 'pop', 'edm', 'idm']:
                normalized_words.append(word_lower)
            elif word_lower == 'r&b':
                # Always keep R&B as R&B
                normalized_words.append('R&B')
            else:
                # Capitalize first letter of each word (including "pop" in compound genres)
                normalized_words.append(word.capitalize())
        
        normalized = ' '.join(normalized_words)
        
        # Additional cleaning
        normalized = normalized.strip()
        
        # Remove any remaining artifacts
        normalized = re.sub(r'^[\*\s{}\|]+', '', normalized)
        normalized = re.sub(r'[\*\s{}\|]+$', '', normalized)
        
        return normalized
    
    def extract_and_normalize_genres(self, artists: List[Dict]) -> List[str]:
        """Extract all genres, normalize, and validate"""
        logger.info("Extracting and normalizing genres...")
        
        all_genres = self.extract_all_genres(artists)
        
        # Normalize and validate genres
        normalized_genres = []
        skipped_count = 0
        
        for genre in all_genres:
            # Normalize
            normalized = self.normalize_genre(genre)
            
            # Validate
            if normalized and self.validate_genre(normalized):
                normalized_genres.append(normalized)
                self.genre_stats[normalized] += 1
            else:
                skipped_count += 1
        
        logger.info(f"✓ Normalized {len(normalized_genres)} genre entries")
        logger.info(f"  Skipped {skipped_count} invalid entries")
        
        return normalized_genres
    
    def deduplicate_genres(self, genres: List[str]) -> List[str]:
        """Remove duplicates while preserving order, case-insensitive"""
        logger.info("Deduplicating genres...")
        
        seen = set()
        unique_genres = []
        
        for genre in genres:
            genre_lower = genre.lower()
            if genre_lower not in seen:
                seen.add(genre_lower)
                unique_genres.append(genre)
        
        logger.info(f"✓ Found {len(unique_genres)} unique genres (from {len(genres)} entries)")
        
        return unique_genres
    
    def create_genres_csv(self, genres: List[str], output_path: str):
        """Create Genre nodes CSV file"""
        logger.info(f"Creating Genre nodes CSV: {output_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create DataFrame
        genres_data = []
        for idx, genre in enumerate(genres):
            genres_data.append({
                'id': f'genre_{idx}',
                'name': genre
            })
        
        df = pd.DataFrame(genres_data)
        
        # Save to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"✓ Created CSV with {len(df)} Genre nodes")
        logger.info(f"  Output: {output_path}")
        
        # Print some statistics
        logger.info("\nGenre Statistics:")
        logger.info(f"  Total unique genres: {len(genres)}")
        
        # Show top genres by frequency
        if self.genre_stats:
            top_genres = sorted(self.genre_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            logger.info("\n  Top 10 genres by frequency:")
            for genre, count in top_genres:
                logger.info(f"    - {genre}: {count} artists")
        
        return df
    
    def process(self, input_path: str = "data/processed/parsed_artists.json",
                output_path: str = "data/migrations/genres.csv"):
        """Main processing function"""
        logger.info("=" * 60)
        logger.info("Task 3.1: Extract Unique Genres")
        logger.info("=" * 60)
        
        try:
            # Step 1: Load parsed artists
            artists = self.load_parsed_artists(input_path)
            
            # Step 2: Extract and normalize genres
            normalized_genres = self.extract_and_normalize_genres(artists)
            
            # Step 3: Deduplicate
            unique_genres = self.deduplicate_genres(normalized_genres)
            
            # Step 4: Create CSV
            df = self.create_genres_csv(unique_genres, output_path)
            
            logger.info("\n" + "=" * 60)
            logger.info("✓ Task 3.1 completed successfully!")
            logger.info("=" * 60)
            
            return df
            
        except Exception as e:
            logger.error(f"\n✗ Task 3.1 failed: {e}")
            raise


class GenreRelationshipCreator:
    """Create HAS_GENRE relationships: Artist → Genre and Album → Genre"""
    
    def __init__(self, genres_csv_path: str = "data/migrations/genres.csv"):
        """Initialize with genre extractor utilities"""
        self.genre_extractor = GenreExtractor()
        self.genres_csv_path = genres_csv_path
        self.genre_map = {}  # genre_name (normalized) -> genre_id
        self.genre_name_map = {}  # genre_id -> genre_name
        
    def load_genres(self) -> Dict[str, str]:
        """Load genre nodes from CSV and create mapping"""
        logger.info(f"Loading genres from {self.genres_csv_path}...")
        
        if not os.path.exists(self.genres_csv_path):
            logger.error(f"✗ Genres CSV not found: {self.genres_csv_path}")
            logger.error("  Please run Task 3.1 first to create genres.csv")
            raise FileNotFoundError(f"Genres CSV not found: {self.genres_csv_path}")
        
        try:
            df = pd.read_csv(self.genres_csv_path, encoding='utf-8')
            
            # Create mappings: normalized name -> id and id -> name
            for _, row in df.iterrows():
                genre_id = row['id']
                genre_name = row['name']
                
                # Normalize genre name for matching
                normalized = self.genre_extractor.normalize_genre(genre_name)
                normalized_lower = normalized.lower()
                
                self.genre_map[normalized_lower] = genre_id
                self.genre_name_map[genre_id] = genre_name
            
            logger.info(f"✓ Loaded {len(self.genre_map)} genres")
            return self.genre_map
            
        except Exception as e:
            logger.error(f"✗ Error loading genres: {e}")
            raise
    
    def parse_artist_genres(self, artist: Dict) -> List[str]:
        """Parse and normalize genres from an artist"""
        genres = artist.get('genres', [])
        if not genres or not isinstance(genres, list):
            return []
        
        normalized_genres = []
        for genre in genres:
            if genre:
                normalized = self.genre_extractor.normalize_genre(genre)
                if normalized and self.genre_extractor.validate_genre(normalized):
                    normalized_genres.append(normalized)
        
        return normalized_genres
    
    def create_artist_genre_relationships(self, artists: List[Dict], 
                                         artist_id_map: Dict[str, str]) -> List[Dict]:
        """Create HAS_GENRE relationships for artists"""
        logger.info("Creating Artist → Genre relationships...")
        
        relationships = []
        artists_with_genres = 0
        artists_without_genres = 0
        relationships_created = 0
        
        for artist in artists:
            artist_name = artist.get('name', '')
            artist_id = artist_id_map.get(artist_name)
            
            if not artist_id:
                continue
            
            # Parse genres from artist
            genres = self.parse_artist_genres(artist)
            
            if not genres:
                artists_without_genres += 1
                continue
            
            artists_with_genres += 1
            
            # Create relationship for each genre
            for genre in genres:
                genre_lower = genre.lower()
                genre_id = self.genre_map.get(genre_lower)
                
                if genre_id:
                    relationships.append({
                        'from': artist_id,
                        'to': genre_id,
                        'type': 'HAS_GENRE',
                        'from_type': 'Artist',
                        'to_type': 'Genre'
                    })
                    relationships_created += 1
                else:
                    logger.warning(f"  Genre '{genre}' not found in genre map for artist '{artist_name}'")
        
        logger.info(f"✓ Created {relationships_created} Artist → Genre relationships")
        logger.info(f"  Artists with genres: {artists_with_genres}")
        logger.info(f"  Artists without genres: {artists_without_genres}")
        
        return relationships
    
    def create_album_genre_relationships(self, albums_json: Dict, 
                                       artists: List[Dict],
                                       artist_id_map: Dict[str, str],
                                       album_id_map: Dict[str, str]) -> List[Dict]:
        """Create HAS_GENRE relationships for albums from their artists' genres"""
        logger.info("Creating Album → Genre relationships...")
        
        relationships = []
        albums_with_genres = 0
        albums_without_genres = 0
        relationships_created = 0
        
        # Create reverse mapping: numeric ID -> artist name
        # albums.json uses numeric IDs (0, 1, 2...) which correspond to row indices
        numeric_id_to_name = {}
        if artist_id_map:
            # If we have CSV IDs, we need to map them back
            # Load artists CSV to get numeric ID -> name mapping
            artists_csv_path = None
            for path in ["data/processed/artists.csv", "data/processed/nodes.csv"]:
                if os.path.exists(path):
                    artists_csv_path = path
                    break
            
            if artists_csv_path:
                try:
                    df = pd.read_csv(artists_csv_path, encoding='utf-8')
                    for idx, row in df.iterrows():
                        numeric_id_to_name[idx] = row['name']
                    logger.info(f"  Created numeric ID mapping for {len(numeric_id_to_name)} artists")
                except Exception as e:
                    logger.warning(f"  Could not create numeric ID mapping: {e}")
        
        # Fallback: create mapping from parsed artists list
        if not numeric_id_to_name:
            for idx, artist in enumerate(artists):
                numeric_id_to_name[idx] = artist.get('name', '')
        
        for album_title, artist_ids in albums_json.items():
            album_id = album_id_map.get(album_title)
            
            if not album_id:
                continue
            
            # Collect all genres from artists that perform on this album
            album_genres = set()
            
            for numeric_id in artist_ids:
                # Get artist name from numeric ID
                artist_name = numeric_id_to_name.get(numeric_id)
                
                if not artist_name:
                    continue
                
                # Find artist in parsed artists list
                artist = next((a for a in artists if a.get('name') == artist_name), None)
                
                if not artist:
                    continue
                
                # Get artist genres
                genres = self.parse_artist_genres(artist)
                album_genres.update(genres)
            
            if not album_genres:
                albums_without_genres += 1
                continue
            
            albums_with_genres += 1
            
            # Create relationship for each genre
            for genre in album_genres:
                genre_lower = genre.lower()
                genre_id = self.genre_map.get(genre_lower)
                
                if genre_id:
                    # Avoid duplicates
                    rel_exists = any(
                        r['from'] == album_id and r['to'] == genre_id 
                        for r in relationships
                    )
                    
                    if not rel_exists:
                        relationships.append({
                            'from': album_id,
                            'to': genre_id,
                            'type': 'HAS_GENRE',
                            'from_type': 'Album',
                            'to_type': 'Genre'
                        })
                        relationships_created += 1
        
        logger.info(f"✓ Created {relationships_created} Album → Genre relationships")
        logger.info(f"  Albums with genres: {albums_with_genres}")
        logger.info(f"  Albums without genres: {albums_without_genres}")
        
        return relationships
    
    def load_artist_id_map(self, artists_csv_path: str = "data/processed/artists.csv") -> Dict[str, str]:
        """Load artist name to ID mapping from CSV"""
        logger.info(f"Loading artist ID map from {artists_csv_path}...")
        
        if not os.path.exists(artists_csv_path):
            logger.warning(f"Artists CSV not found: {artists_csv_path}")
            logger.warning("  Will try to create ID mapping from parsed artists")
            return {}
        
        try:
            df = pd.read_csv(artists_csv_path, encoding='utf-8')
            artist_map = {}
            
            for _, row in df.iterrows():
                artist_id = row['id']
                artist_name = row['name']
                artist_map[artist_name] = artist_id
            
            logger.info(f"✓ Loaded {len(artist_map)} artist IDs")
            return artist_map
            
        except Exception as e:
            logger.warning(f"Error loading artist IDs: {e}")
            return {}
    
    def load_album_id_map(self, albums_csv_path: str = "data/processed/albums.csv") -> Dict[str, str]:
        """Load album title to ID mapping from CSV"""
        logger.info(f"Loading album ID map from {albums_csv_path}...")
        
        if not os.path.exists(albums_csv_path):
            logger.warning(f"Albums CSV not found: {albums_csv_path}")
            return {}
        
        try:
            df = pd.read_csv(albums_csv_path, encoding='utf-8')
            album_map = {}
            
            for _, row in df.iterrows():
                album_id = row['id']
                album_title = row['title']
                album_map[album_title] = album_id
            
            logger.info(f"✓ Loaded {len(album_map)} album IDs")
            return album_map
            
        except Exception as e:
            logger.warning(f"Error loading album IDs: {e}")
            return {}
    
    def create_relationships_csv(self, relationships: List[Dict], 
                                output_path: str) -> pd.DataFrame:
        """Create CSV file with HAS_GENRE relationships"""
        logger.info(f"Creating HAS_GENRE relationships CSV: {output_path}")
        
        if not relationships:
            logger.warning("No relationships to export")
            return pd.DataFrame()
        
        df = pd.DataFrame(relationships)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Log statistics
        logger.info(f"✓ Created CSV with {len(df)} HAS_GENRE relationships")
        logger.info(f"  Output: {output_path}")
        
        # Breakdown by type
        if 'from_type' in df.columns:
            type_counts = df.groupby('from_type').size()
            logger.info("\n  Relationships by type:")
            for from_type, count in type_counts.items():
                logger.info(f"    - {from_type} → Genre: {count}")
        
        return df
    
    def validate_relationships(self, relationships: List[Dict]) -> Tuple[int, int]:
        """Validate relationships and return valid/invalid counts"""
        logger.info("Validating relationships...")
        
        valid_count = 0
        invalid_count = 0
        
        for rel in relationships:
            # Check required fields
            if not all(key in rel for key in ['from', 'to', 'type']):
                invalid_count += 1
                continue
            
            # Check relationship type
            if rel['type'] != 'HAS_GENRE':
                invalid_count += 1
                continue
            
            # Check that 'to' is a genre ID
            if not rel['to'].startswith('genre_'):
                invalid_count += 1
                continue
            
            valid_count += 1
        
        logger.info(f"✓ Validated {len(relationships)} relationships")
        logger.info(f"  Valid: {valid_count}")
        logger.info(f"  Invalid: {invalid_count}")
        
        return valid_count, invalid_count
    
    def import_to_neo4j(self, relationships_csv_path: str,
                       config_path: str = "config/neo4j_config.json"):
        """Import HAS_GENRE relationships to Neo4j"""
        logger.info("=" * 60)
        logger.info("Importing HAS_GENRE relationships to Neo4j")
        logger.info("=" * 60)
        
        if not os.path.exists(relationships_csv_path):
            logger.error(f"✗ Relationships CSV not found: {relationships_csv_path}")
            raise FileNotFoundError(f"Relationships CSV not found: {relationships_csv_path}")
        
        try:
            # Import Neo4j modules
            from neo4j import GraphDatabase
            from dotenv import load_dotenv
            
            # Load config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load password from environment
            load_dotenv()
            password = os.getenv('NEO4J_PASS', 'password')
            
            # Create driver
            driver = GraphDatabase.driver(
                config['uri'],
                auth=(config['user'], password)
            )
            
            logger.info(f"Connected to Neo4j at {config['uri']}")
            
            # Load relationships
            df = pd.read_csv(relationships_csv_path, encoding='utf-8')
            
            # Create Genre constraint if it doesn't exist
            with driver.session(database=config.get('database', 'neo4j')) as session:
                try:
                    session.run("""
                        CREATE CONSTRAINT genre_id IF NOT EXISTS
                        FOR (g:Genre) REQUIRE g.id IS UNIQUE
                    """)
                    logger.info("Created constraint for Genre.id")
                except Exception as e:
                    logger.warning(f"Could not create Genre constraint: {e}")
                
                # Import Genre nodes if they don't exist
                if os.path.exists(self.genres_csv_path):
                    logger.info("Checking if Genre nodes exist...")
                    result = session.run("MATCH (g:Genre) RETURN count(g) AS count")
                    genre_count = result.single()['count']
                    
                    if genre_count == 0:
                        logger.info("Importing Genre nodes...")
                        genres_df = pd.read_csv(self.genres_csv_path, encoding='utf-8')
                        genres = genres_df.to_dict('records')
                        
                        batch_size = 500
                        for i in range(0, len(genres), batch_size):
                            batch = genres[i:i + batch_size]
                            
                            session.run("""
                                UNWIND $genres AS genre
                                CREATE (g:Genre {
                                    id: genre.id,
                                    name: genre.name
                                })
                            """, genres=batch)
                            
                            logger.info(f"Imported genres batch {i//batch_size + 1}: {len(batch)} nodes")
                        
                        logger.info(f"✓ Imported {len(genres)} Genre nodes")
                    else:
                        logger.info(f"✓ Genre nodes already exist ({genre_count} nodes)")
            
            # Import relationships
            relationships = df.to_dict('records')
            
            # Separate by from_type
            artist_relationships = [r for r in relationships if r.get('from_type') == 'Artist']
            album_relationships = [r for r in relationships if r.get('from_type') == 'Album']
            
            with driver.session(database=config.get('database', 'neo4j')) as session:
                batch_size = 1000
                
                # Import Artist → Genre relationships
                if artist_relationships:
                    logger.info(f"Importing {len(artist_relationships)} Artist → Genre relationships...")
                    for i in range(0, len(artist_relationships), batch_size):
                        batch = artist_relationships[i:i + batch_size]
                        
                        session.run("""
                            UNWIND $edges AS edge
                            MATCH (from:Artist {id: edge.from})
                            MATCH (to:Genre {id: edge.to})
                            MERGE (from)-[:HAS_GENRE]->(to)
                        """, edges=batch)
                        
                        logger.info(f"Imported batch {i//batch_size + 1}: {len(batch)} relationships")
                    
                    logger.info(f"✓ Imported {len(artist_relationships)} Artist → Genre relationships")
                
                # Import Album → Genre relationships
                if album_relationships:
                    logger.info(f"Importing {len(album_relationships)} Album → Genre relationships...")
                    for i in range(0, len(album_relationships), batch_size):
                        batch = album_relationships[i:i + batch_size]
                        
                        session.run("""
                            UNWIND $edges AS edge
                            MATCH (from:Album {id: edge.from})
                            MATCH (to:Genre {id: edge.to})
                            MERGE (from)-[:HAS_GENRE]->(to)
                        """, edges=batch)
                        
                        logger.info(f"Imported batch {i//batch_size + 1}: {len(batch)} relationships")
                    
                    logger.info(f"✓ Imported {len(album_relationships)} Album → Genre relationships")
            
            # Verify import
            with driver.session(database=config.get('database', 'neo4j')) as session:
                result = session.run("""
                    MATCH ()-[r:HAS_GENRE]->()
                    RETURN count(r) AS count
                """)
                count = result.single()['count']
                logger.info(f"✓ Total HAS_GENRE relationships in Neo4j: {count}")
            
            driver.close()
            logger.info("\n" + "=" * 60)
            logger.info("✓ Neo4j import completed successfully!")
            logger.info("=" * 60)
            
        except ImportError:
            logger.error("✗ Neo4j driver not installed. Install with: pip install neo4j python-dotenv")
            raise
        except Exception as e:
            logger.error(f"\n✗ Neo4j import failed: {e}")
            raise
    
    def process(self, 
               parsed_artists_path: str = "data/processed/parsed_artists.json",
               albums_json_path: str = "data/processed/albums.json",
               artists_csv_path: str = "data/processed/artists.csv",
               albums_csv_path: str = "data/processed/albums.csv",
               output_path: str = "data/migrations/has_genre_relationships.csv"):
        """Main processing function for Task 3.2"""
        logger.info("=" * 60)
        logger.info("Task 3.2: Create HAS_GENRE Relationships")
        logger.info("=" * 60)
        
        try:
            # Step 1: Load genres
            self.load_genres()
            
            # Step 2: Load parsed artists
            artists = self.genre_extractor.load_parsed_artists(parsed_artists_path)
            
            # Step 3: Load artist and album ID maps
            artist_id_map = self.load_artist_id_map(artists_csv_path)
            album_id_map = self.load_album_id_map(albums_csv_path)
            
            # Step 4: Load albums JSON
            logger.info(f"Loading albums from {albums_json_path}...")
            if not os.path.exists(albums_json_path):
                logger.warning(f"Albums JSON not found: {albums_json_path}")
                albums_json = {}
            else:
                with open(albums_json_path, 'r', encoding='utf-8') as f:
                    albums_json = json.load(f)
                logger.info(f"✓ Loaded {len(albums_json)} albums")
            
            # Step 5: Create Artist → Genre relationships
            artist_relationships = self.create_artist_genre_relationships(
                artists, artist_id_map
            )
            
            # Step 6: Create Album → Genre relationships
            album_relationships = self.create_album_genre_relationships(
                albums_json, artists, artist_id_map, album_id_map
            )
            
            # Step 7: Combine relationships
            all_relationships = artist_relationships + album_relationships
            
            # Step 8: Validate relationships
            valid_count, invalid_count = self.validate_relationships(all_relationships)
            
            # Step 9: Create CSV
            df = self.create_relationships_csv(all_relationships, output_path)
            
            logger.info("\n" + "=" * 60)
            logger.info("✓ Task 3.2 completed successfully!")
            logger.info(f"  Total HAS_GENRE relationships: {len(all_relationships)}")
            logger.info(f"  Artist → Genre: {len(artist_relationships)}")
            logger.info(f"  Album → Genre: {len(album_relationships)}")
            logger.info("=" * 60)
            
            return df
            
        except Exception as e:
            logger.error(f"\n✗ Task 3.2 failed: {e}")
            raise


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract genres and create HAS_GENRE relationships",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tasks:
  3.1  Extract unique genres from parsed artists
  3.2  Create HAS_GENRE relationships (Artist → Genre, Album → Genre)
        """
    )
    
    subparsers = parser.add_subparsers(dest='task', help='Task to run')
    
    # Task 3.1 parser
    parser_31 = subparsers.add_parser('3.1', help='Extract unique genres')
    parser_31.add_argument("--input", "-i", 
                          default="data/processed/parsed_artists.json",
                          help="Path to parsed artists JSON file")
    parser_31.add_argument("--output", "-o",
                          default="data/migrations/genres.csv",
                          help="Path to output CSV file")
    
    # Task 3.2 parser
    parser_32 = subparsers.add_parser('3.2', help='Create HAS_GENRE relationships')
    parser_32.add_argument("--parsed-artists", "-pa",
                          default="data/processed/parsed_artists.json",
                          help="Path to parsed artists JSON file")
    parser_32.add_argument("--albums-json", "-aj",
                          default="data/processed/albums.json",
                          help="Path to albums JSON file")
    parser_32.add_argument("--artists-csv", "-ac",
                          default="data/processed/artists.csv",
                          help="Path to artists CSV file")
    parser_32.add_argument("--albums-csv", "-al",
                          default="data/processed/albums.csv",
                          help="Path to albums CSV file")
    parser_32.add_argument("--genres-csv", "-gc",
                          default="data/migrations/genres.csv",
                          help="Path to genres CSV file")
    parser_32.add_argument("--output", "-o",
                          default="data/migrations/has_genre_relationships.csv",
                          help="Path to output CSV file")
    parser_32.add_argument("--import-neo4j", "-neo4j",
                          action="store_true",
                          help="Import relationships to Neo4j after creating CSV")
    parser_32.add_argument("--neo4j-config", "-nc",
                          default="config/neo4j_config.json",
                          help="Path to Neo4j config file")
    
    args = parser.parse_args()
    
    if args.task == '3.1':
        extractor = GenreExtractor()
        extractor.process(args.input, args.output)
    elif args.task == '3.2':
        creator = GenreRelationshipCreator(genres_csv_path=args.genres_csv)
        creator.process(
            parsed_artists_path=args.parsed_artists,
            albums_json_path=args.albums_json,
            artists_csv_path=args.artists_csv,
            albums_csv_path=args.albums_csv,
            output_path=args.output
        )
        
        # Import to Neo4j if requested
        if args.import_neo4j:
            creator.import_to_neo4j(
                relationships_csv_path=args.output,
                config_path=args.neo4j_config
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


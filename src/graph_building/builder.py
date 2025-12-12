"""Graph building module using NetworkX"""

import json
import os
from typing import Dict, List, Tuple, Optional
import pandas as pd
import networkx as nx
from data_collection.utils import logger, clean_text


class GraphBuilder:
    """Build graph network from processed data"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.artist_nodes = {}
        self.album_nodes = {}
        self.album_id_to_artists = {}  # Map album_id -> list of artist_node_ids
        self.genre_nodes = {}
        self.band_nodes = {}
        self.record_label_nodes = {}
        self.song_nodes = {}
        self.award_nodes = {}
    
    def load_nodes(self, nodes_path: str) -> pd.DataFrame:
        """Load artist nodes from CSV"""
        try:
            df = pd.read_csv(nodes_path, encoding='utf-8')
            logger.info(f"Loaded {len(df)} artist nodes from {nodes_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading nodes: {e}")
            return pd.DataFrame()
    
    def load_albums(self, albums_path: str) -> Dict:
        """Load album mapping from JSON"""
        try:
            with open(albums_path, 'r', encoding='utf-8') as f:
                albums = json.load(f)
            logger.info(f"Loaded {len(albums)} albums from {albums_path}")
            return albums
        except Exception as e:
            logger.error(f"Error loading albums: {e}")
            return {}
    
    def load_genres(self, genres_path: str) -> pd.DataFrame:
        """Load genre nodes from CSV"""
        try:
            df = pd.read_csv(genres_path, encoding='utf-8')
            logger.info(f"Loaded {len(df)} genre nodes from {genres_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading genres: {e}")
            return pd.DataFrame()
    
    def load_band_classifications(self, classifications_path: str) -> List[Dict]:
        """Load band classifications from JSON"""
        try:
            with open(classifications_path, 'r', encoding='utf-8') as f:
                classifications = json.load(f)
            logger.info(f"Loaded {len(classifications)} band classifications from {classifications_path}")
            return classifications
        except Exception as e:
            logger.error(f"Error loading band classifications: {e}")
            return []
    
    def load_songs(self, songs_path: str) -> pd.DataFrame:
        """Load song nodes from CSV"""
        try:
            df = pd.read_csv(songs_path, encoding='utf-8')
            logger.info(f"Loaded {len(df)} song nodes from {songs_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading songs: {e}")
            return pd.DataFrame()
    
    def load_awards(self, awards_path: str) -> pd.DataFrame:
        """Load award nodes from CSV"""
        try:
            df = pd.read_csv(awards_path, encoding='utf-8')
            logger.info(f"Loaded {len(df)} award nodes from {awards_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading awards: {e}")
            return pd.DataFrame()
    
    def add_award_nodes(self, df: pd.DataFrame):
        """Add award nodes to graph
        
        Args:
            df: DataFrame with award nodes (columns: id, name, ceremony, category, year)
        """
        if df.empty:
            logger.warning("No awards to add")
            return
        
        awards_added = 0
        
        for idx, row in df.iterrows():
            award_id = f"award_{row['id']}"
            self.award_nodes[row['id']] = award_id
            
            # Add award node
            self.graph.add_node(
                award_id,
                node_type='Award',
                name=row.get('name', ''),
                ceremony=row.get('ceremony', ''),
                category=row.get('category', ''),
                year=row.get('year', '')
            )
            awards_added += 1
        
        logger.info(f"Added {awards_added} award nodes to graph")
    
    def add_award_nomination_relationships(self, awards_json_path: str, awards_csv_path: str = None):
        """Add AWARD_NOMINATION relationships between Artists/Bands/Albums/Songs and Awards
        
        Args:
            awards_json_path: Path to awards JSON file (artist -> list of awards)
            awards_csv_path: Optional path to awards CSV file. If not provided, uses award nodes already in graph.
        """
        import json
        
        # Load awards JSON data
        logger.info(f"Loading awards data from {awards_json_path}...")
        try:
            with open(awards_json_path, 'r', encoding='utf-8') as f:
                awards_data = json.load(f)
            logger.info(f"Loaded awards data for {len(awards_data)} artists")
        except Exception as e:
            logger.error(f"Error loading awards JSON file: {e}")
            return
        
        if not awards_data:
            logger.warning("No awards data found")
            return
        
        # Create mapping from (ceremony, category, year) -> award_id
        # This matches the award node creation logic
        award_key_to_id = {}
        
        if awards_csv_path and os.path.exists(awards_csv_path):
            # Load from CSV
            awards_df = self.load_awards(awards_csv_path)
            if not awards_df.empty:
                for idx, row in awards_df.iterrows():
                    ceremony = str(row.get('ceremony', '')).strip()
                    category = str(row.get('category', '')).strip()
                    year = row.get('year')
                    
                    # Handle empty string year
                    if year == '' or pd.isna(year):
                        year = None
                    elif isinstance(year, str) and year.strip():
                        try:
                            year = int(year.strip())
                        except (ValueError, TypeError):
                            year = None
                    
                    if ceremony and category:
                        # Create mapping with year (or None if no year)
                        award_key = (ceremony, category, year)
                        award_id = f"award_{row['id']}"
                        award_key_to_id[award_key] = award_id
                logger.info(f"Created mapping for {len(award_key_to_id)} awards from CSV")
        else:
            # Use award nodes already in graph
            for node_id in self.graph.nodes():
                node_data = self.graph.nodes[node_id]
                if node_data.get('node_type') == 'Award':
                    ceremony = str(node_data.get('ceremony', '')).strip()
                    category = str(node_data.get('category', '')).strip()
                    year = node_data.get('year')
                    
                    # Handle empty string year
                    if year == '' or pd.isna(year):
                        year = None
                    
                    if ceremony and category:
                        award_key = (ceremony, category, year)
                        award_key_to_id[award_key] = node_id
            logger.info(f"Created mapping for {len(award_key_to_id)} awards from graph")
        
        if not award_key_to_id:
            logger.warning("No award nodes found. Call add_award_nodes() first or provide awards_csv_path.")
            return
        
        # Normalization functions (matching extract_awards.py)
        def normalize_award_name(ceremony: str) -> str:
            """Normalize award ceremony name (e.g., 'Grammy Awards' → 'Grammy')"""
            if not ceremony:
                return ""
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
            """Normalize award category name (matching extract_awards.py)"""
            if not category:
                return "General"
            
            import re
            
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
                r'best\s+pop\s+video': 'Best Pop Video',
                r'best\s+pop\s+vocal\s+album': 'Best Pop Vocal Album',
                r'best\s+pop\s+solo\s+performance': 'Best Pop Solo Performance',
            }
            
            for pattern, normalized in category_patterns.items():
                if re.search(pattern, category_lower):
                    return normalized
            
            # Extract English text from Vietnamese text (e.g., "hạng mục Best Pop Video với..." -> "Best Pop Video")
            # Look for "Best X" or "X of the Year" patterns
            english_patterns = [
                r'best\s+(?:pop\s+)?video',
                r'best\s+(?:pop\s+)?(?:vocal\s+)?album',
                r'best\s+(?:pop\s+)?(?:solo\s+)?performance',
                r'best\s+new\s+artist',
                r'album\s+of\s+the\s+year',
                r'song\s+of\s+the\s+year',
                r'record\s+of\s+the\s+year',
            ]
            for pattern in english_patterns:
                match = re.search(pattern, category_lower)
                if match:
                    # Normalize the matched text
                    matched = match.group(0)
                    for p, norm in category_patterns.items():
                        if re.search(p, matched):
                            return norm
            
            # Capitalize first letter if needed
            if category and category[0].islower():
                category = category[0].upper() + category[1:]
            
            return category if category else "General"
        
        edges_added = 0
        edges_skipped = 0
        artists_not_found = 0
        awards_not_found = 0
        
        # Process each artist's awards
        for artist_name, awards in awards_data.items():
            # Find artist/band node
            artist_node_id = self._find_artist_by_name(artist_name)
            
            if not artist_node_id:
                artists_not_found += 1
                logger.debug(f"Artist/Band not found: {artist_name}")
                continue
            
            # Verify artist node exists in graph
            if artist_node_id not in self.graph.nodes:
                artists_not_found += 1
                logger.debug(f"Artist node not in graph: {artist_node_id}")
                continue
            
            # Process each award
            for award in awards:
                # Normalize ceremony and category (same as award node creation)
                ceremony = normalize_award_name(award.get('ceremony', ''))
                category = normalize_award_category(award.get('category', ''))
                year = award.get('year')
                
                # Handle year normalization (convert to int if possible, None if empty/null)
                if year is None or year == '':
                    year = None
                elif isinstance(year, str):
                    try:
                        year = int(year.strip())
                    except (ValueError, TypeError):
                        year = None
                elif isinstance(year, (int, float)):
                    year = int(year)
                
                # Skip if missing required fields (year is optional for Vietnamese Wikipedia)
                if not ceremony or not category:
                    edges_skipped += 1
                    logger.debug(f"Award missing required fields: {award}")
                    continue
                
                # Find award node - handle both with and without year
                award_key = (ceremony, category, year)
                award_node_id = award_key_to_id.get(award_key)
                
                # If not found with year, try without year (for Vietnamese Wikipedia)
                if not award_node_id and year is not None:
                    award_key_no_year = (ceremony, category, None)
                    award_node_id = award_key_to_id.get(award_key_no_year)
                
                if not award_node_id:
                    awards_not_found += 1
                    logger.debug(f"Award node not found: {ceremony} - {category} ({year})")
                    continue
                
                # Verify award node exists in graph
                if award_node_id not in self.graph.nodes:
                    awards_not_found += 1
                    logger.debug(f"Award node not in graph: {award_node_id}")
                    continue
                
                # Get status (won/nominated) and year from award
                status = award.get('status', 'nominated')  # Default to nominated
                award_year = award.get('year')
                
                # Create edge data with optional properties
                edge_data = {
                    'relationship': 'AWARD_NOMINATION',
                    'status': status,
                    'year': award_year
                }
                
                # Create AWARD_NOMINATION edge (Artist/Band → Award)
                if not self.graph.has_edge(artist_node_id, award_node_id):
                    self.graph.add_edge(artist_node_id, award_node_id, **edge_data)
                    edges_added += 1
                else:
                    # Edge already exists - update with status if needed
                    existing_edge = self.graph.edges[artist_node_id, award_node_id]
                    # Update status if 'won' is more specific than existing
                    if status == 'won' and existing_edge.get('status') != 'won':
                        existing_edge['status'] = 'won'
                    logger.debug(f"AWARD_NOMINATION edge already exists: {artist_node_id} -> {award_node_id}")
        
        logger.info(f"Added {edges_added} AWARD_NOMINATION relationships (Artist/Band → Award)")
        if edges_skipped > 0:
            logger.warning(f"Skipped {edges_skipped} potential relationships due to missing data")
        if artists_not_found > 0:
            logger.warning(f"Could not find {artists_not_found} artists/bands in graph")
        if awards_not_found > 0:
            logger.warning(f"Could not find {awards_not_found} award nodes in graph")
    
    def add_song_nodes(self, df: pd.DataFrame):
        """Add song nodes to graph"""
        if df.empty:
            logger.warning("No songs to add")
            return
        
        songs_added = 0
        songs_without_album = 0
        
        for idx, row in df.iterrows():
            song_id = f"song_{row['id']}"
            self.song_nodes[row['id']] = song_id
            
            # Get album_id
            album_id = row.get('album_id', '')
            
            # Only add song node if it has an album (matching album node logic)
            if not album_id or pd.isna(album_id) or album_id == '':
                songs_without_album += 1
                logger.debug(f"Song {row['title']} has no album_id, skipping")
                continue
            
            # Verify album node exists
            if album_id not in self.graph.nodes:
                songs_without_album += 1
                logger.debug(f"Song {row['title']}: album {album_id} not in graph, skipping")
                continue
            
            # Add song node
            self.graph.add_node(
                song_id,
                node_type='Song',
                title=row['title'],
                duration=row.get('duration', ''),
                track_number=row.get('track_number', ''),
                album_id=album_id,
                featured_artists=row.get('featured_artists', '')
            )
            songs_added += 1
        
        logger.info(f"Added {songs_added} song nodes to graph")
        if songs_without_album > 0:
            logger.warning(f"Skipped {songs_without_album} songs without valid album nodes")
    
    def add_part_of_relationships(self, df: pd.DataFrame = None):
        """Add PART_OF relationships between Song and Album nodes
        
        Args:
            df: Optional DataFrame of songs. If not provided, uses songs already in graph.
        """
        edges_added = 0
        edges_skipped = 0
        songs_with_track_number = 0
        
        # If DataFrame provided, iterate through it
        if df is not None and not df.empty:
            logger.info("Creating PART_OF relationships from provided DataFrame")
            for idx, row in df.iterrows():
                song_id = f"song_{row['id']}"
                album_id = row.get('album_id', '')
                
                # Skip if no album_id
                if not album_id or pd.isna(album_id) or album_id == '':
                    edges_skipped += 1
                    continue
                
                # Verify both nodes exist in graph
                if song_id not in self.graph.nodes:
                    edges_skipped += 1
                    logger.debug(f"Song node not found: {song_id}")
                    continue
                
                if album_id not in self.graph.nodes:
                    edges_skipped += 1
                    logger.debug(f"Album node not found: {album_id} for song {row.get('title', 'unknown')}")
                    continue
                
                # Verify album node is actually an Album
                album_node_data = self.graph.nodes[album_id]
                if album_node_data.get('node_type') != 'Album':
                    edges_skipped += 1
                    logger.debug(f"Node {album_id} is not an Album node")
                    continue
                
                # Get track_number if available
                track_number = row.get('track_number', '')
                if track_number and str(track_number).strip() and not pd.isna(track_number):
                    try:
                        # Try to convert to integer for proper ordering
                        track_num = int(float(str(track_number).strip()))
                        edge_data = {'relationship': 'PART_OF', 'track_number': track_num}
                        songs_with_track_number += 1
                    except (ValueError, TypeError):
                        # If conversion fails, store as string
                        track_str = str(track_number).strip()
                        if track_str:
                            edge_data = {'relationship': 'PART_OF', 'track_number': track_str}
                            songs_with_track_number += 1
                        else:
                            edge_data = {'relationship': 'PART_OF'}
                else:
                    edge_data = {'relationship': 'PART_OF'}
                
                # Create PART_OF edge (Song → Album)
                if not self.graph.has_edge(song_id, album_id):
                    self.graph.add_edge(song_id, album_id, **edge_data)
                    edges_added += 1
                else:
                    logger.debug(f"PART_OF edge already exists: {song_id} -> {album_id}")
        
        else:
            # If no DataFrame provided, iterate through song nodes already in graph
            logger.info("Creating PART_OF relationships from song nodes in graph")
            song_nodes_in_graph = [
                node_id for node_id in self.graph.nodes()
                if self.graph.nodes[node_id].get('node_type') == 'Song'
            ]
            
            for song_id in song_nodes_in_graph:
                song_data = self.graph.nodes[song_id]
                album_id = song_data.get('album_id', '')
                
                # Skip if no album_id
                if not album_id or album_id == '':
                    edges_skipped += 1
                    continue
                
                # Verify album node exists
                if album_id not in self.graph.nodes:
                    edges_skipped += 1
                    logger.debug(f"Album node not found: {album_id} for song {song_data.get('title', 'unknown')}")
                    continue
                
                # Verify album node is actually an Album
                album_node_data = self.graph.nodes[album_id]
                if album_node_data.get('node_type') != 'Album':
                    edges_skipped += 1
                    logger.debug(f"Node {album_id} is not an Album node")
                    continue
                
                # Get track_number if available
                track_number = song_data.get('track_number', '')
                if track_number and str(track_number).strip():
                    try:
                        # Try to convert to integer for proper ordering
                        track_num = int(float(str(track_number).strip()))
                        edge_data = {'relationship': 'PART_OF', 'track_number': track_num}
                        songs_with_track_number += 1
                    except (ValueError, TypeError):
                        # If conversion fails, store as string
                        track_str = str(track_number).strip()
                        if track_str:
                            edge_data = {'relationship': 'PART_OF', 'track_number': track_str}
                            songs_with_track_number += 1
                        else:
                            edge_data = {'relationship': 'PART_OF'}
                else:
                    edge_data = {'relationship': 'PART_OF'}
                
                # Create PART_OF edge (Song → Album)
                if not self.graph.has_edge(song_id, album_id):
                    self.graph.add_edge(song_id, album_id, **edge_data)
                    edges_added += 1
                else:
                    logger.debug(f"PART_OF edge already exists: {song_id} -> {album_id}")
        
        logger.info(f"Added {edges_added} PART_OF relationships (Song → Album)")
        logger.info(f"  - Songs with track_number: {songs_with_track_number}")
        if edges_skipped > 0:
            logger.warning(f"Skipped {edges_skipped} potential PART_OF relationships due to missing nodes or invalid data")
    
    def _find_artist_by_name(self, artist_name: str) -> Optional[str]:
        """Find artist node ID by name (case-insensitive partial match)
        
        Args:
            artist_name: Artist name to search for
            
        Returns:
            Artist node ID if found, None otherwise
        """
        if not artist_name:
            return None
        
        artist_name_lower = artist_name.lower().strip()
        
        # First try exact match
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Artist':
                node_name = node_data.get('name', '')
                if node_name and node_name.lower() == artist_name_lower:
                    return node_id
        
        # Try partial match (contains)
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Artist':
                node_name = node_data.get('name', '')
                if node_name and artist_name_lower in node_name.lower():
                    return node_id
        
        # Try Band nodes too
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Band':
                node_name = node_data.get('name', '')
                if node_name and node_name.lower() == artist_name_lower:
                    return node_id
        
        return None
    
    def _parse_featured_artists(self, featured_artists_str: str) -> List[str]:
        """Parse featured artists from string
        
        Args:
            featured_artists_str: String containing featured artists (semicolon-separated)
            
        Returns:
            List of artist names
        """
        if not featured_artists_str or pd.isna(featured_artists_str):
            return []
        
        featured_artists_str = str(featured_artists_str).strip()
        if not featured_artists_str:
            return []
        
        # Split by semicolon and clean
        artists = [a.strip() for a in featured_artists_str.split(';') if a.strip()]
        return artists
    
    def add_performs_on_song_relationships(self, songs_df: pd.DataFrame = None):
        """Add PERFORMS_ON relationships between Artist/Band and Song nodes
        
        Args:
            songs_df: Optional DataFrame of songs. If not provided, uses songs already in graph.
        """
        if songs_df is None or songs_df.empty:
            # Get songs from graph
            song_nodes_in_graph = [
                node_id for node_id in self.graph.nodes()
                if self.graph.nodes[node_id].get('node_type') == 'Song'
            ]
            
            if not song_nodes_in_graph:
                logger.info("No songs found in graph. Skipping PERFORMS_ON (Artist → Song) relationships.")
                return
        else:
            song_nodes_in_graph = []
            for idx, row in songs_df.iterrows():
                song_id = f"song_{row['id']}"
                if song_id in self.graph.nodes:
                    song_nodes_in_graph.append(song_id)
        
        if not song_nodes_in_graph:
            logger.info("No songs found. Skipping PERFORMS_ON (Artist → Song) relationships.")
            return
        
        edges_added = 0
        edges_skipped = 0
        songs_with_featured_artists = 0
        collaboration_edges_added = 0
        
        # Create mapping from artist name to artist node ID for featured artists lookup
        name_to_artist_node = {}
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Artist':
                name = node_data.get('name', '')
                if name:
                    name_to_artist_node[name.lower()] = node_id
        
        # Also include Band nodes
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Band':
                name = node_data.get('name', '')
                if name:
                    name_to_artist_node[name.lower()] = node_id
        
        # Process each song
        for song_id in song_nodes_in_graph:
            song_data = self.graph.nodes[song_id]
            album_id = song_data.get('album_id', '')
            
            if not album_id:
                edges_skipped += 1
                continue
            
            # Get artists from album
            album_artist_nodes = self.album_id_to_artists.get(album_id, [])
            
            # Also get featured artists from song
            featured_artists_str = song_data.get('featured_artists', '')
            featured_artist_nodes = []
            
            if featured_artists_str:
                featured_artists_names = self._parse_featured_artists(featured_artists_str)
                if featured_artists_names:
                    songs_with_featured_artists += 1
                    
                    for feat_name in featured_artists_names:
                        # Try exact match first
                        feat_node_id = name_to_artist_node.get(feat_name.lower())
                        if not feat_node_id:
                            # Try fuzzy match
                            feat_node_id = self._find_artist_by_name(feat_name)
                        
                        if feat_node_id:
                            featured_artist_nodes.append(feat_node_id)
            
            # Combine album artists and featured artists
            all_artist_nodes = list(set(album_artist_nodes + featured_artist_nodes))
            
            if not all_artist_nodes:
                edges_skipped += 1
                logger.debug(f"Song {song_data.get('title', 'unknown')} has no associated artists")
                continue
            
            # Create PERFORMS_ON edges: Artist → Song
            for artist_node_id in all_artist_nodes:
                if not self.graph.has_edge(artist_node_id, song_id):
                    self.graph.add_edge(
                        artist_node_id,
                        song_id,
                        relationship='PERFORMS_ON'
                    )
                    edges_added += 1
                else:
                    logger.debug(f"PERFORMS_ON edge already exists: {artist_node_id} -> {song_id}")
            
            # Update COLLABORATES_WITH based on songs
            # Create collaboration edges between artists on the same song
            for i, artist1 in enumerate(all_artist_nodes):
                for artist2 in all_artist_nodes[i+1:]:
                    # Check if collaboration edge already exists
                    if not self.graph.has_edge(artist1, artist2):
                        self.graph.add_edge(
                            artist1,
                            artist2,
                            relationship='COLLABORATES_WITH',
                            shared_albums=0,
                            shared_songs=1
                        )
                        collaboration_edges_added += 1
                    else:
                        # Increment shared songs count
                        edge_data = self.graph[artist1][artist2]
                        if edge_data.get('relationship') == 'COLLABORATES_WITH':
                            # Initialize shared_songs if not exists
                            if 'shared_songs' not in edge_data:
                                edge_data['shared_songs'] = 0
                            edge_data['shared_songs'] = edge_data.get('shared_songs', 0) + 1
        
        logger.info(f"Added {edges_added} PERFORMS_ON relationships (Artist/Band → Song)")
        logger.info(f"  - Songs with featured artists: {songs_with_featured_artists}")
        logger.info(f"  - Updated/created {collaboration_edges_added} COLLABORATES_WITH relationships from songs")
        if edges_skipped > 0:
            logger.warning(f"Skipped {edges_skipped} potential PERFORMS_ON relationships due to missing artists")
    
    def add_genre_nodes(self, df: pd.DataFrame):
        """Add genre nodes to graph"""
        if df.empty:
            logger.warning("No genres to add")
            return
        
        for idx, row in df.iterrows():
            genre_id = row['id']
            self.genre_nodes[genre_id] = genre_id
            
            self.graph.add_node(
                genre_id,
                node_type='Genre',
                name=row['name'],
                normalized_name=row.get('normalized_name', row['name']),
                count=row.get('count', 0)
            )
        
        logger.info(f"Added {len(self.genre_nodes)} genre nodes to graph")
    
    def add_has_genre_relationships(self, relationships_path: str):
        """Add HAS_GENRE relationships from CSV"""
        try:
            df = pd.read_csv(relationships_path, encoding='utf-8')
            logger.info(f"Loading HAS_GENRE relationships from {relationships_path}")
            
            edges_added = 0
            artist_genre_count = 0
            album_genre_count = 0
            
            for idx, row in df.iterrows():
                from_id = row['from']
                to_id = row['to']
                from_type = row.get('from_type', 'Artist')
                to_type = row.get('to_type', 'Genre')
                
                # Verify nodes exist
                if from_id not in self.graph.nodes:
                    logger.debug(f"Skipping relationship: {from_id} not in graph")
                    continue
                
                if to_id not in self.graph.nodes:
                    logger.debug(f"Skipping relationship: {to_id} not in graph")
                    continue
                
                # Add edge
                self.graph.add_edge(
                    from_id,
                    to_id,
                    relationship='HAS_GENRE'
                )
                edges_added += 1
                
                if from_type == 'Artist':
                    artist_genre_count += 1
                elif from_type == 'Album':
                    album_genre_count += 1
            
            logger.info(f"Added {edges_added} HAS_GENRE relationships:")
            logger.info(f"  - Artist → Genre: {artist_genre_count}")
            logger.info(f"  - Album → Genre: {album_genre_count}")
            
        except Exception as e:
            logger.error(f"Error loading HAS_GENRE relationships: {e}")
    
    def add_artist_nodes(self, df: pd.DataFrame):
        """Add artist nodes to graph"""
        for idx, row in df.iterrows():
            node_id = f"artist_{row['id']}"
            self.artist_nodes[row['id']] = node_id
            
            self.graph.add_node(
                node_id,
                node_type='Artist',
                name=row['name'],
                genres=row.get('genres', ''),
                instruments=row.get('instruments', ''),
                active_years=row.get('active_years', ''),
                url=row.get('url', '')
            )
        
        logger.info(f"Added {len(self.artist_nodes)} artist nodes to graph")
    
    def add_record_label_nodes(self, df: pd.DataFrame):
        """Add RecordLabel nodes from unique labels in artist data"""
        if df.empty:
            logger.warning("No artist data provided for label extraction")
            return
        
        # Check if 'labels' column exists
        if 'labels' not in df.columns:
            logger.info("No 'labels' column found in data. Skipping RecordLabel node creation.")
            return
        
        # Extract all unique labels
        all_labels = set()
        
        for idx, row in df.iterrows():
            labels_str = row.get('labels', '')
            
            # Handle NaN, None, or empty values
            if pd.isna(labels_str) or not labels_str:
                continue
            
            # Ensure it's a string
            labels_str = str(labels_str).strip()
            
            if not labels_str:
                continue
            
            # Split by semicolon (labels are stored as semicolon-separated string)
            labels = [label.strip() for label in labels_str.split(';') if label.strip()]
            
            # Add to set of unique labels
            for label in labels:
                if label:  # Ensure label is not empty
                    all_labels.add(label)
        
        if not all_labels:
            logger.info("No record labels found in data")
            return
        
        # Create RecordLabel nodes
        labels_added = 0
        
        for idx, label_name in enumerate(sorted(all_labels)):
            # Create unique label ID
            label_id = f"label_{idx}"
            
            # Add label node to graph
            self.graph.add_node(
                label_id,
                node_type='RecordLabel',
                name=label_name
            )
            
            # Track label node
            self.record_label_nodes[label_name] = label_id
            labels_added += 1
        
        logger.info(f"Added {labels_added} RecordLabel nodes to graph")
    
    def add_signed_with_relationships(self, df: pd.DataFrame):
        """Add SIGNED_WITH relationships between Artist and RecordLabel nodes"""
        if df.empty:
            logger.warning("No artist data provided for SIGNED_WITH relationship creation")
            return
        
        if not self.record_label_nodes:
            logger.warning("No RecordLabel nodes found. Call add_record_label_nodes() first.")
            return
        
        # Check if 'labels' column exists
        if 'labels' not in df.columns:
            logger.info("No 'labels' column found in data. Skipping SIGNED_WITH relationship creation.")
            return
        
        edges_added = 0
        edges_skipped = 0
        
        for idx, row in df.iterrows():
            artist_id = row['id']
            artist_node_id = self.artist_nodes.get(artist_id)
            
            if not artist_node_id:
                logger.debug(f"Artist node not found for artist ID: {artist_id}")
                edges_skipped += 1
                continue
            
            # Verify artist node exists in graph
            if artist_node_id not in self.graph.nodes:
                logger.debug(f"Artist node not in graph: {artist_node_id}")
                edges_skipped += 1
                continue
            
            labels_str = row.get('labels', '')
            
            # Handle NaN, None, or empty values
            if pd.isna(labels_str) or not labels_str:
                continue
            
            # Ensure it's a string
            labels_str = str(labels_str).strip()
            
            if not labels_str:
                continue
            
            # Split by semicolon (labels are stored as semicolon-separated string)
            labels = [label.strip() for label in labels_str.split(';') if label.strip()]
            
            # Create SIGNED_WITH relationship for each label
            for label_name in labels:
                if not label_name:
                    continue
                
                # Find corresponding RecordLabel node ID
                label_node_id = self.record_label_nodes.get(label_name)
                
                if not label_node_id:
                    logger.debug(f"RecordLabel node not found for label: {label_name}")
                    edges_skipped += 1
                    continue
                
                # Verify label node exists in graph
                if label_node_id not in self.graph.nodes:
                    logger.debug(f"RecordLabel node not in graph: {label_node_id}")
                    edges_skipped += 1
                    continue
                
                # Check if edge already exists
                if not self.graph.has_edge(artist_node_id, label_node_id):
                    self.graph.add_edge(
                        artist_node_id,
                        label_node_id,
                        relationship='SIGNED_WITH'
                    )
                    edges_added += 1
                else:
                    logger.debug(f"SIGNED_WITH edge already exists: {artist_node_id} -> {label_node_id}")
        
        logger.info(f"Added {edges_added} SIGNED_WITH relationships")
        if edges_skipped > 0:
            logger.warning(f"Skipped {edges_skipped} potential SIGNED_WITH relationships due to missing nodes")
    
    def add_band_nodes(self, classifications: List[Dict]):
        """Add Band nodes from band classifications"""
        if not classifications:
            logger.warning("No classifications provided")
            return
        
        # Filter for bands only
        bands = [c for c in classifications if c.get('classification') == 'band']
        
        if not bands:
            logger.info("No bands found in classifications")
            return
        
        # Create mapping from artist name to URL from existing artist nodes
        name_to_url = {}
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Artist':
                name = node_data.get('name', '')
                url = node_data.get('url', '')
                if name:
                    name_to_url[name] = url
        
        bands_added = 0
        bands_skipped = 0
        
        for idx, band_class in enumerate(bands):
            band_name = band_class.get('name', '')
            if not band_name:
                bands_skipped += 1
                continue
            
            # Create unique band ID
            band_id = f"band_{idx}"
            
            # Get URL from artist node if available
            url = name_to_url.get(band_name, '')
            
            # Get confidence score
            confidence = band_class.get('confidence', 0.0)
            
            # Add band node to graph
            self.graph.add_node(
                band_id,
                node_type='Band',
                name=band_name,
                url=url,
                classification_confidence=confidence
            )
            
            # Track band node
            self.band_nodes[band_name] = band_id
            bands_added += 1
        
        logger.info(f"Added {bands_added} Band nodes to graph")
        if bands_skipped > 0:
            logger.warning(f"Skipped {bands_skipped} bands due to missing name")
    
    def add_member_of_relationships(self, classifications: List[Dict] = None, members_map: Dict[str, List[str]] = None):
        """
        Add MEMBER_OF relationships between Artist and Band nodes
        
        Args:
            classifications: Optional list of band classifications. If provided, will try to match
                           artists with same name as bands (for simplified 1-to-1 mapping)
            members_map: Optional dict mapping band names to list of member artist names.
                        Format: {band_name: [member1, member2, ...]}
        """
        if not self.band_nodes:
            logger.warning("No Band nodes found. Call add_band_nodes() first.")
            return
        
        edges_added = 0
        edges_skipped = 0
        
        # Create mapping from artist name to artist node ID
        name_to_artist_node = {}
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Artist':
                name = node_data.get('name', '')
                if name:
                    name_to_artist_node[name] = node_id
        
        # Case 1: Use members_map if provided (more accurate)
        if members_map:
            logger.info(f"Creating MEMBER_OF relationships from members_map ({len(members_map)} bands)")
            for band_name, members in members_map.items():
                band_id = self.band_nodes.get(band_name)
                if not band_id:
                    logger.debug(f"Band node not found: {band_name}")
                    continue
                
                for member_name in members:
                    artist_node_id = name_to_artist_node.get(member_name)
                    if not artist_node_id:
                        logger.debug(f"Artist node not found for member: {member_name}")
                        edges_skipped += 1
                        continue
                    
                    # Check if edge already exists
                    if not self.graph.has_edge(artist_node_id, band_id):
                        self.graph.add_edge(
                            artist_node_id,
                            band_id,
                            relationship='MEMBER_OF'
                        )
                        edges_added += 1
                    else:
                        logger.debug(f"MEMBER_OF edge already exists: {member_name} -> {band_name}")
        
        # Case 2: Fallback to simple 1-to-1 mapping from classifications
        # This assumes if an artist is classified as "band", the artist node represents
        # a member of that band (simplified approach until full member parsing is implemented)
        elif classifications:
            logger.info("Creating MEMBER_OF relationships from classifications (simplified approach)")
            logger.warning("Note: Full member parsing from infobox not yet implemented. "
                         "Using simplified 1-to-1 mapping based on classification.")
            
            for classification in classifications:
                if classification.get('classification') != 'band':
                    continue
                
                band_name = classification.get('name', '')
                if not band_name:
                    continue
                
                band_id = self.band_nodes.get(band_name)
                if not band_id:
                    continue
                
                # Find artist node with same name
                artist_node_id = name_to_artist_node.get(band_name)
                if not artist_node_id:
                    logger.debug(f"Artist node not found for band: {band_name}")
                    edges_skipped += 1
                    continue
                
                # Create MEMBER_OF relationship
                if not self.graph.has_edge(artist_node_id, band_id):
                    self.graph.add_edge(
                        artist_node_id,
                        band_id,
                        relationship='MEMBER_OF'
                    )
                    edges_added += 1
        
        logger.info(f"Added {edges_added} MEMBER_OF relationships")
        if edges_skipped > 0:
            logger.warning(f"Skipped {edges_skipped} potential MEMBER_OF relationships due to missing nodes")
    
    def add_album_nodes_and_edges(self, album_map: Dict):
        """Add album nodes and create artist-album edges"""
        edges_added = 0
        collaboration_edges = 0
        
        # Sort albums to ensure consistent album_id indexing (matching create_song_nodes_csv)
        sorted_albums = sorted(album_map.items())
        
        album_idx = 0
        for album_title, artist_ids in sorted_albums:
            # Only create album nodes if multiple artists are associated
            if len(artist_ids) < 2:
                continue
            
            album_id = f"album_{album_idx}"
            album_idx += 1
            self.album_nodes[album_title] = album_id
            
            # Add album node
            self.graph.add_node(
                album_id,
                node_type='Album',
                title=album_title
            )
            
            # Add edges from artists to album
            valid_artist_nodes = []
            for artist_id in artist_ids:
                artist_node_id = self.artist_nodes.get(artist_id)
                if artist_node_id:
                    self.graph.add_edge(
                        artist_node_id,
                        album_id,
                        relationship='PERFORMS_ON'
                    )
                    edges_added += 1
                    valid_artist_nodes.append(artist_node_id)
            
            # Store mapping from album_id to artist_node_ids for song linking
            self.album_id_to_artists[album_id] = valid_artist_nodes
            
            # Create collaboration edges between artists on the same album
            for i, artist1 in enumerate(valid_artist_nodes):
                for artist2 in valid_artist_nodes[i+1:]:
                    # Check if collaboration edge already exists
                    if not self.graph.has_edge(artist1, artist2):
                        self.graph.add_edge(
                            artist1,
                            artist2,
                            relationship='COLLABORATES_WITH',
                            shared_albums=1,
                            shared_songs=0  # Initialize shared_songs, will be updated by songs if available
                        )
                        collaboration_edges += 1
                    else:
                        # Increment shared albums count
                        edge_data = self.graph[artist1][artist2]
                        if edge_data.get('relationship') == 'COLLABORATES_WITH':
                            edge_data['shared_albums'] = edge_data.get('shared_albums', 0) + 1
                            # Initialize shared_songs if not exists
                            if 'shared_songs' not in edge_data:
                                edge_data['shared_songs'] = 0
        
        logger.info(f"Added {len(self.album_nodes)} album nodes")
        logger.info(f"Added {edges_added} artist-album edges")
        logger.info(f"Added {collaboration_edges} artist-artist collaboration edges")
    
    def create_similar_genre_edges(self, similarity_threshold: float = 0.3):
        """Create SIMILAR_GENRE edges between artists with similar genres"""
        logger.info("Creating SIMILAR_GENRE edges...")
        
        edges_added = 0
        
        # Get all artist nodes
        artist_nodes_list = list(self.artist_nodes.values())
        
        for i, artist1_id in enumerate(artist_nodes_list):
            artist1 = self.graph.nodes[artist1_id]
            genres1_str = artist1.get('genres', '')
            
            # Handle NaN and None values
            if pd.isna(genres1_str) or not genres1_str:
                continue
            
            # Ensure it's a string
            genres1_str = str(genres1_str)
            
            if not genres1_str.strip():
                continue
            
            # Parse genres
            genres1 = set(g.lower().strip() for g in genres1_str.split(';') if g.strip())
            
            if not genres1:
                continue
            
            # Compare with other artists
            for artist2_id in artist_nodes_list[i+1:]:
                artist2 = self.graph.nodes[artist2_id]
                genres2_str = artist2.get('genres', '')
                
                # Handle NaN and None values
                if pd.isna(genres2_str) or not genres2_str:
                    continue
                
                # Ensure it's a string
                genres2_str = str(genres2_str)
                
                if not genres2_str.strip():
                    continue
                
                genres2 = set(g.lower().strip() for g in genres2_str.split(';') if g.strip())
                
                if not genres2:
                    continue
                
                # Calculate similarity
                common_genres = genres1.intersection(genres2)
                all_genres = genres1.union(genres2)
                
                if len(common_genres) > 0 and len(all_genres) > 0:
                    similarity = len(common_genres) / len(all_genres)
                    
                    # Create edge if similarity exceeds threshold
                    if similarity >= similarity_threshold:
                        # Check if edge already exists
                        if not self.graph.has_edge(artist1_id, artist2_id):
                            self.graph.add_edge(
                                artist1_id,
                                artist2_id,
                                relationship='SIMILAR_GENRE',
                                similarity=round(similarity, 3)
                            )
                            edges_added += 1
        
        logger.info(f"Added {edges_added} SIMILAR_GENRE edges")
        return edges_added
    
    def build_graph(self, nodes_path: str, albums_path: str, songs_path: str = None) -> nx.Graph:
        """Build complete graph from processed data
        
        Args:
            nodes_path: Path to artist nodes CSV
            albums_path: Path to albums JSON
            songs_path: Optional path to songs CSV
        """
        logger.info("Building graph network...")
        
        # Load data
        df = self.load_nodes(nodes_path)
        album_map = self.load_albums(albums_path)
        
        if df.empty:
            logger.error("No nodes to build graph")
            return self.graph
        
        # Build graph
        self.add_artist_nodes(df)
        self.add_album_nodes_and_edges(album_map)
        
        # Add record label nodes
        self.add_record_label_nodes(df)
        
        # Add SIGNED_WITH relationships
        self.add_signed_with_relationships(df)
        
        # Create similar genre edges
        self.create_similar_genre_edges(similarity_threshold=0.3)
        
        # Add Song nodes and PART_OF relationships if songs_path provided
        if songs_path and os.path.exists(songs_path):
            logger.info(f"Loading songs from {songs_path}")
            songs_df = self.load_songs(songs_path)
            if not songs_df.empty:
                self.add_song_nodes(songs_df)
                self.add_part_of_relationships(songs_df)
                # Add PERFORMS_ON relationships: Artist → Song
                self.add_performs_on_song_relationships(songs_df)
        
        # Log statistics
        logger.info(f"Graph built successfully:")
        logger.info(f"  - Nodes: {self.graph.number_of_nodes()}")
        logger.info(f"  - Edges: {self.graph.number_of_edges()}")
        
        return self.graph
    
    def export_edges_csv(self, output_path: str):
        """Export edges to CSV for Neo4j import
        
        Exports all relationship types including:
        - PERFORMS_ON (Artist -> Album, Artist -> Song)
        - COLLABORATES_WITH (Artist -> Artist)
        - SIMILAR_GENRE (Artist -> Artist)
        - MEMBER_OF (Artist -> Band)
        - HAS_GENRE (Artist/Album -> Genre)
        - SIGNED_WITH (Artist -> RecordLabel)
        - PART_OF (Song -> Album)
        - AWARD_NOMINATION (Artist/Band -> Award)
        """
        edges_data = []
        
        for u, v, data in self.graph.edges(data=True):
            edge_record = {
                'from': u,
                'to': v,
                'type': data.get('relationship', 'PERFORMS_ON')
            }
            
            # Add weight based on relationship type
            relationship = data.get('relationship', 'PERFORMS_ON')
            
            if relationship == 'COLLABORATES_WITH':
                # Use combined weight: shared_albums + shared_songs
                shared_albums = data.get('shared_albums', 0)
                shared_songs = data.get('shared_songs', 0)
                edge_record['weight'] = shared_albums + shared_songs
                edge_record['shared_albums'] = shared_albums
                edge_record['shared_songs'] = shared_songs
            elif relationship == 'SIMILAR_GENRE':
                edge_record['weight'] = data.get('similarity', 0.5)
            elif relationship == 'PART_OF':
                # For PART_OF relationships, include track_number if available
                track_number = data.get('track_number')
                if track_number is not None:
                    edge_record['track_number'] = track_number
                edge_record['weight'] = 1
            elif relationship == 'AWARD_NOMINATION':
                # For AWARD_NOMINATION relationships, include optional status and year
                status = data.get('status')
                if status is not None:
                    edge_record['status'] = status
                year = data.get('year')
                if year is not None:
                    edge_record['year'] = year
                edge_record['weight'] = 1
            else:
                # Default weight for all other relationships (PERFORMS_ON, MEMBER_OF, 
                # HAS_GENRE, SIGNED_WITH, etc.)
                edge_record['weight'] = 1
                
            edges_data.append(edge_record)
        
        df = pd.DataFrame(edges_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Log breakdown by type with detailed statistics
        type_counts = df['type'].value_counts().to_dict()
        logger.info(f"Exported {len(edges_data)} edges to {output_path}")
        for edge_type, count in type_counts.items():
            logger.info(f"  - {edge_type}: {count}")
        
        # Detailed breakdown for PERFORMS_ON edges (Artist → Album vs Artist → Song)
        if 'PERFORMS_ON' in type_counts:
            performs_on_edges = df[df['type'] == 'PERFORMS_ON']
            # Count Artist → Album vs Artist → Song
            artist_to_album = 0
            artist_to_song = 0
            band_to_album = 0
            band_to_song = 0
            
            for _, row in performs_on_edges.iterrows():
                from_node = row['from']
                to_node = row['to']
                
                # Check from node type
                from_type = self.graph.nodes.get(from_node, {}).get('node_type', '')
                # Check to node type
                to_type = self.graph.nodes.get(to_node, {}).get('node_type', '')
                
                if from_type == 'Artist':
                    if to_type == 'Album':
                        artist_to_album += 1
                    elif to_type == 'Song':
                        artist_to_song += 1
                elif from_type == 'Band':
                    if to_type == 'Album':
                        band_to_album += 1
                    elif to_type == 'Song':
                        band_to_song += 1
            
            logger.info(f"  PERFORMS_ON breakdown:")
            if artist_to_album > 0:
                logger.info(f"    - Artist → Album: {artist_to_album}")
            if artist_to_song > 0:
                logger.info(f"    - Artist → Song: {artist_to_song}")
            if band_to_album > 0:
                logger.info(f"    - Band → Album: {band_to_album}")
            if band_to_song > 0:
                logger.info(f"    - Band → Song: {band_to_song}")
        
        # Detailed breakdown for PART_OF edges
        if 'PART_OF' in type_counts:
            part_of_edges = df[df['type'] == 'PART_OF']
            tracks_with_number = 0
            if 'track_number' in part_of_edges.columns:
                tracks_with_number = part_of_edges['track_number'].notna().sum()
            logger.info(f"  PART_OF breakdown:")
            logger.info(f"    - Total: {len(part_of_edges)}")
            logger.info(f"    - With track_number: {tracks_with_number}")
        
        # Detailed breakdown for AWARD_NOMINATION edges
        if 'AWARD_NOMINATION' in type_counts:
            award_nomination_edges = df[df['type'] == 'AWARD_NOMINATION']
            with_status = 0
            with_year = 0
            if 'status' in award_nomination_edges.columns:
                with_status = award_nomination_edges['status'].notna().sum()
            if 'year' in award_nomination_edges.columns:
                with_year = award_nomination_edges['year'].notna().sum()
            
            # Count by status
            won_count = 0
            nominated_count = 0
            if 'status' in award_nomination_edges.columns:
                won_count = (award_nomination_edges['status'] == 'won').sum()
                nominated_count = (award_nomination_edges['status'] == 'nominated').sum()
            
            logger.info(f"  AWARD_NOMINATION breakdown:")
            logger.info(f"    - Total: {len(award_nomination_edges)}")
            if with_status > 0:
                logger.info(f"    - With status: {with_status}")
                if won_count > 0:
                    logger.info(f"      - Won: {won_count}")
                if nominated_count > 0:
                    logger.info(f"      - Nominated: {nominated_count}")
            if with_year > 0:
                logger.info(f"    - With year: {with_year}")
    
    def export_has_genre_relationships_csv(self, relationships_path: str, output_path: str):
        """Export HAS_GENRE relationships from migration CSV to edges CSV format"""
        try:
            df = pd.read_csv(relationships_path, encoding='utf-8')
            
            # Convert to edges format
            edges_data = []
            for idx, row in df.iterrows():
                edges_data.append({
                    'from': row['from'],
                    'to': row['to'],
                    'type': 'HAS_GENRE',
                    'weight': 1
                })
            
            df_edges = pd.DataFrame(edges_data)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df_edges.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"Exported {len(edges_data)} HAS_GENRE relationships to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting HAS_GENRE relationships: {e}")
    
    def export_nodes_for_neo4j(self, output_dir: str):
        """Export nodes in Neo4j-friendly format"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export artist nodes
        artist_data = []
        for node_id in self.artist_nodes.values():
            node_attrs = self.graph.nodes[node_id]
            artist_data.append({
                'id': node_id,
                'name': node_attrs.get('name', ''),
                'genres': node_attrs.get('genres', ''),
                'instruments': node_attrs.get('instruments', ''),
                'active_years': node_attrs.get('active_years', ''),
                'url': node_attrs.get('url', '')
            })
        
        df_artists = pd.DataFrame(artist_data)
        df_artists.to_csv(f"{output_dir}/artists.csv", index=False, encoding='utf-8')
        logger.info(f"Exported {len(artist_data)} artists to {output_dir}/artists.csv")
        
        # Export album nodes
        album_data = []
        for node_id in self.album_nodes.values():
            node_attrs = self.graph.nodes[node_id]
            album_data.append({
                'id': node_id,
                'title': node_attrs.get('title', '')
            })
        
        df_albums = pd.DataFrame(album_data)
        df_albums.to_csv(f"{output_dir}/albums.csv", index=False, encoding='utf-8')
        logger.info(f"Exported {len(album_data)} albums to {output_dir}/albums.csv")
        
        # Export genre nodes
        if self.genre_nodes:
            genre_data = []
            for genre_id in self.genre_nodes.values():
                node_attrs = self.graph.nodes[genre_id]
                genre_data.append({
                    'id': genre_id,
                    'name': node_attrs.get('name', ''),
                    'normalized_name': node_attrs.get('normalized_name', ''),
                    'count': node_attrs.get('count', 0)
                })
            
            df_genres = pd.DataFrame(genre_data)
            df_genres.to_csv(f"{output_dir}/genres.csv", index=False, encoding='utf-8')
            logger.info(f"Exported {len(genre_data)} genres to {output_dir}/genres.csv")
        
        # Export band nodes
        if self.band_nodes:
            band_data = []
            for band_id in self.band_nodes.values():
                node_attrs = self.graph.nodes[band_id]
                band_data.append({
                    'id': band_id,
                    'name': node_attrs.get('name', ''),
                    'url': node_attrs.get('url', ''),
                    'classification_confidence': node_attrs.get('classification_confidence', 0.0)
                })
            
            df_bands = pd.DataFrame(band_data)
            df_bands.to_csv(f"{output_dir}/bands.csv", index=False, encoding='utf-8')
            logger.info(f"Exported {len(band_data)} bands to {output_dir}/bands.csv")
        
        # Export record label nodes
        if self.record_label_nodes:
            label_data = []
            for label_id in self.record_label_nodes.values():
                node_attrs = self.graph.nodes[label_id]
                label_data.append({
                    'id': label_id,
                    'name': node_attrs.get('name', '')
                })
            
            df_labels = pd.DataFrame(label_data)
            df_labels.to_csv(f"{output_dir}/record_labels.csv", index=False, encoding='utf-8')
            logger.info(f"Exported {len(label_data)} record labels to {output_dir}/record_labels.csv")
        else:
            logger.info("No record labels to export (record_labels.csv not created)")
        
        # Export song nodes
        song_data = []
        # Get songs from both self.song_nodes and graph (in case songs were added directly)
        song_ids_to_export = set()
        
        # Add songs from self.song_nodes
        if self.song_nodes:
            for song_id in self.song_nodes.values():
                if song_id in self.graph.nodes:
                    song_ids_to_export.add(song_id)
        
        # Also check graph for any Song nodes that might not be in self.song_nodes
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Song':
                song_ids_to_export.add(node_id)
        
        # Export all song nodes
        for song_id in song_ids_to_export:
            node_attrs = self.graph.nodes[song_id]
            song_data.append({
                'id': song_id,
                'title': node_attrs.get('title', ''),
                'duration': node_attrs.get('duration', ''),
                'track_number': node_attrs.get('track_number', ''),
                'album_id': node_attrs.get('album_id', ''),
                'featured_artists': node_attrs.get('featured_artists', '')
            })
        
        if song_data:
            df_songs = pd.DataFrame(song_data)
            df_songs.to_csv(f"{output_dir}/songs.csv", index=False, encoding='utf-8')
            logger.info(f"Exported {len(song_data)} songs to {output_dir}/songs.csv")
        else:
            logger.info("No songs to export (songs.csv not created)")
        
        # Export award nodes
        award_data = []
        # Get awards from both self.award_nodes and graph (in case awards were added directly)
        award_ids_to_export = set()
        
        # Add awards from self.award_nodes
        if self.award_nodes:
            for award_id in self.award_nodes.values():
                if award_id in self.graph.nodes:
                    award_ids_to_export.add(award_id)
        
        # Also check graph for any Award nodes that might not be in self.award_nodes
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            if node_data.get('node_type') == 'Award':
                award_ids_to_export.add(node_id)
        
        # Export all award nodes
        for award_id in award_ids_to_export:
            node_attrs = self.graph.nodes[award_id]
            award_data.append({
                'id': award_id,
                'name': node_attrs.get('name', ''),
                'ceremony': node_attrs.get('ceremony', ''),
                'category': node_attrs.get('category', ''),
                'year': node_attrs.get('year', '')
            })
        
        if award_data:
            df_awards = pd.DataFrame(award_data)
            df_awards.to_csv(f"{output_dir}/awards.csv", index=False, encoding='utf-8')
            logger.info(f"Exported {len(award_data)} awards to {output_dir}/awards.csv")
        else:
            logger.info("No awards to export (awards.csv not created)")
    
    def save_graph(self, output_path: str):
        """Save graph in GraphML format"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        nx.write_graphml(self.graph, output_path)
        logger.info(f"Saved graph to {output_path}")


def build_graph(nodes_path: str = "data/processed/nodes.csv",
                albums_path: str = "data/processed/albums.json",
                output_dir: str = "data/processed",
                genres_path: str = None,
                has_genre_path: str = None,
                band_classifications_path: str = None,
                songs_path: str = None,
                awards_csv_path: str = None,
                awards_json_path: str = None) -> int:
    """Main function to build graph
    
    Args:
        nodes_path: Path to artist nodes CSV
        albums_path: Path to albums JSON
        output_dir: Output directory for exported files
        genres_path: Optional path to genres CSV
        has_genre_path: Optional path to HAS_GENRE relationships CSV
        band_classifications_path: Optional path to band classifications JSON
        songs_path: Optional path to songs CSV
        awards_csv_path: Optional path to awards CSV file
        awards_json_path: Optional path to awards JSON file (artist -> list of awards)
    """
    builder = GraphBuilder()
    graph = builder.build_graph(nodes_path, albums_path, songs_path=songs_path)
    
    # Add Genre nodes if provided
    if genres_path and os.path.exists(genres_path):
        genres_df = builder.load_genres(genres_path)
        builder.add_genre_nodes(genres_df)
    
    # Add HAS_GENRE relationships if provided
    if has_genre_path and os.path.exists(has_genre_path):
        builder.add_has_genre_relationships(has_genre_path)
    
    # Add Band nodes and MEMBER_OF relationships if provided
    if band_classifications_path and os.path.exists(band_classifications_path):
        logger.info(f"Loading band classifications from {band_classifications_path}")
        classifications = builder.load_band_classifications(band_classifications_path)
        builder.add_band_nodes(classifications)
        builder.add_member_of_relationships(classifications)
    
    # Add Award nodes if provided
    if awards_csv_path and os.path.exists(awards_csv_path):
        logger.info(f"Loading awards from {awards_csv_path}")
        awards_df = builder.load_awards(awards_csv_path)
        if not awards_df.empty:
            builder.add_award_nodes(awards_df)
    
    # Add AWARD_NOMINATION relationships if provided
    if awards_json_path and os.path.exists(awards_json_path):
        logger.info(f"Loading award relationships from {awards_json_path}")
        builder.add_award_nomination_relationships(awards_json_path, awards_csv_path)
    
    # Export for Neo4j
    builder.export_nodes_for_neo4j(output_dir)
    builder.export_edges_csv(f"{output_dir}/edges.csv")
    
    # Export HAS_GENRE relationships separately if provided
    if has_genre_path and os.path.exists(has_genre_path):
        builder.export_has_genre_relationships_csv(
            has_genre_path,
            f"{output_dir}/has_genre_edges.csv"
        )
    
    # Save graph file
    builder.save_graph(f"{output_dir}/network.graphml")
    
    return graph.number_of_nodes()


if __name__ == "__main__":
    build_graph()


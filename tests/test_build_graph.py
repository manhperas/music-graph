#!/usr/bin/env python3
"""
Test script to build graph with Genre nodes
"""
import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import json
import pandas as pd
import networkx as nx
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_graph_with_genres():
    """Build graph with Genre nodes"""
    logger.info("=" * 60)
    logger.info("Building graph with Genre nodes...")
    logger.info("=" * 60)
    
    # Initialize graph
    graph = nx.Graph()
    artist_nodes = {}
    album_nodes = {}
    genre_nodes = {}
    
    # Load artists
    logger.info("Loading artists...")
    artists_df = pd.read_csv('data/processed/nodes.csv', encoding='utf-8')
    for idx, row in artists_df.iterrows():
        node_id = f"artist_{row['id']}"
        artist_nodes[row['id']] = node_id
        graph.add_node(
            node_id,
            node_type='Artist',
            name=row['name'],
            genres=row.get('genres', ''),
            instruments=row.get('instruments', ''),
            active_years=row.get('active_years', ''),
            url=row.get('url', '')
        )
    logger.info(f"✓ Added {len(artist_nodes)} artist nodes")
    
    # Load albums
    logger.info("Loading albums...")
    with open('data/processed/albums.json', 'r', encoding='utf-8') as f:
        album_map = json.load(f)
    
    edges_added = 0
    for album_idx, (album_title, artist_ids) in enumerate(album_map.items()):
        if len(artist_ids) < 2:
            continue
        
        album_id = f"album_{album_idx}"
        album_nodes[album_title] = album_id
        
        graph.add_node(
            album_id,
            node_type='Album',
            title=album_title
        )
        
        for artist_id in artist_ids:
            artist_node_id = artist_nodes.get(artist_id)
            if artist_node_id:
                graph.add_edge(
                    artist_node_id,
                    album_id,
                    relationship='PERFORMS_ON'
                )
                edges_added += 1
    
    logger.info(f"✓ Added {len(album_nodes)} album nodes")
    logger.info(f"✓ Added {edges_added} artist-album edges")
    
    # Load genres
    genres_path = 'data/migrations/genres.csv'
    if os.path.exists(genres_path):
        logger.info("Loading genres...")
        genres_df = pd.read_csv(genres_path, encoding='utf-8')
        for idx, row in genres_df.iterrows():
            genre_id = row['id']
            genre_nodes[genre_id] = genre_id
            graph.add_node(
                genre_id,
                node_type='Genre',
                name=row['name'],
                normalized_name=row.get('normalized_name', row['name']),
                count=row.get('count', 0)
            )
        logger.info(f"✓ Added {len(genre_nodes)} genre nodes")
    else:
        logger.warning(f"Genres file not found: {genres_path}")
    
    # Load HAS_GENRE relationships
    has_genre_path = 'data/migrations/has_genre_relationships.csv'
    if os.path.exists(has_genre_path):
        logger.info("Loading HAS_GENRE relationships...")
        has_genre_df = pd.read_csv(has_genre_path, encoding='utf-8')
        
        artist_genre_count = 0
        album_genre_count = 0
        skipped = 0
        
        for idx, row in has_genre_df.iterrows():
            from_id = row['from']
            to_id = row['to']
            from_type = row.get('from_type', 'Artist')
            
            if from_id not in graph.nodes:
                skipped += 1
                continue
            if to_id not in graph.nodes:
                skipped += 1
                continue
            
            graph.add_edge(
                from_id,
                to_id,
                relationship='HAS_GENRE'
            )
            
            if from_type == 'Artist':
                artist_genre_count += 1
            elif from_type == 'Album':
                album_genre_count += 1
        
        logger.info(f"✓ Added HAS_GENRE relationships:")
        logger.info(f"  - Artist → Genre: {artist_genre_count}")
        logger.info(f"  - Album → Genre: {album_genre_count}")
        if skipped > 0:
            logger.warning(f"  - Skipped: {skipped}")
    else:
        logger.warning(f"HAS_GENRE file not found: {has_genre_path}")
    
    # Export nodes
    logger.info("Exporting nodes...")
    os.makedirs('data/processed', exist_ok=True)
    
    # Export artists
    artist_data = []
    for node_id in artist_nodes.values():
        node_attrs = graph.nodes[node_id]
        artist_data.append({
            'id': node_id,
            'name': node_attrs.get('name', ''),
            'genres': node_attrs.get('genres', ''),
            'instruments': node_attrs.get('instruments', ''),
            'active_years': node_attrs.get('active_years', ''),
            'url': node_attrs.get('url', '')
        })
    pd.DataFrame(artist_data).to_csv('data/processed/artists.csv', index=False, encoding='utf-8')
    logger.info(f"✓ Exported {len(artist_data)} artists")
    
    # Export albums
    album_data = []
    for node_id in album_nodes.values():
        node_attrs = graph.nodes[node_id]
        album_data.append({
            'id': node_id,
            'title': node_attrs.get('title', '')
        })
    pd.DataFrame(album_data).to_csv('data/processed/albums.csv', index=False, encoding='utf-8')
    logger.info(f"✓ Exported {len(album_data)} albums")
    
    # Export genres
    if genre_nodes:
        genre_data = []
        for genre_id in genre_nodes.values():
            node_attrs = graph.nodes[genre_id]
            genre_data.append({
                'id': genre_id,
                'name': node_attrs.get('name', ''),
                'normalized_name': node_attrs.get('normalized_name', ''),
                'count': node_attrs.get('count', 0)
            })
        pd.DataFrame(genre_data).to_csv('data/processed/genres.csv', index=False, encoding='utf-8')
        logger.info(f"✓ Exported {len(genre_data)} genres")
    
    # Export edges
    logger.info("Exporting edges...")
    edges_data = []
    for u, v, data in graph.edges(data=True):
        edges_data.append({
            'from': u,
            'to': v,
            'type': data.get('relationship', 'PERFORMS_ON'),
            'weight': 1
        })
    
    pd.DataFrame(edges_data).to_csv('data/processed/edges.csv', index=False, encoding='utf-8')
    logger.info(f"✓ Exported {len(edges_data)} edges")
    
    # Export HAS_GENRE separately
    if os.path.exists(has_genre_path):
        has_genre_df = pd.read_csv(has_genre_path, encoding='utf-8')
        has_genre_edges = []
        for idx, row in has_genre_df.iterrows():
            has_genre_edges.append({
                'from': row['from'],
                'to': row['to'],
                'type': 'HAS_GENRE',
                'weight': 1
            })
        pd.DataFrame(has_genre_edges).to_csv('data/processed/has_genre_edges.csv', index=False, encoding='utf-8')
        logger.info(f"✓ Exported {len(has_genre_edges)} HAS_GENRE edges")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Graph Summary:")
    logger.info(f"  - Total nodes: {graph.number_of_nodes()}")
    logger.info(f"  - Total edges: {graph.number_of_edges()}")
    logger.info(f"  - Artists: {len(artist_nodes)}")
    logger.info(f"  - Albums: {len(album_nodes)}")
    logger.info(f"  - Genres: {len(genre_nodes)}")
    logger.info("=" * 60)
    
    return graph.number_of_nodes()


if __name__ == "__main__":
    try:
        node_count = build_graph_with_genres()
        print(f"\n✅ Success! Graph built with {node_count} nodes")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


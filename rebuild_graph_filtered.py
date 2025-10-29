#!/usr/bin/env python3
"""Rebuild graph with filtered nodes"""

import json
import csv
from collections import defaultdict

def load_filtered_nodes(nodes_file):
    """Load filtered nodes"""
    print(f"Loading filtered nodes from {nodes_file}...")
    
    nodes = {}
    
    with open(nodes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            old_id = int(row['id'])
            node_id = f"artist_{old_id}"
            nodes[old_id] = {
                'node_id': node_id,
                'name': row['name'],
                'genres': row.get('genres', ''),
                'instruments': row.get('instruments', ''),
                'active_years': row.get('active_years', ''),
                'url': row.get('url', '')
            }
    
    print(f"Loaded {len(nodes)} artist nodes")
    return nodes

def load_albums(albums_file):
    """Load album mapping"""
    print(f"Loading albums from {albums_file}...")
    
    with open(albums_file, 'r', encoding='utf-8') as f:
        albums = json.load(f)
    
    print(f"Loaded {len(albums)} albums")
    return albums

def rebuild_graph(nodes_file, albums_file, output_dir):
    """Rebuild graph with filtered nodes"""
    import os
    
    # Load data
    nodes = load_filtered_nodes(nodes_file)
    albums = load_albums(albums_file)
    
    # Create graph structures
    print("\nBuilding graph...")
    
    # Track edges
    performs_on_edges = []
    collaboration_edges = defaultdict(lambda: {'count': 0, 'shared_albums': 0})
    
    album_count = 0
    
    for album_title, artist_ids in albums.items():
        # Filter to only valid artist IDs
        valid_artist_ids = []
        for artist_id in artist_ids:
            if artist_id in nodes:
                valid_artist_ids.append(artist_id)
        
        # Only create album nodes if multiple artists
        if len(valid_artist_ids) >= 2:
            album_count += 1
            
            # Create PERFORMS_ON edges
            for artist_id in valid_artist_ids:
                performs_on_edges.append({
                    'from': f"artist_{artist_id}",
                    'to': f"album_{album_count}",
                    'type': 'PERFORMS_ON',
                    'weight': 1
                })
            
            # Create COLLABORATES_WITH edges
            for i, artist1_id in enumerate(valid_artist_ids):
                for artist2_id in valid_artist_ids[i+1:]:
                    key = tuple(sorted([artist1_id, artist2_id]))
                    collaboration_edges[key]['shared_albums'] += 1
    
    # Convert collaboration edges to list
    collaboration_edges_list = []
    for (id1, id2), data in collaboration_edges.items():
        collaboration_edges_list.append({
            'from': f"artist_{id1}",
            'to': f"artist_{id2}",
            'type': 'COLLABORATES_WITH',
            'weight': data['shared_albums']
        })
    
    # Save nodes
    print(f"\nSaving {len(nodes)} artist nodes...")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/artists.csv", 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'genres', 'instruments', 'active_years', 'url'])
        writer.writeheader()
        for old_id, node_data in nodes.items():
            writer.writerow({
                'id': node_data['node_id'],
                'name': node_data['name'],
                'genres': node_data['genres'],
                'instruments': node_data['instruments'],
                'active_years': node_data['active_years'],
                'url': node_data['url']
            })
    
    # Save album nodes (just titles for now)
    album_nodes = []
    for i in range(1, album_count + 1):
        album_nodes.append({
            'id': f"album_{i}",
            'title': ''  # Will need to be filled from albums.json
        })
    
    with open(f"{output_dir}/albums.csv", 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'title'])
        writer.writeheader()
        writer.writerows(album_nodes)
    
    # Save edges
    print(f"Saving {len(performs_on_edges)} PERFORMS_ON edges...")
    print(f"Saving {len(collaboration_edges_list)} COLLABORATES_WITH edges...")
    
    all_edges = performs_on_edges + collaboration_edges_list
    
    with open(f"{output_dir}/edges.csv", 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['from', 'to', 'type', 'weight'])
        writer.writeheader()
        writer.writerows(all_edges)
    
    print(f"\n✓ Graph rebuilt successfully!")
    print(f"  - Artists: {len(nodes)}")
    print(f"  - Albums: {album_count}")
    print(f"  - PERFORMS_ON edges: {len(performs_on_edges)}")
    print(f"  - COLLABORATES_WITH edges: {len(collaboration_edges_list)}")
    print(f"  - Total edges: {len(all_edges)}")

if __name__ == "__main__":
    rebuild_graph(
        nodes_file="data/processed/nodes_filtered.csv",
        albums_file="data/processed/albums.json",
        output_dir="data/processed/filtered"
    )


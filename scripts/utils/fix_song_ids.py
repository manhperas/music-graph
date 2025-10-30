#!/usr/bin/env python3
"""
Fix song IDs in edges.csv to match songs.csv format
Rebuild edges.csv with correct song IDs
"""

import pandas as pd
import os

def fix_song_ids_in_edges():
    """Fix song IDs in edges.csv to match songs.csv"""
    edges_path = "data/processed/edges.csv"
    songs_path = "data/processed/songs.csv"
    
    if not os.path.exists(edges_path):
        print(f"❌ {edges_path} not found")
        return
    
    if not os.path.exists(songs_path):
        print(f"❌ {songs_path} not found")
        return
    
    print("Loading edges.csv...")
    df_edges = pd.read_csv(edges_path)
    
    print("Loading songs.csv...")
    df_songs = pd.read_csv(songs_path)
    
    # Create mapping: old_id -> new_id
    # Old format: song_song_song_142 -> song_142
    # New format: song_{id} where id is from songs.csv
    
    print("Creating ID mapping...")
    id_mapping = {}
    
    # Map from song index to song_id
    for idx, row in df_songs.iterrows():
        old_id_pattern = f"song_song_song_{idx}"
        new_id = f"song_{idx}"
        id_mapping[old_id_pattern] = new_id
    
    # Also handle other patterns
    for old_id in df_edges['from'].unique():
        if isinstance(old_id, str) and old_id.startswith('song_song_song_'):
            # Extract number
            try:
                num = int(old_id.replace('song_song_song_', ''))
                new_id = f"song_{num}"
                id_mapping[old_id] = new_id
            except:
                pass
    
    for old_id in df_edges['to'].unique():
        if isinstance(old_id, str) and old_id.startswith('song_song_song_'):
            try:
                num = int(old_id.replace('song_song_song_', ''))
                new_id = f"song_{num}"
                id_mapping[old_id] = new_id
            except:
                pass
    
    print(f"Created {len(id_mapping)} ID mappings")
    
    # Replace IDs in edges
    print("Updating edges.csv...")
    df_edges['from'] = df_edges['from'].replace(id_mapping)
    df_edges['to'] = df_edges['to'].replace(id_mapping)
    
    # Save backup
    backup_path = edges_path + ".backup"
    print(f"Creating backup: {backup_path}")
    df_edges.to_csv(backup_path, index=False)
    
    # Save updated edges
    df_edges.to_csv(edges_path, index=False)
    print(f"✅ Updated {edges_path}")
    print(f"   Total edges: {len(df_edges)}")
    print(f"   PART_OF edges: {len(df_edges[df_edges['type'] == 'PART_OF'])}")
    
    # Show sample
    part_of_edges = df_edges[df_edges['type'] == 'PART_OF']
    if not part_of_edges.empty:
        print("\nSample PART_OF edges:")
        print(part_of_edges[['from', 'to', 'type']].head())

if __name__ == "__main__":
    fix_song_ids_in_edges()


#!/usr/bin/env python3
"""
Rebuild PART_OF edges with correct song IDs by matching album_id
"""

import pandas as pd
import os

def rebuild_part_of_edges():
    """Rebuild PART_OF edges with correct song IDs"""
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
    
    # Create mapping from (album_id, song_index_in_album) -> song_id
    # First, let's create a mapping from old song IDs to new song IDs based on album_id
    
    print("Creating song ID mapping based on album_id...")
    
    # Get all PART_OF edges
    part_of_edges = df_edges[df_edges['type'] == 'PART_OF'].copy()
    
    if part_of_edges.empty:
        print("No PART_OF edges found")
        return
    
    # Create mapping: album_id -> list of songs in that album (sorted by track_number if available)
    album_to_songs = {}
    for _, song_row in df_songs.iterrows():
        album_id = song_row.get('album_id', '')
        if album_id and album_id != '':
            if album_id not in album_to_songs:
                album_to_songs[album_id] = []
            album_to_songs[album_id].append({
                'song_id': f"song_{song_row['id']}",
                'title': song_row.get('title', ''),
                'track_number': song_row.get('track_number', '')
            })
    
    # Sort songs by track_number within each album
    for album_id in album_to_songs:
        songs = album_to_songs[album_id]
        try:
            songs.sort(key=lambda x: int(x['track_number']) if x['track_number'] and str(x['track_number']).isdigit() else 999)
        except:
            pass
    
    # Now map old song IDs to new song IDs based on position in album
    id_mapping = {}
    
    for _, edge_row in part_of_edges.iterrows():
        old_song_id = edge_row['to']
        album_id = edge_row['from']
        
        if album_id in album_to_songs:
            songs_in_album = album_to_songs[album_id]
            # Find position of this edge in PART_OF edges for this album
            edges_for_album = part_of_edges[part_of_edges['from'] == album_id]
            
            # Get index of current edge
            edge_index = edges_for_album.index.get_loc(edge_row.name)
            
            if edge_index < len(songs_in_album):
                new_song_id = songs_in_album[edge_index]['song_id']
                id_mapping[old_song_id] = new_song_id
    
    print(f"Created {len(id_mapping)} song ID mappings")
    
    # Update edges
    print("Updating edges.csv...")
    df_edges['to'] = df_edges['to'].replace(id_mapping)
    df_edges['from'] = df_edges['from'].replace(id_mapping)
    
    # Save
    backup_path = edges_path + ".backup2"
    if os.path.exists(backup_path):
        os.remove(backup_path)
    os.rename(edges_path, backup_path)
    print(f"Backup saved: {backup_path}")
    
    df_edges.to_csv(edges_path, index=False)
    print(f"✅ Updated {edges_path}")
    
    # Verify
    part_of_edges_new = df_edges[df_edges['type'] == 'PART_OF']
    print(f"   PART_OF edges: {len(part_of_edges_new)}")
    
    # Check if song IDs match
    song_ids_in_edges = set(part_of_edges_new['to'].unique())
    song_ids_in_csv = set([f"song_{idx}" for idx in df_songs['id']])
    
    matched = len(song_ids_in_edges.intersection(song_ids_in_csv))
    print(f"   Matched song IDs: {matched}/{len(song_ids_in_edges)}")
    
    if matched < len(song_ids_in_edges):
        unmatched = song_ids_in_edges - song_ids_in_csv
        print(f"   ⚠️  Unmatched song IDs: {len(unmatched)}")
        print(f"   Sample unmatched: {list(unmatched)[:5]}")

if __name__ == "__main__":
    rebuild_part_of_edges()


#!/usr/bin/env python3
"""Check which multi-artist albums already have songs"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))


def list_albums_with_songs():
    """List multi-artist albums that already have songs"""
    
    # Load albums
    albums_file = "data/processed/albums.json"
    with open(albums_file, 'r', encoding='utf-8') as f:
        albums_data = json.load(f)
    
    # Load songs
    songs_file = "data/processed/songs.json"
    existing_songs = {}
    if os.path.exists(songs_file):
        with open(songs_file, 'r', encoding='utf-8') as f:
            existing_songs = json.load(f)
    
    # Find multi-artist albums with songs
    multi_artist_with_songs = []
    
    for album_name, artist_ids in albums_data.items():
        if len(artist_ids) >= 2:
            songs = existing_songs.get(album_name, [])
            # Filter out empty/invalid songs
            valid_songs = [s for s in songs if s.get('title') and len(s.get('title', '').strip()) > 2]
            
            if valid_songs:
                multi_artist_with_songs.append({
                    'album': album_name,
                    'artist_count': len(artist_ids),
                    'song_count': len(valid_songs)
                })
    
    # Sort by song count (descending)
    multi_artist_with_songs.sort(key=lambda x: x['song_count'], reverse=True)
    
    print("=" * 60)
    print("MULTI-ARTIST ALBUMS WITH SONGS")
    print("=" * 60)
    print(f"Total: {len(multi_artist_with_songs)} albums\n")
    
    # Show all albums
    for i, album_info in enumerate(multi_artist_with_songs[:20], 1):
        print(f"{i:3}. {album_info['album']} ({album_info['artist_count']} artists, {album_info['song_count']} songs)")


if __name__ == "__main__":
    list_albums_with_songs()



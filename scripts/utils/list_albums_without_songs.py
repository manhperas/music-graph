#!/usr/bin/env python3
"""List multi-artist albums without songs for manual review"""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))


def list_albums_without_songs():
    """List multi-artist albums without songs"""
    
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
    
    # Find multi-artist albums without songs
    multi_artist_without_songs = []
    
    for album_name, artist_ids in albums_data.items():
        if len(artist_ids) >= 2:
            songs = existing_songs.get(album_name, [])
            # Filter out empty/invalid songs
            valid_songs = [s for s in songs if s.get('title') and len(s.get('title', '').strip()) > 2]
            
            if not valid_songs:
                multi_artist_without_songs.append({
                    'album': album_name,
                    'artist_count': len(artist_ids),
                    'artists': artist_ids[:5]  # Show first 5 artists
                })
    
    # Sort by artist count (descending)
    multi_artist_without_songs.sort(key=lambda x: x['artist_count'], reverse=True)
    
    print("=" * 60)
    print("MULTI-ARTIST ALBUMS WITHOUT SONGS")
    print("=" * 60)
    print(f"Total: {len(multi_artist_without_songs)} albums\n")
    
    # Show all albums
    for i, album_info in enumerate(multi_artist_without_songs, 1):
        print(f"{i:3}. {album_info['album']} ({album_info['artist_count']} artists)")
        if album_info['artists']:
            artists_str = ", ".join(str(a) for a in album_info['artists'][:3])
            if len(album_info['artists']) > 3:
                artists_str += f", ... (+{len(album_info['artists']) - 3} more)"
            print(f"     Artists: {artists_str}")
    
    # Save to file for reference
    output_file = "albums_without_songs.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("MULTI-ARTIST ALBUMS WITHOUT SONGS\n")
        f.write("=" * 60 + "\n\n")
        for album_info in multi_artist_without_songs:
            f.write(f"{album_info['album']}\n")
    
    print(f"\n✓ Saved list to {output_file}")


if __name__ == "__main__":
    list_albums_without_songs()



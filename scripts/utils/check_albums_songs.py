#!/usr/bin/env python3
"""Check if any albums already have songs but weren't counted"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))


def check_albums_with_songs():
    """Check albums that have songs but might not be counted"""
    
    # Load albums
    albums_file = "data/processed/albums.json"
    with open(albums_file, 'r', encoding='utf-8') as f:
        albums_data = json.load(f)
    
    # Load songs
    songs_file = "data/processed/songs.json"
    with open(songs_file, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)
    
    # Find multi-artist albums
    multi_artist_albums = {k: v for k, v in albums_data.items() if len(v) >= 2}
    
    # Check each multi-artist album
    albums_with_songs = []
    albums_without_songs = []
    
    for album_name, artist_ids in multi_artist_albums.items():
        songs = songs_data.get(album_name, [])
        # Filter valid songs
        valid_songs = [s for s in songs if s.get('title') and len(s.get('title', '').strip()) > 2]
        
        if valid_songs:
            albums_with_songs.append({
                'album': album_name,
                'artist_count': len(artist_ids),
                'song_count': len(valid_songs),
                'songs': valid_songs[:5]  # First 5 songs
            })
        else:
            albums_without_songs.append(album_name)
    
    print("=" * 60)
    print("MULTI-ARTIST ALBUMS ANALYSIS")
    print("=" * 60)
    print(f"Total multi-artist albums: {len(multi_artist_albums)}")
    print(f"Albums with songs: {len(albums_with_songs)}")
    print(f"Albums without songs: {len(albums_without_songs)}")
    print(f"Coverage: {len(albums_with_songs)/len(multi_artist_albums)*100:.2f}%")
    
    print("\n" + "=" * 60)
    print("ALBUMS WITH SONGS:")
    print("=" * 60)
    for i, info in enumerate(albums_with_songs[:10], 1):
        print(f"{i}. {info['album']} ({info['artist_count']} artists, {info['song_count']} songs)")
        if info['songs']:
            print(f"   Sample songs: {', '.join(s['title'][:30] for s in info['songs'][:3])}")
    
    print("\n" + "=" * 60)
    print("CHECKING FOR POTENTIAL ISSUES:")
    print("=" * 60)
    
    # Check if any albums have empty song lists but are in songs_data
    albums_in_songs_but_empty = []
    for album_name in multi_artist_albums:
        if album_name in songs_data:
            songs = songs_data[album_name]
            valid_songs = [s for s in songs if s.get('title') and len(s.get('title', '').strip()) > 2]
            if not valid_songs and songs:
                albums_in_songs_but_empty.append({
                    'album': album_name,
                    'raw_songs': len(songs),
                    'valid_songs': 0,
                    'sample': songs[:3]
                })
    
    if albums_in_songs_but_empty:
        print(f"\nFound {len(albums_in_songs_but_empty)} albums with songs but invalid format:")
        for info in albums_in_songs_but_empty[:5]:
            print(f"  - {info['album']}: {info['raw_songs']} songs but none valid")
            print(f"    Sample: {info['sample']}")


if __name__ == "__main__":
    check_albums_with_songs()



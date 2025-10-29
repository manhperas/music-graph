#!/usr/bin/env python3
"""Process albums from updated raw data - standalone version"""

import json
import os
from collections import defaultdict

def main():
    """Main processing function"""
    
    # Step 1: Load raw data
    print("=" * 60)
    print("LOADING RAW DATA")
    print("=" * 60)
    
    with open("data/raw/artists.json", 'r', encoding='utf-8') as f:
        raw_artists = json.load(f)
    
    print(f"Loaded {len(raw_artists)} artists")
    
    # Step 2: Extract albums
    print("\n" + "=" * 60)
    print("EXTRACTING ALBUMS")
    print("=" * 60)
    
    album_map = defaultdict(list)  # album_name -> [artist_names]
    
    for artist in raw_artists:
        artist_name = artist.get('title', '')
        albums = artist.get('albums', [])
        
        for album in albums:
            if isinstance(album, str):
                album_title = album.strip()
            elif isinstance(album, dict):
                album_title = album.get('title', '').strip()
            else:
                continue
            
            if album_title and len(album_title) > 1:
                album_map[album_title].append(artist_name)
    
    print(f"Found {len(album_map)} unique albums")
    
    # Step 3: Filter albums with 2+ artists for graph
    multi_artist_albums = {k: v for k, v in album_map.items() if len(v) >= 2}
    
    print(f"Albums with 2+ artists: {len(multi_artist_albums)}")
    
    # Step 4: Save albums
    print("\n" + "=" * 60)
    print("SAVING ALBUMS")
    print("=" * 60)
    
    os.makedirs("data/processed", exist_ok=True)
    
    # Save all albums
    with open("data/processed/albums.json", 'w', encoding='utf-8') as f:
        json.dump(dict(album_map), f, ensure_ascii=False, indent=2)
    
    # Save multi-artist albums
    with open("data/processed/albums_multi_artist.json", 'w', encoding='utf-8') as f:
        json.dump(multi_artist_albums, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved albums to data/processed/albums.json")
    print(f"✓ Saved multi-artist albums to data/processed/albums_multi_artist.json")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print(f"Total unique albums: {len(album_map)}")
    print(f"Albums with 2+ artists: {len(multi_artist_albums)}")
    print(f"Albums with 1 artist: {len(album_map) - len(multi_artist_albums)}")
    
    # Count total albums
    total_album_count = sum(len(albums) for albums in album_map.values())
    print(f"Total album-artist relationships: {total_album_count}")
    
    # Show sample multi-artist albums
    print("\nTop 10 multi-artist albums:")
    sorted_albums = sorted(multi_artist_albums.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (album, artists) in enumerate(sorted_albums[:10], 1):
        print(f"  {i}. {album}: {len(artists)} artists")
        print(f"     Artists: {', '.join(artists[:5])}")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""Clean albums.json to remove parsing artifacts"""

import json
import re
import os
from pathlib import Path

def validate_album_name(album_name: str) -> bool:
    """Validate album name to filter out parsing artifacts"""
    if not album_name:
        return False
    
    album_name = album_name.strip()
    
    # Basic length checks
    if len(album_name) < 4:
        return False
    
    # Filter out names starting with single lowercase letter + space (parsing artifacts)
    # Examples: "n trên Pop Chronicles", "u tay Hybrid Theory", "c Sweetener"
    if re.match(r'^[a-z]\s+', album_name):
        return False
    
    # Filter out names starting with Vietnamese incomplete words
    # But keep valid English names starting with "A" (like "A Star Is Born")
    vietnamese_incomplete = [
        r'^nh\s+', r'^ng\s+', r'^của\s+', r'^trên\s+', 
        r'^c\s+[A-Z][a-z]{0,15}$',  # "c Sweetener" but not "A Star Is Born"
        r'^y\s+', r'^p\s+', 
        r'^u\s+tay\s+',  # "u tay ..."
        r'^n\s+công', r'^a\s+ông',  # Vietnamese incomplete
        r'^t\s+[a-z]',  # "t Fearless" but check for valid "The ..."
    ]
    
    # Allow "A" or "The" at start (valid English articles)
    if re.match(r'^(A|The)\s+[A-Z]', album_name):
        return True
    for pattern in vietnamese_incomplete:
        if re.match(pattern, album_name, re.IGNORECASE):
            return False
    
    return True

def clean_albums_json(input_file: str = "data/processed/albums.json",
                     output_file: str = "data/processed/albums.json"):
    """Clean albums.json to remove invalid album names"""
    
    print("=" * 60)
    print("CLEANING ALBUMS.JSON")
    print("=" * 60)
    
    # Load albums
    with open(input_file, 'r', encoding='utf-8') as f:
        albums_data = json.load(f)
    
    print(f"Original albums: {len(albums_data)}")
    
    # Clean albums
    cleaned_albums = {}
    removed_albums = []
    
    for album_name, artist_ids in albums_data.items():
        if validate_album_name(album_name):
            cleaned_albums[album_name] = artist_ids
        else:
            removed_albums.append((album_name, len(artist_ids)))
    
    print(f"Cleaned albums: {len(cleaned_albums)}")
    print(f"Removed: {len(removed_albums)} invalid albums")
    
    if removed_albums:
        print("\nRemoved albums:")
        for name, artist_count in sorted(removed_albums, key=lambda x: x[1], reverse=True):
            print(f"  \"{name}\" ({artist_count} artists)")
    
    # Check multi-artist albums
    multi_artist_albums = {k: v for k, v in cleaned_albums.items() if len(v) >= 2}
    print(f"\nMulti-artist albums (2+): {len(multi_artist_albums)}")
    
    # Save cleaned data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_albums, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved cleaned albums to {output_file}")
    print(f"  → Backup original: {input_file}.backup")
    
    # Create backup
    backup_file = f"{input_file}.backup"
    if not os.path.exists(backup_file):
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(albums_data, f, ensure_ascii=False, indent=2)
        print(f"  → Created backup: {backup_file}")
    
    return cleaned_albums

if __name__ == "__main__":
    clean_albums_json()


#!/usr/bin/env python3
"""Compare old and new parsed data to validate improvements"""

import json
import sys
from collections import Counter

def load_json(path):
    """Load JSON file"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        return None

def analyze_albums(artists):
    """Analyze album data"""
    total_albums = 0
    artists_with_albums = 0
    album_titles = []
    bad_patterns = []
    
    for artist in artists:
        albums = artist.get('albums', [])
        if albums:
            artists_with_albums += 1
            total_albums += len(albums)
            for album in albums:
                if isinstance(album, dict):
                    title = album.get('title', '')
                else:
                    title = str(album)
                
                if title:
                    album_titles.append(title)
                    
                    # Check for bad patterns
                    title_lower = title.lower()
                    if any(pattern in title_lower for pattern in ['đầu tay', 'tư ', 'của ', 'album của', 'by ', 'of ']):
                        bad_patterns.append(title)
    
    return {
        'total_albums': total_albums,
        'artists_with_albums': artists_with_albums,
        'unique_albums': len(set(album_titles)),
        'bad_patterns': bad_patterns,
        'bad_count': len(bad_patterns)
    }

def analyze_genres(artists):
    """Analyze genre data"""
    artists_with_genres = 0
    total_genres = 0
    all_genres = []
    
    for artist in artists:
        genres = artist.get('genres', [])
        if genres:
            artists_with_genres += 1
            total_genres += len(genres)
            all_genres.extend(genres)
    
    return {
        'artists_with_genres': artists_with_genres,
        'total_genres': total_genres,
        'unique_genres': len(set(all_genres)),
        'coverage': artists_with_genres / len(artists) * 100 if artists else 0
    }

def main():
    """Compare old and new parsed data"""
    
    # Find backup file
    import glob
    backup_files = glob.glob('data/processed/parsed_artists_backup_*.json')
    if not backup_files:
        print("Error: No backup file found")
        print("Looking for: data/processed/parsed_artists_backup_*.json")
        return
    
    backup_file = sorted(backup_files)[-1]  # Get most recent backup
    new_file = 'data/processed/parsed_artists.json'
    
    print("=" * 60)
    print("PARSED DATA COMPARISON")
    print("=" * 60)
    print(f"\nOld data (backup): {backup_file}")
    print(f"New data: {new_file}\n")
    
    # Load data
    old_data = load_json(backup_file)
    new_data = load_json(new_file)
    
    if not old_data or not new_data:
        return
    
    print(f"Total artists:")
    print(f"  Old: {len(old_data)}")
    print(f"  New: {len(new_data)}")
    print(f"  Difference: {len(new_data) - len(old_data):+d}\n")
    
    # Analyze genres
    print("=" * 60)
    print("GENRE ANALYSIS")
    print("=" * 60)
    
    old_genres = analyze_genres(old_data)
    new_genres = analyze_genres(new_data)
    
    print(f"\nArtists with genres:")
    print(f"  Old: {old_genres['artists_with_genres']} ({old_genres['coverage']:.1f}%)")
    print(f"  New: {new_genres['artists_with_genres']} ({new_genres['coverage']:.1f}%)")
    print(f"  Change: {new_genres['artists_with_genres'] - old_genres['artists_with_genres']:+d} ({new_genres['coverage'] - old_genres['coverage']:+.1f}%)")
    
    print(f"\nUnique genres:")
    print(f"  Old: {old_genres['unique_genres']}")
    print(f"  New: {new_genres['unique_genres']}")
    print(f"  Change: {new_genres['unique_genres'] - old_genres['unique_genres']:+d}")
    
    # Analyze albums
    print("\n" + "=" * 60)
    print("ALBUM ANALYSIS")
    print("=" * 60)
    
    old_albums = analyze_albums(old_data)
    new_albums = analyze_albums(new_data)
    
    print(f"\nArtists with albums:")
    print(f"  Old: {old_albums['artists_with_albums']}")
    print(f"  New: {new_albums['artists_with_albums']}")
    print(f"  Change: {new_albums['artists_with_albums'] - old_albums['artists_with_albums']:+d}")
    
    print(f"\nTotal albums:")
    print(f"  Old: {old_albums['total_albums']}")
    print(f"  New: {new_albums['total_albums']}")
    print(f"  Change: {new_albums['total_albums'] - old_albums['total_albums']:+d}")
    
    print(f"\nUnique albums:")
    print(f"  Old: {old_albums['unique_albums']}")
    print(f"  New: {new_albums['unique_albums']}")
    print(f"  Change: {new_albums['unique_albums'] - old_albums['unique_albums']:+d}")
    
    print(f"\nBad patterns detected:")
    print(f"  Old: {old_albums['bad_count']}")
    if old_albums['bad_patterns']:
        print(f"  Examples: {', '.join(old_albums['bad_patterns'][:5])}")
    print(f"  New: {new_albums['bad_count']}")
    if new_albums['bad_patterns']:
        print(f"  Examples: {', '.join(new_albums['bad_patterns'][:5])}")
    else:
        print(f"  ✓ No bad patterns found!")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    improvements = []
    if new_genres['coverage'] > old_genres['coverage']:
        improvements.append(f"✓ Genre coverage improved: {old_genres['coverage']:.1f}% → {new_genres['coverage']:.1f}%")
    if new_albums['bad_count'] < old_albums['bad_count']:
        improvements.append(f"✓ Bad album patterns reduced: {old_albums['bad_count']} → {new_albums['bad_count']}")
    if new_albums['unique_albums'] > old_albums['unique_albums']:
        improvements.append(f"✓ More unique albums extracted: {old_albums['unique_albums']} → {new_albums['unique_albums']}")
    
    if improvements:
        print("\nImprovements:")
        for imp in improvements:
            print(f"  {imp}")
    else:
        print("\nNo significant improvements detected")
    
    print()

if __name__ == "__main__":
    main()


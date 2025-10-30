#!/usr/bin/env python3
"""Clean album data to remove false positives"""

import json
import re

def is_valid_album_name(album_name):
    """Check if album name is valid"""
    album_name = album_name.strip()
    
    # Filter out common false positives
    false_positives = [
        'yes', 'no', 'all', 'one', 'two', 'three', 'four', 'five',
        'six', 'seven', 'eight', 'nine', 'ten', 'ref', 'web',
        'review', 'citation', 'billboard', 'magic', 'week'
    ]
    
    # Filter out year-only patterns
    year_pattern = r'^\(\d{4}\)$'
    
    # Filter out single characters or numbers
    if len(album_name) <= 1 or album_name.isdigit():
        return False
    
    # Filter out common words
    if album_name.lower() in false_positives:
        return False
    
    # Filter out year patterns
    if re.match(year_pattern, album_name):
        return False
    
    # Filter out names that are too short
    if len(album_name) < 4:
        return False
    
    # Filter out names that start with special characters
    if album_name[0] in ['(', '[', '{', '/', '\\', '-', '_']:
        return False
    
    # Filter out incomplete text (ends with odd characters)
    if album_name[-1] in ['(', '[', '{', '/', '\\']:
        return False
    
    # Filter out wiki markup that wasn't cleaned
    if '}}' in album_name or '{{' in album_name or '</ref>' in album_name:
        return False
    
    # Filter out names that look like incomplete extractions
    # (single word that's a common name, or very short)
    if len(album_name.split()) == 1 and len(album_name) < 8:
        # Allow single-word album names that are long enough
        if len(album_name) < 8:
            return False
    
    # Filter out Vietnamese partial words and phrases
    vietnamese_patterns = [
        r'^ng\s', r'^của\s', r'^được\s', r'^là\s', r'^có\s',
        r'^trong\s', r'^với\s', r'^theo\s', r'^từ\s',
        r'nh tên', r'a cô', r'ng tên', r'tên cô'
    ]
    for pattern in vietnamese_patterns:
        if re.search(pattern, album_name, re.IGNORECASE):
            return False
    
    # Filter out incomplete album names
    incomplete_patterns = [
        r'^to\s', r'^a\s', r'^an\s', r'^the\s[A-Z][a-z]+$',  # Single article + word
        r'^Book\s+(I|II|III|IV|V|1|2|3|4|5)$',  # Book I, Book II, etc.
    ]
    for pattern in incomplete_patterns:
        if re.match(pattern, album_name, re.IGNORECASE):
            return False
    
    # Filter out generic words that aren't specific enough
    generic_words = [
        'book', 'chapter', 'part', 'section', 'volume', 'edition',
        'version', 'demo', 'remix', 'edit', 'mix', 'cut'
    ]
    words = album_name.lower().split()
    if len(words) == 1 and words[0] in generic_words:
        return False
    
    # Filter out album names that are too generic/common
    # These are legitimate but appear too frequently across different artists
    overly_common = ['celebration', 'greatest hits', 'best of', 'collection', 'anthology']
    if album_name.lower() in overly_common:
        return False
    
    return True

def clean_albums():
    """Clean album data"""
    
    # Load albums
    with open('data/processed/albums.json', 'r', encoding='utf-8') as f:
        albums = json.load(f)
    
    print(f"Original albums: {len(albums)}")
    
    # Filter albums
    cleaned_albums = {}
    for album_name, artists in albums.items():
        if is_valid_album_name(album_name):
            cleaned_albums[album_name] = artists
    
    print(f"Cleaned albums: {len(cleaned_albums)}")
    print(f"Removed: {len(albums) - len(cleaned_albums)} false positives")
    
    # Filter multi-artist albums
    multi_artist_albums = {k: v for k, v in cleaned_albums.items() if len(v) >= 2}
    
    print(f"\nMulti-artist albums (2+): {len(multi_artist_albums)}")
    
    # Save cleaned data
    with open('data/processed/albums.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_albums, f, ensure_ascii=False, indent=2)
    
    with open('data/processed/albums_multi_artist.json', 'w', encoding='utf-8') as f:
        json.dump(multi_artist_albums, f, ensure_ascii=False, indent=2)
    
    print("\n✓ Saved cleaned albums")
    
    # Show top multi-artist albums
    print("\nTop 10 multi-artist albums:")
    sorted_albums = sorted(multi_artist_albums.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (album, artists) in enumerate(sorted_albums[:10], 1):
        print(f"  {i}. {album}: {len(artists)} artists")

if __name__ == "__main__":
    clean_albums()


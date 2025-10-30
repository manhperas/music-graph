#!/usr/bin/env python3
"""Extract albums from existing raw data using improved extraction methods"""

import json
import re
import sys
from pathlib import Path

def clean_text(text):
    """Clean text"""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_albums_from_text(text, summary):
    """Extract album names from text content using regex patterns"""
    albums = []
    combined_text = f"{summary} {text[:5000]}"
    
    # Enhanced patterns for Vietnamese Wikipedia
    patterns = [
        # "album Title (YYYY)" format
        r'album\s+([A-ZĂÂÊÔƠƯĐ][^(\n]{2,50}?)\s*\((\d{4})\)',
        # "Title (YYYY)" format
        r'([A-ZĂÂÊÔƠƯĐ][A-Za-zĂâÊôƠơƯđ\s&\'\"]{2,50}?)\s*\((\d{4})\)',
        # "Album: Title" format
        r'Album:\s*([A-ZĂÂÊÔƠƯĐ][^:\n]{2,50})',
        # "Đĩa nhạc: Title" format
        r'Đĩa nhạc:\s*([A-ZĂÂÊÔƠƯĐ][^:\n]{2,50})',
        # Match album names in [[links]]
        r'\[\[([A-ZĂÂÊÔƠƯĐ][A-Za-zĂâÊôƠơƯđ\s&\'\"\d]{2,50})\]\](?:\s*\((\d{4})\))?',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            album_name = match.group(1).strip()
            # Clean the album name
            album_name = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', album_name)
            album_name = re.sub(r"'''?([^']+)'''?", r'\1', album_name)
            album_name = re.sub(r'<[^>]+>', '', album_name)
            album_name = clean_text(album_name)
            
            # Filter out common false positives
            false_positives = [
                'phát hành', 'năm', 'phòng thu', 'thứ', 'bài hát', 
                'single', 'đĩa đơn', 'ep', 'album', 'song', 'track',
                'bản thu', 'ghi âm', 'tháng', 'ngày', 'tuần', 'review',
                'ref', 'chú thích', 'web', 'citation', 'yes', 'no'
            ]
            
            # Additional filters
            is_year_only = album_name.strip() in ['(2008)', '(2009)', '(2010)', '(2011)', '(2012)', '(2013)', '(2014)', '(2015)', '(2016)', '(2017)', '(2018)', '(2019)', '(2020)', '(2021)', '(2022)', '(2023)', '(2024)']
            is_common_word = album_name.lower() in ['yes', 'no', 'all', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
            starts_with_digit = album_name[0].isdigit() if album_name else False
            
            if (album_name and 
                len(album_name) > 2 and 
                len(album_name) < 100 and
                not any(word in album_name.lower() for word in false_positives) and
                not album_name.isdigit() and
                not is_year_only and
                not is_common_word and
                not starts_with_digit):
                albums.append(album_name)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_albums = []
    for album in albums:
        normalized = album.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            unique_albums.append(album)
    
    return unique_albums[:30]

def extract_albums_from_infobox(infobox_text):
    """Extract album names from infobox wikitext"""
    albums = []
    if not infobox_text:
        return albums
    
    # Simple regex extraction from infobox
    # Look for album names in various formats
    patterns = [
        r'album[^=]*=\s*([^|\n]+)',
        r'đĩa nhạc[^=]*=\s*([^|\n]+)',
        r'discography[^=]*=\s*([^|\n]+)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, infobox_text, re.IGNORECASE)
        for match in matches:
            album_text = match.group(1).strip()
            # Split by common separators
            items = re.split(r'[,;\n•]|<br\s*/?>', album_text)
            for item in items:
                item = clean_text(item)
                if item and len(item) > 2 and len(item) < 100:
                    albums.append(item)
    
    return albums[:20]

def process_raw_data(input_path, output_path):
    """Process raw data and add albums"""
    print(f"Loading data from {input_path}...")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        artists = json.load(f)
    
    print(f"Found {len(artists)} artists")
    print("Extracting albums...")
    
    total_albums = 0
    artists_with_albums = 0
    
    for i, artist in enumerate(artists, 1):
        # Extract albums from text
        text = artist.get('text', '')
        summary = artist.get('summary', '')
        infobox = artist.get('infobox', '')
        
        albums_from_text = extract_albums_from_text(text, summary)
        albums_from_infobox = extract_albums_from_infobox(infobox)
        
        # Combine albums
        all_albums = list(set(albums_from_text + albums_from_infobox))
        
        # Add albums to artist data
        artist['albums'] = all_albums
        
        total_albums += len(all_albums)
        if all_albums:
            artists_with_albums += 1
        
        if i % 100 == 0:
            print(f"Processed {i}/{len(artists)} artists...")
    
    print(f"\nExtraction complete:")
    print(f"  - Artists with albums: {artists_with_albums}/{len(artists)}")
    print(f"  - Total albums: {total_albums}")
    print(f"  - Average albums per artist: {total_albums/len(artists):.1f}")
    
    # Save updated data
    print(f"\nSaving updated data to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)
    
    print("✓ Done!")
    
    return artists

if __name__ == "__main__":
    input_path = "data/raw/artists.json"
    output_path = "data/raw/artists_with_albums.json"
    
    artists = process_raw_data(input_path, output_path)
    
    # Show some sample results
    print("\n" + "=" * 60)
    print("SAMPLE RESULTS")
    print("=" * 60)
    
    sample_artists = [a for a in artists if a.get('albums')][:5]
    for artist in sample_artists:
        print(f"\n{artist['title']}:")
        for album in artist['albums'][:5]:
            print(f"  • {album}")


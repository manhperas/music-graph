#!/usr/bin/env python3
"""Filter out non-artist entries (songs/albums) from nodes.csv"""

import csv
import re

def is_artist_name(name):
    """Check if name is actually an artist (not a song/album)"""
    if not name:
        return False
    
    # Filter out songs and albums with patterns like:
    # - "(album của ...)"
    # - "(bài hát của ...)"
    # - "(song của ...)"
    # - "(single của ...)"
    false_patterns = [
        '(album của',
        '(bài hát của',
        '(song của',
        '(single của',
        '(song by',
        '(album by',
        '(single by'
    ]
    
    for pattern in false_patterns:
        if pattern in name.lower():
            return False
    
    return True

def filter_nodes(input_file, output_file):
    """Filter nodes.csv to remove non-artist entries"""
    print(f"Reading {input_file}...")
    
    filtered_rows = []
    removed_rows = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            name = row.get('name', '')
            if is_artist_name(name):
                filtered_rows.append(row)
            else:
                removed_rows.append(name)
    
    print(f"Removed {len(removed_rows)} non-artist entries:")
    for name in removed_rows[:20]:  # Show first 20
        print(f"  - {name}")
    if len(removed_rows) > 20:
        print(f"  ... and {len(removed_rows) - 20} more")
    
    print(f"\nWriting {len(filtered_rows)} artist nodes to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)
    
    print(f"✓ Done! Filtered nodes saved to {output_file}")
    print(f"  - Original: {len(filtered_rows) + len(removed_rows)} nodes")
    print(f"  - Filtered: {len(filtered_rows)} nodes")
    print(f"  - Removed: {len(removed_rows)} non-artist entries")

if __name__ == "__main__":
    input_file = "data/processed/nodes.csv"
    output_file = "data/processed/nodes_filtered.csv"
    
    filter_nodes(input_file, output_file)


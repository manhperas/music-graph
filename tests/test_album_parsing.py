#!/usr/bin/env python3
"""Test album parsing improvements"""

import sys
sys.path.insert(0, 'src')

from data_processing.parser import InfoboxParser

def test_album_validation():
    """Test album name validation"""
    parser = InfoboxParser()
    
    # Test cases: (album_name, should_be_valid)
    test_cases = [
        # Valid albums
        ("1989", True),
        ("Red", True),
        ("Taylor Swift", True),
        ("Fearless (Taylor's Version)", True),
        ("Midnights", True),
        ("The Tortured Poets Department", True),
        
        # Invalid albums - Vietnamese bad patterns
        ("đầu tay Taylor Swift", False),
        ("tư Red", False),
        ("của Taylor Swift", False),
        ("được Taylor Swift", False),
        ("album của Taylor Swift", False),
        
        # Invalid albums - incomplete patterns
        ("to Taylor Swift", False),
        ("by Taylor Swift", False),
        ("of Taylor Swift", False),
        ("album by Taylor Swift", False),
        
        # Invalid albums - artifacts
        ("(2008)", False),
        ("}}", False),
        ("{{", False),
        ("|", False),
        ("*", False),
        
        # Invalid albums - too short
        ("ab", False),
        ("abc", False),
        ("yes", False),
        ("no", False),
        
        # Invalid albums - generic words
        ("album", False),
        ("single", False),
        ("ep", False),
        
        # Invalid albums - incomplete
        ("the album", False),  # Only common words
        ("of the", False),
    ]
    
    print("Testing album validation...")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for album_name, expected_valid in test_cases:
        result = parser._validate_album_name(album_name)
        status = "✓" if result == expected_valid else "✗"
        
        if result == expected_valid:
            passed += 1
        else:
            failed += 1
            print(f"{status} FAILED: '{album_name}' - Expected {expected_valid}, Got {result}")
        
        if result == expected_valid:
            print(f"{status} PASS: '{album_name}' -> {result}")
    
    print("-" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    return failed == 0

def test_album_parsing():
    """Test album field parsing"""
    parser = InfoboxParser()
    
    # Test infobox parsing with album field
    test_infobox = """
    {{Infobox musical artist
    | name = Test Artist
    | albums = [[1989]], [[Red]], [[Taylor Swift]]
    }}
    """
    
    parsed = parser.parse_infobox(test_infobox)
    albums = parsed.get('albums', [])
    
    print("\nTesting album field parsing...")
    print("-" * 60)
    print(f"Extracted {len(albums)} albums:")
    for album in albums:
        print(f"  - {album.get('title', 'N/A')}")
    
    # Test with Vietnamese bad patterns
    test_infobox_bad = """
    {{Infobox musical artist
    | name = Test Artist
    | albums = [[đầu tay Taylor Swift]], [[tư Red]], [[1989]]
    }}
    """
    
    parsed_bad = parser.parse_infobox(test_infobox_bad)
    albums_bad = parsed_bad.get('albums', [])
    
    print(f"\nTesting with bad patterns (should filter them):")
    print(f"Extracted {len(albums_bad)} albums (should be 1):")
    for album in albums_bad:
        title = album.get('title', 'N/A')
        is_valid = parser._validate_album_name(title)
        print(f"  - {title} (valid: {is_valid})")
    
    return len(albums_bad) == 1 or all(parser._validate_album_name(a.get('title', '')) for a in albums_bad)

if __name__ == "__main__":
    print("=" * 60)
    print("ALBUM PARSING TEST SUITE")
    print("=" * 60)
    
    validation_ok = test_album_validation()
    parsing_ok = test_album_parsing()
    
    print("\n" + "=" * 60)
    if validation_ok and parsing_ok:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)


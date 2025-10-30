"""
Band Classification Script

Analyzes Wikipedia categories and other indicators to classify artists as bands or solo artists.
"""

import json
import os
import re
import sys
import time
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import wikipediaapi
    import requests
except ImportError as e:
    print(f"Error: Required packages not installed. Please run: pip install -r requirements.txt")
    print(f"Missing: {e}")
    sys.exit(1)


class BandClassifier:
    """Classify artists as bands or solo artists based on Wikipedia data"""
    
    def __init__(self, language: str = 'vi', rate_limit_delay: float = 0.5):
        """Initialize classifier with Wikipedia API"""
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='MusicNetworkProject/1.0 (test@example.com)',
            language=language
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MusicNetworkProject/1.0 (test@example.com)'
        })
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
        # Band-indicating category keywords (Vietnamese and English)
        self.band_category_keywords = {
            # Vietnamese
            'nhóm nhạc', 'ban nhạc', 'nhạc đoàn', 'đội nhạc',
            'group', 'band', 'bands',
            # English (for fallback)
            'musical groups', 'bands', 'music groups', 'rock bands',
            'pop groups', 'boy bands', 'girl groups'
        }
        
        # Solo artist-indicating category keywords
        self.solo_category_keywords = {
            # Vietnamese
            'ca sĩ', 'nghệ sĩ', 'nhạc sĩ', 'ca sĩ-nhạc sĩ',
            'solo', 'singer', 'songwriter', 'musician', 'solo artist'
        }
        
        # Name patterns that suggest bands
        self.band_name_patterns = [
            r'^the\s+[a-z]+',  # "The Beatles", "The Chainsmokers"
            r'&',  # "Simon & Garfunkel"
            r'\sand\s+',  # "Hall & Oates"
            r'[a-z]+\s+[a-z]+\s+[a-z]+',  # Multi-word names more likely bands
        ]
        
        # Name patterns that suggest solo artists
        self.solo_name_patterns = [
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # "Taylor Swift", "Ed Sheeran" (First Last)
        ]
        
        # Solo artists with "The" prefix (exceptions)
        self.solo_with_the = {
            'The Weeknd', 'The Kid LAROI', 'The Game', 'The Notorious B.I.G.'
        }
        
        # Patterns that indicate songs/albums (not artists)
        self.song_album_patterns = [
            r'\(bài hát của',  # "(bài hát của ...)"
            r'\(album của',     # "(album của ...)"
            r'\(song by',       # "(song by ...)"
            r'\(album by',      # "(album by ...)"
            r'original soundtrack',
            r'soundtrack album',
            r'\(bài hát\)',
            r'\(album\)',
            r'\(song\)',
            r'\(single\)',
            r'\(ep\)',
            r'\(soundtrack\)',
        ]
        
    def fetch_categories(self, page_title: str) -> List[str]:
        """Fetch Wikipedia categories for a page using MediaWiki API"""
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
        
        try:
            url = f"https://vi.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'prop': 'categories',
                'titles': page_title,
                'cllimit': 'max',
                'format': 'json',
                'formatversion': 2
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', [])
            if not pages:
                return []
            
            categories = []
            for page in pages:
                cats = page.get('categories', [])
                for cat in cats:
                    cat_title = cat.get('title', '')
                    # Remove "Category:" prefix
                    if cat_title.startswith('Thể loại:'):
                        cat_title = cat_title.replace('Thể loại:', '').strip()
                    elif cat_title.startswith('Category:'):
                        cat_title = cat_title.replace('Category:', '').strip()
                    if cat_title:
                        categories.append(cat_title)
            
            return categories
            
        except Exception as e:
            print(f"Error fetching categories for {page_title}: {e}")
            return []
    
    def analyze_categories(self, categories: List[str]) -> Dict[str, any]:
        """Analyze categories to determine band indicators"""
        band_score = 0
        solo_score = 0
        indicators = []
        
        categories_lower = [cat.lower() for cat in categories]
        
        # Check for band keywords
        for cat in categories_lower:
            for keyword in self.band_category_keywords:
                if keyword.lower() in cat:
                    band_score += 1
                    indicators.append(f"Band category: {cat}")
                    break
        
        # Check for solo keywords
        for cat in categories_lower:
            for keyword in self.solo_category_keywords:
                if keyword.lower() in cat:
                    solo_score += 1
                    indicators.append(f"Solo category: {cat}")
                    break
        
        return {
            'band_score': band_score,
            'solo_score': solo_score,
            'indicators': indicators
        }
    
    def is_song_or_album(self, name: str) -> bool:
        """Check if name is likely a song or album, not an artist"""
        name_lower = name.lower()
        for pattern in self.song_album_patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                return True
        return False
    
    def analyze_name_patterns(self, name: str) -> Dict[str, any]:
        """Analyze name patterns to determine if band or solo"""
        band_score = 0
        solo_score = 0
        indicators = []
        
        name_lower = name.lower()
        
        # Check if it's a known solo artist with "The"
        if name in self.solo_with_the:
            solo_score += 3
            indicators.append(f"Known solo artist with 'The': {name}")
        
        # Check band patterns
        for pattern in self.band_name_patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                # But skip if it's a known solo artist exception
                if name not in self.solo_with_the:
                    band_score += 1
                    indicators.append(f"Band name pattern: {pattern}")
        
        # Check solo patterns
        for pattern in self.solo_name_patterns:
            if re.match(pattern, name):
                solo_score += 1
                indicators.append(f"Solo name pattern: {pattern}")
        
        # Specific patterns
        if name.startswith('The '):
            if name in self.solo_with_the:
                solo_score += 2
                indicators.append(f"Known solo artist exception: {name}")
            else:
                band_score += 2
                indicators.append("Name starts with 'The'")
        
        if '&' in name or ' and ' in name.lower():
            band_score += 2
            indicators.append("Name contains '&' or 'and'")
        
        return {
            'band_score': band_score,
            'solo_score': solo_score,
            'indicators': indicators
        }
    
    def analyze_infobox(self, infobox_text: str) -> Dict[str, any]:
        """Analyze infobox for band indicators"""
        if not infobox_text:
            return {'band_score': 0, 'solo_score': 0, 'indicators': []}
        
        band_score = 0
        solo_score = 0
        indicators = []
        
        infobox_lower = infobox_text.lower()
        
        # Check for members field (strong band indicator)
        members_patterns = [
            r'members\s*=', r'thành viên\s*=', r'current members',
            r'past members', r'cựu thành viên'
        ]
        for pattern in members_patterns:
            if re.search(pattern, infobox_lower):
                band_score += 3
                indicators.append(f"Found members field: {pattern}")
                break
        
        # Check for background field
        if 'background = solo_singer' in infobox_lower or 'background=solo_singer' in infobox_lower:
            solo_score += 2
            indicators.append("Infobox indicates solo singer")
        
        if 'background = group' in infobox_lower or 'background=group' in infobox_lower:
            band_score += 3
            indicators.append("Infobox indicates group")
        
        return {
            'band_score': band_score,
            'solo_score': solo_score,
            'indicators': indicators
        }
    
    def analyze_text_content(self, text: str, summary: str) -> Dict[str, any]:
        """Analyze text content for band indicators"""
        combined_text = f"{summary} {text[:2000]}".lower()
        
        band_score = 0
        solo_score = 0
        indicators = []
        
        # Band indicators in text
        band_text_patterns = [
            r'nhóm nhạc', r'ban nhạc', r'nhạc đoàn',
            r'formed', r'band', r'group', r'members',
            r'thành viên', r'các thành viên'
        ]
        for pattern in band_text_patterns:
            matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
            if matches > 0:
                band_score += min(matches, 2)  # Cap at 2 per pattern
                indicators.append(f"Band text pattern: {pattern} ({matches} matches)")
        
        # Solo indicators in text
        solo_text_patterns = [
            r'ca sĩ', r'nghệ sĩ', r'nhạc sĩ', r'solo artist',
            r'singer', r'songwriter', r'là một.*ca sĩ'
        ]
        for pattern in solo_text_patterns:
            matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
            if matches > 0:
                solo_score += min(matches, 2)  # Cap at 2 per pattern
                indicators.append(f"Solo text pattern: {pattern} ({matches} matches)")
        
        return {
            'band_score': band_score,
            'solo_score': solo_score,
            'indicators': indicators
        }
    
    def classify_artist(self, artist_data: Dict) -> Dict[str, any]:
        """Classify a single artist as band or solo"""
        name = artist_data.get('title', artist_data.get('name', ''))
        infobox = artist_data.get('infobox', '')
        text = artist_data.get('text', '')
        summary = artist_data.get('summary', '')
        
        # Skip if it's clearly a song or album
        if self.is_song_or_album(name):
            return {
                'name': name,
                'classification': 'filtered',
                'confidence': 1.0,
                'band_score': 0,
                'solo_score': 0,
                'categories': [],
                'indicators': [f"Filtered: detected as song/album, not artist"],
                'reason': 'song_or_album'
            }
        
        # Fetch categories
        categories = self.fetch_categories(name)
        
        # Analyze all indicators
        category_analysis = self.analyze_categories(categories)
        name_analysis = self.analyze_name_patterns(name)
        infobox_analysis = self.analyze_infobox(infobox)
        text_analysis = self.analyze_text_content(text, summary)
        
        # Aggregate scores
        total_band_score = (
            category_analysis['band_score'] +
            name_analysis['band_score'] +
            infobox_analysis['band_score'] +
            text_analysis['band_score']
        )
        
        total_solo_score = (
            category_analysis['solo_score'] +
            name_analysis['solo_score'] +
            infobox_analysis['solo_score'] +
            text_analysis['solo_score']
        )
        
        # Collect all indicators first
        all_indicators = (
            category_analysis['indicators'] +
            name_analysis['indicators'] +
            infobox_analysis['indicators'] +
            text_analysis['indicators']
        )
        
        # Determine classification
        # If both scores are 0, it's likely not a valid artist entry
        if total_band_score == 0 and total_solo_score == 0:
            classification = 'filtered'
            confidence = 0.0
            all_indicators.append("No indicators found - likely not a valid artist entry")
        elif total_band_score > total_solo_score:
            classification = 'band'
            confidence = min(total_band_score / (total_band_score + total_solo_score + 1), 1.0)
        elif total_solo_score > total_band_score:
            classification = 'solo'
            confidence = min(total_solo_score / (total_band_score + total_solo_score + 1), 1.0)
        else:
            # Tie - check if we have any indicators at all
            if len(all_indicators) > 0:
                classification = 'unknown'
                confidence = 0.5
            else:
                classification = 'filtered'
                confidence = 0.0
                all_indicators.append("No clear indicators - likely not a valid artist entry")
        
        return {
            'name': name,
            'classification': classification,
            'confidence': round(confidence, 3),
            'band_score': total_band_score,
            'solo_score': total_solo_score,
            'categories': categories,
            'indicators': all_indicators,
            'category_analysis': category_analysis,
            'name_analysis': name_analysis,
            'infobox_analysis': infobox_analysis,
            'text_analysis': text_analysis
        }
    
    def classify_artists(self, artists: List[Dict], verbose: bool = False) -> List[Dict]:
        """Classify multiple artists"""
        results = []
        total = len(artists)
        
        for i, artist in enumerate(artists, 1):
            artist_name = artist.get('title', artist.get('name', 'Unknown'))
            if verbose or i % 50 == 0 or i == 1:
                print(f"[{i}/{total}] Classifying: {artist_name}")
                sys.stdout.flush()
            
            try:
                classification = self.classify_artist(artist)
                results.append(classification)
                
                # Save progress periodically
                if i % 100 == 0:
                    print(f"  ✓ Progress: {i}/{total} ({i*100/total:.1f}%) - {len(results)} classified")
                    sys.stdout.flush()
            except Exception as e:
                print(f"Error classifying {artist_name}: {e}")
                sys.stdout.flush()
                results.append({
                    'name': artist_name,
                    'classification': 'error',
                    'error': str(e)
                })
        
        return results
    
    def test_with_seed_artists(self, seed_path: str = "config/seed_artists.json",
                               raw_data_path: str = "data/raw/artists.json") -> List[Dict]:
        """Test classification with seed artists"""
        print("=" * 60)
        print("TESTING BAND CLASSIFICATION WITH SEED ARTISTS")
        print("=" * 60)
        
        # Load seed artists
        with open(seed_path, 'r', encoding='utf-8') as f:
            seed_data = json.load(f)
        seed_names = seed_data.get('seed_artists', [])
        
        # Load raw artist data
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            raw_artists = json.load(f)
        
        # Create mapping
        artist_map = {artist.get('title', ''): artist for artist in raw_artists}
        
        # Classify seed artists
        results = []
        for seed_name in seed_names:
            artist_data = artist_map.get(seed_name)
            if not artist_data:
                print(f"Warning: {seed_name} not found in raw data")
                continue
            
            print(f"\nClassifying: {seed_name}")
            classification = self.classify_artist(artist_data)
            results.append(classification)
            
            print(f"  Classification: {classification['classification']} (confidence: {classification['confidence']:.2f})")
            print(f"  Band score: {classification['band_score']}, Solo score: {classification['solo_score']}")
            print(f"  Categories found: {len(classification['categories'])}")
            if classification['indicators']:
                print(f"  Key indicators: {', '.join(classification['indicators'][:3])}")
        
        return results
    
    def generate_statistics(self, classifications: List[Dict]) -> Dict:
        """Generate statistics from classifications"""
        stats = {
            'total': len(classifications),
            'bands': sum(1 for c in classifications if c.get('classification') == 'band'),
            'solo': sum(1 for c in classifications if c.get('classification') == 'solo'),
            'unknown': sum(1 for c in classifications if c.get('classification') == 'unknown'),
            'filtered': sum(1 for c in classifications if c.get('classification') == 'filtered'),
            'errors': sum(1 for c in classifications if c.get('classification') == 'error'),
            'avg_confidence': 0.0,
            'band_examples': [],
            'solo_examples': []
        }
        
        # Calculate average confidence
        confidences = [c.get('confidence', 0) for c in classifications if c.get('confidence')]
        if confidences:
            stats['avg_confidence'] = sum(confidences) / len(confidences)
        
        # Get examples
        bands = [c for c in classifications if c.get('classification') == 'band']
        bands.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        stats['band_examples'] = [b['name'] for b in bands[:5]]
        
        solos = [c for c in classifications if c.get('classification') == 'solo']
        solos.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        stats['solo_examples'] = [s['name'] for s in solos[:5]]
        
        return stats


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Classify artists as bands or solo artists')
    parser.add_argument('--input', '-i', default='data/processed/parsed_artists.json',
                       help='Input JSON file with artist data')
    parser.add_argument('--raw-input', '-r', default='data/raw/artists.json',
                       help='Raw input JSON file (for testing with seed artists)')
    parser.add_argument('--output', '-o', default='data/processed/band_classifications.json',
                       help='Output JSON file for classifications')
    parser.add_argument('--test-seed', action='store_true',
                       help='Test with seed artists')
    parser.add_argument('--test-sample', type=int, metavar='N',
                       help='Test with first N artists only')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        classifier = BandClassifier()
    except Exception as e:
        print(f"Error initializing classifier: {e}")
        print("Please ensure dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    
    if args.test_seed:
        # Test with seed artists
        results = classifier.test_with_seed_artists(raw_data_path=args.raw_input)
        
        # Save results
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Print statistics
        stats = classifier.generate_statistics(results)
        print("\n" + "=" * 60)
        print("CLASSIFICATION STATISTICS")
        print("=" * 60)
        print(f"Total artists: {stats['total']}")
        print(f"Bands: {stats['bands']} ({stats['bands']/stats['total']*100:.1f}%)")
        print(f"Solo artists: {stats['solo']} ({stats['solo']/stats['total']*100:.1f}%)")
        print(f"Unknown: {stats['unknown']} ({stats['unknown']/stats['total']*100:.1f}%)")
        if stats.get('filtered', 0) > 0:
            print(f"Filtered (songs/albums): {stats['filtered']} ({stats['filtered']/stats['total']*100:.1f}%)")
        print(f"Average confidence: {stats['avg_confidence']:.2f}")
        print(f"\nBand examples: {', '.join(stats['band_examples'])}")
        print(f"Solo examples: {', '.join(stats['solo_examples'])}")
    else:
        # Classify all artists
        print(f"Loading artists from {args.input}...")
        sys.stdout.flush()
        with open(args.input, 'r', encoding='utf-8') as f:
            artists = json.load(f)
        print(f"✓ Loaded {len(artists)} parsed artists")
        sys.stdout.flush()
        
        # Need to load raw data for infobox and text
        print(f"Loading raw data from {args.raw_input}...")
        sys.stdout.flush()
        with open(args.raw_input, 'r', encoding='utf-8') as f:
            raw_artists = json.load(f)
        print(f"✓ Loaded {len(raw_artists)} raw artists")
        sys.stdout.flush()
        
        # Create mapping
        print("Creating artist mapping...")
        sys.stdout.flush()
        raw_map = {artist.get('title', ''): artist for artist in raw_artists}
        
        # Merge data
        print("Merging data...")
        sys.stdout.flush()
        merged_artists = []
        for i, artist in enumerate(artists, 1):
            name = artist.get('name', '')
            raw_data = raw_map.get(name, {})
            merged = {
                'title': name,
                'name': name,
                'infobox': raw_data.get('infobox', ''),
                'text': raw_data.get('text', ''),
                'summary': raw_data.get('summary', ''),
                **artist
            }
            merged_artists.append(merged)
            if i % 500 == 0:
                print(f"  Merged {i}/{len(artists)} artists...")
                sys.stdout.flush()
        
        # Limit to sample if requested
        if args.test_sample:
            merged_artists = merged_artists[:args.test_sample]
            print(f"Limiting to first {args.test_sample} artists for testing...")
            sys.stdout.flush()
        
        print(f"\nStarting classification of {len(merged_artists)} artists...")
        print("This will take approximately 15-20 minutes with rate limiting.")
        print("=" * 60)
        sys.stdout.flush()
        results = classifier.classify_artists(merged_artists, verbose=args.verbose)
        
        # Save results
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Print statistics
        stats = classifier.generate_statistics(results)
        print("\n" + "=" * 60)
        print("CLASSIFICATION STATISTICS")
        print("=" * 60)
        print(f"Total artists: {stats['total']}")
        print(f"Bands: {stats['bands']} ({stats['bands']/stats['total']*100:.1f}%)")
        print(f"Solo artists: {stats['solo']} ({stats['solo']/stats['total']*100:.1f}%)")
        print(f"Unknown: {stats['unknown']} ({stats['unknown']/stats['total']*100:.1f}%)")
        print(f"Filtered (songs/albums): {stats['filtered']} ({stats['filtered']/stats['total']*100:.1f}%)")
        print(f"Errors: {stats['errors']}")
        print(f"Average confidence: {stats['avg_confidence']:.2f}")
        print(f"\nTop band examples: {', '.join(stats['band_examples'])}")
        print(f"Top solo examples: {', '.join(stats['solo_examples'])}")
        
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()


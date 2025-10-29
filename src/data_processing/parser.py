"""Parser for Wikipedia infobox data"""

import json
import re
from typing import Dict, List, Optional, Any
import mwparserfromhell
from data_collection.utils import logger, clean_text


class InfoboxParser:
    """Parse Wikipedia infobox templates to extract structured data"""
    
    def __init__(self):
        self.genre_patterns = [
            'thể loại', 'genre', 'loại nhạc', 'thể_loại'
        ]
        self.instrument_patterns = [
            'nhạc cụ', 'instruments', 'instrument', 'nhạc_cụ'
        ]
        self.years_patterns = [
            'năm hoạt động', 'years active', 'years_active', 'năm_hoạt_động'
        ]
        self.album_patterns = [
            'album', 'albums', 'discography', 'đĩa nhạc'
        ]
    
    def parse_infobox(self, infobox_text: str) -> Dict[str, Any]:
        """Parse infobox wikitext and extract fields"""
        if not infobox_text:
            return {}
        
        try:
            wikicode = mwparserfromhell.parse(infobox_text)
            templates = wikicode.filter_templates()
            
            if not templates:
                return {}
            
            template = templates[0]
            data = {
                'genres': [],
                'instruments': [],
                'active_years': '',
                'albums': []
            }
            
            for param in template.params:
                param_name = str(param.name).strip().lower()
                param_value = str(param.value).strip()
                
                # Extract genres
                if any(pattern in param_name for pattern in self.genre_patterns):
                    data['genres'] = self._parse_list_field(param_value)
                
                # Extract instruments
                elif any(pattern in param_name for pattern in self.instrument_patterns):
                    data['instruments'] = self._parse_list_field(param_value)
                
                # Extract active years
                elif any(pattern in param_name for pattern in self.years_patterns):
                    data['active_years'] = clean_text(param_value)
                
                # Extract albums (simplified - just names)
                elif any(pattern in param_name for pattern in self.album_patterns):
                    albums = self._parse_list_field(param_value)
                    data['albums'] = [{'title': album} for album in albums]
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing infobox: {e}")
            return {}
    
    def _parse_list_field(self, field_value: str) -> List[str]:
        """Parse a field that contains a list of values"""
        if not field_value:
            return []
        
        # Remove wiki markup
        field_value = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', field_value)
        field_value = re.sub(r"'''?([^']+)'''?", r'\1', field_value)
        field_value = re.sub(r'<[^>]+>', '', field_value)
        
        # Split by common separators
        items = re.split(r'[,;\n•]|<br\s*/?>|\{\{[^\}]+\}\}', field_value)
        
        # Clean and filter items
        cleaned_items = []
        for item in items:
            item = clean_text(item)
            if item and len(item) > 1 and len(item) < 100:
                cleaned_items.append(item)
        
        return cleaned_items[:10]  # Limit to 10 items
    
    def parse_artist(self, artist_data: Dict) -> Dict[str, Any]:
        """Parse a single artist's data"""
        infobox_text = artist_data.get('infobox', '')
        parsed_infobox = self.parse_infobox(infobox_text)
        
        # Get albums from raw data if available, otherwise from infobox
        raw_albums = artist_data.get('albums', [])
        infobox_albums = parsed_infobox.get('albums', [])
        
        # Combine albums from both sources
        all_albums = []
        album_titles = set()
        
        # Add albums from raw data (already extracted by scraper)
        for album in raw_albums:
            if isinstance(album, str):
                album_title = album.strip()
            elif isinstance(album, dict):
                album_title = album.get('title', '').strip()
            else:
                continue
                
            if album_title and album_title.lower() not in album_titles:
                album_titles.add(album_title.lower())
                all_albums.append({'title': album_title})
        
        # Add albums from infobox
        for album in infobox_albums:
            if isinstance(album, dict):
                album_title = album.get('title', '').strip()
            elif isinstance(album, str):
                album_title = album.strip()
            else:
                continue
                
            if album_title and album_title.lower() not in album_titles:
                album_titles.add(album_title.lower())
                all_albums.append({'title': album_title})
        
        return {
            'name': artist_data.get('title', ''),
            'url': artist_data.get('url', ''),
            'summary': artist_data.get('summary', ''),
            'genres': parsed_infobox.get('genres', []),
            'instruments': parsed_infobox.get('instruments', []),
            'active_years': parsed_infobox.get('active_years', ''),
            'albums': all_albums
        }
    
    def parse_all(self, input_path: str = "data/raw/artists.json") -> List[Dict]:
        """Parse all artists from raw data file"""
        logger.info(f"Parsing artists from {input_path}...")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                artists = json.load(f)
            
            parsed_artists = []
            for i, artist in enumerate(artists, 1):
                try:
                    parsed = self.parse_artist(artist)
                    parsed_artists.append(parsed)
                    
                    if i % 100 == 0:
                        logger.info(f"Parsed {i}/{len(artists)} artists")
                        
                except Exception as e:
                    logger.error(f"Error parsing artist {artist.get('title', 'unknown')}: {e}")
            
            logger.info(f"Successfully parsed {len(parsed_artists)} artists")
            return parsed_artists
            
        except Exception as e:
            logger.error(f"Error loading artists from {input_path}: {e}")
            return []


def parse_all(input_path: str = "data/raw/artists.json", 
              output_path: str = "data/processed/parsed_artists.json") -> int:
    """Main function to parse all artist data"""
    import os
    
    parser = InfoboxParser()
    parsed_artists = parser.parse_all(input_path)
    
    # Save parsed data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_artists, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved parsed data to {output_path}")
    return len(parsed_artists)


if __name__ == "__main__":
    parse_all()



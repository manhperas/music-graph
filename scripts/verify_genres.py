#!/usr/bin/env python3
"""
Verify Genre nodes and HAS_GENRE relationships in Neo4j
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from neo4j import GraphDatabase
import json
import os

# Load config
with open('config/neo4j_config.json', 'r') as f:
    config = json.load(f)

password = os.getenv('NEO4J_PASS', 'password')
driver = GraphDatabase.driver(config['uri'], auth=(config['user'], password))

print("=" * 60)
print("VERIFICATION - Genre Nodes & HAS_GENRE Relationships")
print("=" * 60)

with driver.session(database=config.get('database', 'neo4j')) as session:
    # Count Genre nodes
    result = session.run("MATCH (g:Genre) RETURN count(g) AS count")
    genre_count = result.single()['count']
    print(f"\n✅ Genre nodes: {genre_count}")
    
    # Count HAS_GENRE relationships
    result = session.run("MATCH ()-[r:HAS_GENRE]->() RETURN count(r) AS count")
    has_genre_count = result.single()['count']
    print(f"✅ HAS_GENRE relationships: {has_genre_count}")
    
    # Count Artist → Genre
    result = session.run("MATCH (a:Artist)-[:HAS_GENRE]->(g:Genre) RETURN count(*) AS count")
    artist_genre_count = result.single()['count']
    print(f"   - Artist → Genre: {artist_genre_count}")
    
    # Count Album → Genre
    result = session.run("MATCH (a:Album)-[:HAS_GENRE]->(g:Genre) RETURN count(*) AS count")
    album_genre_count = result.single()['count']
    print(f"   - Album → Genre: {album_genre_count}")
    
    # Top genres
    print("\n📊 Top 10 Genres:")
    result = session.run("""
        MATCH (a:Artist)-[:HAS_GENRE]->(g:Genre)
        RETURN g.name AS genre, count(DISTINCT a) AS artist_count
        ORDER BY artist_count DESC
        LIMIT 10
    """)
    for i, record in enumerate(result, 1):
        print(f"   {i}. {record['genre']}: {record['artist_count']} artists")
    
    # Sample query
    print("\n🎵 Sample: Artists with Genre 'pop':")
    result = session.run("""
        MATCH (a:Artist)-[:HAS_GENRE]->(g:Genre {name: 'pop'})
        RETURN a.name AS artist, g.name AS genre
        LIMIT 5
    """)
    for record in result:
        print(f"   - {record['artist']} → {record['genre']}")

driver.close()
print("\n" + "=" * 60)
print("✅ Verification complete!")
print("=" * 60)


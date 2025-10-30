#!/usr/bin/env python3
"""
Import data to Neo4j Local Database
Includes Genre nodes and HAS_GENRE relationships
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import json
import pandas as pd
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def import_to_neo4j_local():
    """Import data to local Neo4j"""
    try:
        from neo4j import GraphDatabase
        from dotenv import load_dotenv
    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.error("Please install: pip install neo4j python-dotenv pandas")
        return False
    
    # Load config
    config_path = "config/neo4j_config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"✓ Loaded config from {config_path}")
        logger.info(f"  URI: {config['uri']}")
        logger.info(f"  User: {config['user']}")
        logger.info(f"  Database: {config.get('database', 'neo4j')}")
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return False
    
    # Load password
    load_dotenv()
    password = os.getenv('NEO4J_PASS', 'password')
    
    # Test connection
    logger.info("Testing Neo4j connection...")
    try:
        driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], password)
        )
        
        with driver.session(database=config.get('database', 'neo4j')) as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record['test'] != 1:
                logger.error("Connection test failed")
                driver.close()
                return False
        
        logger.info("✓ Connection successful!")
        
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        logger.error("\nTroubleshooting:")
        logger.error("  1. Check if Neo4j is running:")
        logger.error("     sudo systemctl status neo4j")
        logger.error("  2. Check Neo4j Browser:")
        logger.error("     http://localhost:7474")
        logger.error("  3. Verify password in .env file or use default 'password'")
        return False
    
    # Import data
    logger.info("\n" + "=" * 60)
    logger.info("Starting import to Neo4j...")
    logger.info("=" * 60)
    
    data_dir = "data/processed"
    
    try:
        # Create constraints
        logger.info("\nCreating constraints...")
        with driver.session(database=config.get('database', 'neo4j')) as session:
            # Artist constraint
            try:
                session.run("""
                    CREATE CONSTRAINT artist_id IF NOT EXISTS
                    FOR (a:Artist) REQUIRE a.id IS UNIQUE
                """)
                logger.info("✓ Created constraint for Artist.id")
            except Exception as e:
                logger.warning(f"Artist constraint: {e}")
            
            # Album constraint
            try:
                session.run("""
                    CREATE CONSTRAINT album_id IF NOT EXISTS
                    FOR (a:Album) REQUIRE a.id IS UNIQUE
                """)
                logger.info("✓ Created constraint for Album.id")
            except Exception as e:
                logger.warning(f"Album constraint: {e}")
            
            # Genre constraint
            try:
                session.run("""
                    CREATE CONSTRAINT genre_id IF NOT EXISTS
                    FOR (g:Genre) REQUIRE g.id IS UNIQUE
                """)
                logger.info("✓ Created constraint for Genre.id")
            except Exception as e:
                logger.warning(f"Genre constraint: {e}")
        
        # Import Artists
        artists_path = os.path.join(data_dir, "artists.csv")
        if os.path.exists(artists_path):
            logger.info(f"\nImporting artists from {artists_path}...")
            df_artists = pd.read_csv(artists_path, encoding='utf-8')
            artists = df_artists.to_dict('records')
            
            with driver.session(database=config.get('database', 'neo4j')) as session:
                batch_size = 500
                for i in range(0, len(artists), batch_size):
                    batch = artists[i:i + batch_size]
                    session.run("""
                        UNWIND $artists AS artist
                        MERGE (a:Artist {id: artist.id})
                        SET a.name = artist.name,
                            a.genres = artist.genres,
                            a.instruments = artist.instruments,
                            a.active_years = artist.active_years,
                            a.url = artist.url
                    """, artists=batch)
                    logger.info(f"  Imported batch {i//batch_size + 1}: {len(batch)} artists")
            
            logger.info(f"✓ Imported {len(artists)} artists")
        
        # Import Albums
        albums_path = os.path.join(data_dir, "albums.csv")
        if os.path.exists(albums_path):
            logger.info(f"\nImporting albums from {albums_path}...")
            df_albums = pd.read_csv(albums_path, encoding='utf-8')
            albums = df_albums.to_dict('records')
            
            with driver.session(database=config.get('database', 'neo4j')) as session:
                batch_size = 500
                for i in range(0, len(albums), batch_size):
                    batch = albums[i:i + batch_size]
                    session.run("""
                        UNWIND $albums AS album
                        MERGE (a:Album {id: album.id})
                        SET a.title = album.title
                    """, albums=batch)
                    logger.info(f"  Imported batch {i//batch_size + 1}: {len(batch)} albums")
            
            logger.info(f"✓ Imported {len(albums)} albums")
        
        # Import Songs
        songs_path = os.path.join(data_dir, "songs.csv")
        if os.path.exists(songs_path):
            logger.info(f"\nImporting songs from {songs_path}...")
            df_songs = pd.read_csv(songs_path, encoding='utf-8')
            songs = df_songs.to_dict('records')
            
            with driver.session(database=config.get('database', 'neo4j')) as session:
                # Create constraint for Song.id
                try:
                    session.run("""
                        CREATE CONSTRAINT song_id IF NOT EXISTS
                        FOR (s:Song) REQUIRE s.id IS UNIQUE
                    """)
                    logger.info("✓ Created constraint for Song.id")
                except Exception as e:
                    logger.debug(f"Constraint may already exist: {e}")
                
                batch_size = 500
                for i in range(0, len(songs), batch_size):
                    batch = songs[i:i + batch_size]
                    session.run("""
                        UNWIND $songs AS song
                        MERGE (s:Song {id: 'song_' + toString(song.id)})
                        SET s.title = COALESCE(song.title, ''),
                            s.duration = COALESCE(song.duration, ''),
                            s.track_number = COALESCE(song.track_number, ''),
                            s.album_id = COALESCE(song.album_id, ''),
                            s.featured_artists = COALESCE(song.featured_artists, '')
                    """, songs=batch)
                    logger.info(f"  Imported batch {i//batch_size + 1}: {len(batch)} songs")
            
            logger.info(f"✓ Imported {len(songs)} songs")
        
        # Import Genres
        genres_path = os.path.join(data_dir, "genres.csv")
        if os.path.exists(genres_path):
            logger.info(f"\nImporting genres from {genres_path}...")
            df_genres = pd.read_csv(genres_path, encoding='utf-8')
            genres = df_genres.to_dict('records')
            
            with driver.session(database=config.get('database', 'neo4j')) as session:
                batch_size = 500
                for i in range(0, len(genres), batch_size):
                    batch = genres[i:i + batch_size]
                    session.run("""
                        UNWIND $genres AS genre
                        MERGE (g:Genre {id: genre.id})
                        SET g.name = genre.name,
                            g.normalized_name = genre.normalized_name,
                            g.count = COALESCE(toInteger(genre.count), 0)
                    """, genres=batch)
                    logger.info(f"  Imported batch {i//batch_size + 1}: {len(batch)} genres")
            
            logger.info(f"✓ Imported {len(genres)} genres")
        
        # Import Relationships
        edges_path = os.path.join(data_dir, "edges.csv")
        has_genre_path = os.path.join(data_dir, "has_genre_edges.csv")
        
        # Import regular edges
        if os.path.exists(edges_path):
            logger.info(f"\nImporting relationships from {edges_path}...")
            df_edges = pd.read_csv(edges_path, encoding='utf-8')
            
            # Filter out HAS_GENRE and AWARD_NOMINATION (will import separately)
            # Keep PART_OF in df_edges_other for processing
            df_edges_other = df_edges[(df_edges['type'] != 'HAS_GENRE') & (df_edges['type'] != 'AWARD_NOMINATION')]
            
            if not df_edges_other.empty:
                # PERFORMS_ON
                performs_on = df_edges_other[df_edges_other['type'] == 'PERFORMS_ON']
                if not performs_on.empty:
                    logger.info(f"  Importing {len(performs_on)} PERFORMS_ON relationships...")
                    with driver.session(database=config.get('database', 'neo4j')) as session:
                        batch_size = 1000
                        for i in range(0, len(performs_on), batch_size):
                            batch = performs_on.iloc[i:i + batch_size].to_dict('records')
                            session.run("""
                                UNWIND $edges AS edge
                                MATCH (from {id: edge.from})
                                MATCH (to {id: edge.to})
                                MERGE (from)-[:PERFORMS_ON]->(to)
                            """, edges=batch)
                    logger.info(f"  ✓ Imported {len(performs_on)} PERFORMS_ON relationships")
                
                # COLLABORATES_WITH
                collabs = df_edges_other[df_edges_other['type'] == 'COLLABORATES_WITH']
                if not collabs.empty:
                    logger.info(f"  Importing {len(collabs)} COLLABORATES_WITH relationships...")
                    with driver.session(database=config.get('database', 'neo4j')) as session:
                        batch_size = 1000
                        for i in range(0, len(collabs), batch_size):
                            batch = collabs.iloc[i:i + batch_size].to_dict('records')
                            session.run("""
                                UNWIND $edges AS edge
                                MATCH (from:Artist {id: edge.from})
                                MATCH (to:Artist {id: edge.to})
                                MERGE (from)-[r:COLLABORATES_WITH]->(to)
                                SET r.shared_albums = COALESCE(toInteger(edge.weight), 1)
                            """, edges=batch)
                    logger.info(f"  ✓ Imported {len(collabs)} COLLABORATES_WITH relationships")
                
                # PART_OF (Song -> Album)
                part_of = df_edges_other[df_edges_other['type'] == 'PART_OF']
                if not part_of.empty:
                    logger.info(f"  Importing {len(part_of)} PART_OF relationships...")
                    with driver.session(database=config.get('database', 'neo4j')) as session:
                        batch_size = 1000
                        for i in range(0, len(part_of), batch_size):
                            batch = part_of.iloc[i:i + batch_size]
                            
                            # Separate edges with and without track_number
                            edges_with_track = batch[batch['track_number'].notna()]
                            edges_without_track = batch[batch['track_number'].isna()]
                            
                            if not edges_with_track.empty:
                                batch_data = edges_with_track.to_dict('records')
                                session.run("""
                                    UNWIND $edges AS edge
                                    MATCH (song:Song {id: edge.to})
                                    MATCH (album:Album {id: edge.from})
                                    MERGE (song)-[r:PART_OF]->(album)
                                    SET r.track_number = edge.track_number
                                """, edges=batch_data)
                            
                            if not edges_without_track.empty:
                                batch_data = edges_without_track.to_dict('records')
                                session.run("""
                                    UNWIND $edges AS edge
                                    MATCH (song:Song {id: edge.to})
                                    MATCH (album:Album {id: edge.from})
                                    MERGE (song)-[:PART_OF]->(album)
                                """, edges=batch_data)
                            
                            logger.info(f"    Imported batch {i//batch_size + 1}: {len(batch)} PART_OF relationships")
                    logger.info(f"  ✓ Imported {len(part_of)} PART_OF relationships")
        
        # Import HAS_GENRE relationships
        if os.path.exists(has_genre_path):
            logger.info(f"\nImporting HAS_GENRE relationships from {has_genre_path}...")
            df_has_genre = pd.read_csv(has_genre_path, encoding='utf-8')
            
            with driver.session(database=config.get('database', 'neo4j')) as session:
                batch_size = 1000
                for i in range(0, len(df_has_genre), batch_size):
                    batch = df_has_genre.iloc[i:i + batch_size].to_dict('records')
                    session.run("""
                        UNWIND $edges AS edge
                        MATCH (from {id: edge.from})
                        MATCH (to:Genre {id: edge.to})
                        MERGE (from)-[:HAS_GENRE]->(to)
                    """, edges=batch)
                    logger.info(f"  Imported batch {i//batch_size + 1}: {len(batch)} relationships")
            
                logger.info(f"✓ Imported {len(df_has_genre)} HAS_GENRE relationships")
            
            # Import awards
            awards_path = os.path.join(data_dir, "awards.csv")
            if os.path.exists(awards_path):
                logger.info(f"\nImporting Awards from {awards_path}...")
                df_awards = pd.read_csv(awards_path)
                
                with driver.session(database=config.get('database', 'neo4j')) as session:
                    # Create constraint for Award.id
                    try:
                        session.run("""
                            CREATE CONSTRAINT award_id IF NOT EXISTS
                            FOR (a:Award) REQUIRE a.id IS UNIQUE
                        """)
                        logger.info("✓ Created constraint for Award.id")
                    except Exception as e:
                        logger.debug(f"Constraint may already exist: {e}")
                    
                    # Import awards in batches
                    batch_size = 100
                    for i in range(0, len(df_awards), batch_size):
                        batch = df_awards.iloc[i:i+batch_size]
                        
                        query = """
                        UNWIND $batch AS award
                        MERGE (a:Award {id: award.id})
                        SET a.name = COALESCE(award.name, ''),
                            a.ceremony = COALESCE(award.ceremony, ''),
                            a.category = COALESCE(award.category, ''),
                            a.year = CASE 
                                WHEN award.year IS NULL OR award.year = '' THEN null
                                ELSE toInteger(award.year)
                            END
                        """
                        
                        batch_data = batch.to_dict('records')
                        session.run(query, batch=batch_data)
                        logger.info(f"  Imported batch {i//batch_size + 1}: {len(batch)} awards")
                
                logger.info(f"✓ Imported {len(df_awards)} Award nodes")
            else:
                logger.warning(f"Awards file not found: {awards_path}")
            
            # Import AWARD_NOMINATION relationships from edges.csv
            edges_path = os.path.join(data_dir, "edges.csv")
            if os.path.exists(edges_path):
                logger.info(f"\nImporting AWARD_NOMINATION relationships from {edges_path}...")
                df_edges = pd.read_csv(edges_path)
                
                # Import AWARD_NOMINATION relationships separately to handle optional properties
                df_award_nominations = df_edges[df_edges['type'] == 'AWARD_NOMINATION'].copy()
                
                if not df_award_nominations.empty:
                    logger.info(f"  Found {len(df_award_nominations)} AWARD_NOMINATION relationships...")
                    
                    with driver.session(database=config.get('database', 'neo4j')) as session:
                        # Separate edges with and without status/year
                        edges_with_props = df_award_nominations[
                            df_award_nominations['status'].notna() | df_award_nominations['year'].notna()
                        ]
                        edges_without_props = df_award_nominations[
                            df_award_nominations['status'].isna() & df_award_nominations['year'].isna()
                        ]
                        
                        # Import edges with properties
                        if not edges_with_props.empty:
                            batch_size = 100
                            for i in range(0, len(edges_with_props), batch_size):
                                batch = edges_with_props.iloc[i:i+batch_size]
                                
                                query = """
                                UNWIND $batch AS edge
                                MATCH (source {id: edge.from})
                                MATCH (target {id: edge.to})
                                MERGE (source)-[r:AWARD_NOMINATION]->(target)
                                SET r.status = CASE 
                                    WHEN edge.status IS NULL OR edge.status = '' THEN null
                                    ELSE edge.status
                                END,
                                r.year = CASE 
                                    WHEN edge.year IS NULL OR edge.year = '' THEN null
                                    ELSE toInteger(edge.year)
                                END
                                """
                                
                                batch_data = batch.to_dict('records')
                                session.run(query, batch=batch_data)
                                logger.info(f"    Imported batch {i//batch_size + 1}: {len(batch)} AWARD_NOMINATION relationships")
                        
                        # Import edges without properties
                        if not edges_without_props.empty:
                            batch_size = 100
                            for i in range(0, len(edges_without_props), batch_size):
                                batch = edges_without_props.iloc[i:i+batch_size]
                                
                                query = """
                                UNWIND $batch AS edge
                                MATCH (source {id: edge.from})
                                MATCH (target {id: edge.to})
                                MERGE (source)-[r:AWARD_NOMINATION]->(target)
                                """
                                
                                batch_data = batch.to_dict('records')
                                session.run(query, batch=batch_data)
                                logger.info(f"    Imported batch {i//batch_size + 1}: {len(batch)} AWARD_NOMINATION relationships (no props)")
                    
                    logger.info(f"✓ Imported {len(df_award_nominations)} AWARD_NOMINATION relationships")
                else:
                    logger.info("  No AWARD_NOMINATION relationships found")
        
        # Verify import
        logger.info("\n" + "=" * 60)
        logger.info("Verifying import...")
        logger.info("=" * 60)
        
        with driver.session(database=config.get('database', 'neo4j')) as session:
            # Count nodes
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
                ORDER BY count DESC
            """)
            
            logger.info("\nNode counts:")
            for record in result:
                logger.info(f"  - {record['label']}: {record['count']}")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(r) AS count
                ORDER BY count DESC
            """)
            
            logger.info("\nRelationship counts:")
            for record in result:
                logger.info(f"  - {record['type']}: {record['count']}")
        
        driver.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Import completed successfully!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        driver.close()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Neo4j Local Import Script")
    print("=" * 60)
    print()
    
    success = import_to_neo4j_local()
    
    if success:
        print("\n✅ Import completed!")
        print("\nNext steps:")
        print("  1. Open Neo4j Browser: http://localhost:7474")
        print("  2. Try queries:")
        print("     MATCH (g:Genre) RETURN count(g)")
        print("     MATCH (a:Artist)-[:HAS_GENRE]->(g:Genre) RETURN a, g LIMIT 10")
    else:
        print("\n❌ Import failed. Please check errors above.")
    
    sys.exit(0 if success else 1)


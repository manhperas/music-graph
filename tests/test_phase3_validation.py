#!/usr/bin/env python3
"""
Test và Validate Phase 3: Songs + PART_OF Relationships
Task 3.7: Test và Validate
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add src directory to path
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from data_processing import parse_all, clean_all
    from graph_building import build_graph, import_to_neo4j
    from data_collection.utils import logger
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    
    # Import song extraction functions
    sys.path.insert(0, str(Path(__file__).parent / "scripts"))
    from extract_songs import extract_songs_from_albums_file, create_song_nodes_csv
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please run with: uv run python test_phase3_validation.py")
    sys.exit(1)


def check_neo4j_connection(config_path: str = "config/neo4j_config.json"):
    """Check if Neo4j local is accessible"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        uri = config.get('uri', 'bolt://localhost:7687')
        logger.info(f"Connecting to Neo4j local: {uri}")
        
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        if not password or password == 'password':
            logger.warning("⚠ Using default password 'password'. Make sure .env file has NEO4J_PASS set!")
        
        driver = GraphDatabase.driver(
            uri,
            auth=(config['user'], password)
        )
        
        # Test connection
        database = config.get('database', 'neo4j')
        logger.info(f"Testing connection to database: {database}")
        
        with driver.session(database=database) as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record['test'] == 1:
                logger.info("✓ Neo4j local connection successful")
        
        # Get Neo4j version info
        try:
            with driver.session(database=database) as session:
                result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version LIMIT 1")
                version_record = result.single()
                if version_record:
                    logger.info(f"✓ Neo4j version: {version_record['version']}")
        except:
            pass  # Version check is optional
        
        driver.close()
        return True
    except Exception as e:
        logger.error(f"✗ Neo4j local connection failed: {e}")
        logger.error("")
        logger.error("Troubleshooting for Neo4j Local:")
        logger.error("  1. Check Neo4j is running:")
        logger.error("     - Local service: sudo systemctl status neo4j")
        logger.error("     - Neo4j Desktop: Check app is running")
        logger.error("  2. Check Neo4j Browser: http://localhost:7474")
        logger.error("  3. Verify password in .env file:")
        logger.error("     - Create .env file if not exists")
        logger.error("     - Add: NEO4J_PASS=your_password")
        logger.error("  4. Check config/neo4j_config.json:")
        logger.error("     - URI should be: bolt://localhost:7687")
        logger.error("     - User should be: neo4j")
        logger.error("     - Database should be: neo4j")
        logger.error("")
        logger.error("Quick test:")
        logger.error("  uv run python check_neo4j_local.py")
        return False


def step1_extract_songs():
    """Step 1: Extract songs from album pages
    
    NOTE: Không cần scrape lại raw data từ Wikipedia!
    Chỉ extract songs từ albums.json đã có sẵn.
    Nếu songs.json đã tồn tại thì sẽ skip extraction.
    """
    logger.info("=" * 60)
    logger.info("STEP 1: EXTRACT SONGS FROM ALBUM PAGES")
    logger.info("=" * 60)
    logger.info("⚠  NOTE: Không scrape lại raw data!")
    logger.info("    Chỉ extract songs từ albums.json đã có sẵn.")
    logger.info("")
    
    try:
        songs_json_path = "data/processed/songs.json"
        albums_json_path = "data/processed/albums.json"
        
        # Check if songs.json already exists
        if os.path.exists(songs_json_path):
            logger.info(f"✓ Found existing songs.json: {songs_json_path}")
            logger.info("  → Sẽ SKIP extraction (dùng file hiện có)")
            with open(songs_json_path, 'r', encoding='utf-8') as f:
                songs_data = json.load(f)
            logger.info(f"  Contains songs from {len(songs_data)} albums")
            total_songs = sum(len(songs) for songs in songs_data.values())
            logger.info(f"  Total songs: {total_songs}")
            
            # Check if we need to re-extract
            if total_songs == 0:
                logger.warning("  songs.json exists but has no songs. Re-extracting...")
                logger.info("  (Chỉ extract từ albums.json, không scrape lại Wikipedia)")
                if os.path.exists(albums_json_path):
                    logger.info("Extracting songs from albums...")
                    extract_songs_from_albums_file(
                        albums_file=albums_json_path,
                        output_file=songs_json_path,
                        max_albums=None,  # Extract all albums
                        skip_existing=True  # Skip albums đã có songs để tăng tốc độ
                    )
                else:
                    logger.error(f"✗ albums.json not found: {albums_json_path}")
                    return False
            else:
                logger.info("  ✓ Songs data ready, skipping extraction")
        else:
            # Extract songs from albums
            logger.info("songs.json not found. Extracting songs from albums...")
            logger.info("  (Chỉ extract từ albums.json, không scrape lại Wikipedia)")
            if not os.path.exists(albums_json_path):
                logger.error(f"✗ albums.json not found: {albums_json_path}")
                logger.error("")
                logger.error("Please run data processing first:")
                logger.error("  uv run python src/main.py process")
                logger.error("")
                logger.error("This will create albums.json from existing parsed data.")
                logger.error("(Không cần scrape lại raw data từ Wikipedia)")
                return False
            
            extract_songs_from_albums_file(
                albums_file=albums_json_path,
                output_file=songs_json_path,
                max_albums=None,  # Extract all albums
                skip_existing=True  # Skip albums đã có songs để tăng tốc độ
            )
        
        # Verify songs.json was created/updated
        if os.path.exists(songs_json_path):
            with open(songs_json_path, 'r', encoding='utf-8') as f:
                songs_data = json.load(f)
            
            albums_with_songs = len([a for a, songs in songs_data.items() if songs])
            total_songs = sum(len(songs) for songs in songs_data.values())
            
            logger.info(f"✓ Songs extraction completed:")
            logger.info(f"  - Albums with songs: {albums_with_songs}")
            logger.info(f"  - Total songs extracted: {total_songs}")
            
            if total_songs == 0:
                logger.warning("✗ No songs extracted. Check album pages on Wikipedia.")
                return False
            
            return True
        else:
            logger.error("✗ songs.json was not created")
            return False
            
    except Exception as e:
        logger.error(f"✗ Song extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step2_create_songs_csv():
    """Step 2: Create songs.csv from songs.json"""
    logger.info("=" * 60)
    logger.info("STEP 2: CREATE SONGS.CSV FROM SONGS.JSON")
    logger.info("=" * 60)
    
    try:
        songs_json_path = "data/processed/songs.json"
        albums_json_path = "data/processed/albums.json"
        songs_csv_path = "data/processed/songs.csv"
        
        if not os.path.exists(songs_json_path):
            logger.error(f"✗ songs.json not found: {songs_json_path}")
            logger.error("Run Step 1 first: Extract songs")
            return False
        
        if not os.path.exists(albums_json_path):
            logger.error(f"✗ albums.json not found: {albums_json_path}")
            return False
        
        # Create songs.csv
        logger.info("Creating songs.csv from songs.json...")
        df_songs = create_song_nodes_csv(
            songs_file=songs_json_path,
            albums_file=albums_json_path,
            output_file=songs_csv_path
        )
        
        if df_songs.empty:
            logger.error("✗ songs.csv is empty")
            return False
        
        logger.info(f"✓ Created songs.csv with {len(df_songs)} song nodes")
        
        # Verify columns
        required_columns = ['id', 'title', 'album_id']
        missing_columns = [col for col in required_columns if col not in df_songs.columns]
        if missing_columns:
            logger.error(f"✗ Missing required columns: {missing_columns}")
            return False
        
        # Statistics
        songs_with_album = df_songs['album_id'].notna().sum()
        songs_with_duration = df_songs['duration'].astype(str).str.len().gt(0).sum()
        songs_with_track_number = df_songs['track_number'].astype(str).str.len().gt(0).sum()
        songs_with_featured = df_songs['featured_artists'].astype(str).str.len().gt(0).sum()
        
        logger.info(f"  - Songs with album_id: {songs_with_album}/{len(df_songs)}")
        logger.info(f"  - Songs with duration: {songs_with_duration}/{len(df_songs)}")
        logger.info(f"  - Songs with track_number: {songs_with_track_number}/{len(df_songs)}")
        logger.info(f"  - Songs with featured artists: {songs_with_featured}/{len(df_songs)}")
        
        if songs_with_album == 0:
            logger.warning("✗ No songs have album_id! Songs won't be linked to albums.")
            return False
        
        # Show sample songs
        logger.info("\n  Sample songs:")
        sample_songs = df_songs.head(5)
        for idx, row in sample_songs.iterrows():
            logger.info(f"    • {row['title']} (album_id: {row['album_id']})")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Creating songs.csv failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step3_build_graph():
    """Step 3: Build graph and verify Song nodes"""
    logger.info("=" * 60)
    logger.info("STEP 3: BUILD GRAPH AND VERIFY SONG NODES")
    logger.info("=" * 60)
    
    try:
        songs_csv_path = "data/processed/songs.csv"
        
        if not os.path.exists(songs_csv_path):
            logger.error(f"✗ songs.csv not found: {songs_csv_path}")
            logger.error("Run Step 2 first: Create songs.csv")
            return False
        
        # Check if genre files exist
        genres_path = "data/migrations/genres.csv" if os.path.exists("data/migrations/genres.csv") else None
        has_genre_path = "data/migrations/has_genre_relationships.csv" if os.path.exists("data/migrations/has_genre_relationships.csv") else None
        band_classifications_path = "data/processed/band_classifications.json" if os.path.exists("data/processed/band_classifications.json") else None
        
        logger.info(f"✓ Found songs.csv: {songs_csv_path}")
        if genres_path:
            logger.info(f"✓ Found genres file: {genres_path}")
        if has_genre_path:
            logger.info(f"✓ Found HAS_GENRE relationships: {has_genre_path}")
        if band_classifications_path:
            logger.info(f"✓ Found band classifications: {band_classifications_path}")
        
        # Build graph with songs
        node_count = build_graph(
            nodes_path="data/processed/nodes.csv",
            albums_path="data/processed/albums.json",
            output_dir="data/processed",
            genres_path=genres_path,
            has_genre_path=has_genre_path,
            band_classifications_path=band_classifications_path,
            songs_path=songs_csv_path
        )
        logger.info(f"✓ Built graph with {node_count} nodes")
        
        # Verify songs.csv was exported
        exported_songs_path = "data/processed/songs.csv"
        if os.path.exists(exported_songs_path):
            df_songs = pd.read_csv(exported_songs_path)
            logger.info(f"✓ Song nodes CSV verified: {len(df_songs)} songs")
        else:
            logger.warning("✗ songs.csv not found in output directory")
            return False
        
        # Verify edges.csv contains PART_OF and PERFORMS_ON (Artist → Song) edges
        edges_path = "data/processed/edges.csv"
        if os.path.exists(edges_path):
            df_edges = pd.read_csv(edges_path)
            
            # Check PART_OF edges
            part_of_count = len(df_edges[df_edges['type'] == 'PART_OF'])
            logger.info(f"✓ Found {part_of_count} PART_OF edges (Song → Album)")
            
            if part_of_count == 0:
                logger.warning("✗ No PART_OF edges found")
                return False
            
            # Check PERFORMS_ON edges (Artist → Song)
            # We need to check if edges are from Artist/Band to Song
            # Load graph to verify node types
            import networkx as nx
            graph_path = "data/processed/network.graphml"
            if os.path.exists(graph_path):
                graph = nx.read_graphml(graph_path)
                
                # Count Song nodes
                song_nodes = [n for n in graph.nodes() if graph.nodes[n].get('node_type') == 'Song']
                logger.info(f"✓ Found {len(song_nodes)} Song nodes in graph")
                
                if len(song_nodes) == 0:
                    logger.warning("✗ No Song nodes found in graph")
                    return False
                
                # Count PERFORMS_ON edges from Artist/Band to Song
                performs_on_to_song = 0
                for u, v, data in graph.edges(data=True):
                    if data.get('relationship') == 'PERFORMS_ON':
                        u_type = graph.nodes[u].get('node_type', '')
                        v_type = graph.nodes[v].get('node_type', '')
                        if (u_type in ['Artist', 'Band']) and (v_type == 'Song'):
                            performs_on_to_song += 1
                
                logger.info(f"✓ Found {performs_on_to_song} PERFORMS_ON edges (Artist/Band → Song)")
                
                if performs_on_to_song == 0:
                    logger.warning("✗ No PERFORMS_ON edges from Artist/Band to Song found")
                    return False
                
            else:
                logger.warning("✗ network.graphml not found")
                return False
            
            # Show sample edges
            logger.info("\n  Sample PART_OF edges:")
            sample_part_of = df_edges[df_edges['type'] == 'PART_OF'].head(3)
            for idx, row in sample_part_of.iterrows():
                logger.info(f"    {row['from']} -> {row['to']}")
            
        else:
            logger.warning("✗ edges.csv not found")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Graph building failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step4_check_success_criteria():
    """Step 4: Check success criteria: ≥40% albums have songs"""
    logger.info("=" * 60)
    logger.info("STEP 4: CHECK SUCCESS CRITERIA (≥40% ALBUMS HAVE SONGS)")
    logger.info("=" * 60)
    
    try:
        songs_csv_path = "data/processed/songs.csv"
        albums_json_path = "data/processed/albums.json"
        
        if not os.path.exists(songs_csv_path):
            logger.error(f"✗ songs.csv not found: {songs_csv_path}")
            return False
        
        if not os.path.exists(albums_json_path):
            logger.error(f"✗ albums.json not found: {albums_json_path}")
            return False
        
        # Load songs
        df_songs = pd.read_csv(songs_csv_path)
        
        # Load albums
        with open(albums_json_path, 'r', encoding='utf-8') as f:
            albums_data = json.load(f)
        
        # Count albums with 2+ artists (these are the ones that get album nodes)
        albums_with_nodes = {}
        album_idx = 0
        for album_name in sorted(albums_data.keys()):
            artist_ids = albums_data[album_name]
            if len(artist_ids) >= 2:
                albums_with_nodes[album_name] = f"album_{album_idx}"
                album_idx += 1
        
        total_albums = len(albums_with_nodes)
        logger.info(f"Total albums (with 2+ artists): {total_albums}")
        
        # Count albums with songs
        songs_with_album = df_songs[df_songs['album_id'].notna()]
        unique_album_ids = set(songs_with_album['album_id'].unique())
        albums_with_songs = len([aid for aid in unique_album_ids if aid])
        
        logger.info(f"Albums with songs: {albums_with_songs}")
        
        if total_albums > 0:
            percentage = (albums_with_songs / total_albums) * 100
            logger.info(f"Percentage: {percentage:.2f}%")
            
            success_threshold = 40.0
            if percentage >= success_threshold:
                logger.info(f"✓ SUCCESS CRITERIA MET: {percentage:.2f}% >= {success_threshold}%")
                return True
            else:
                logger.warning(f"✗ SUCCESS CRITERIA NOT MET: {percentage:.2f}% < {success_threshold}%")
                logger.warning("  Need to extract songs from more albums")
                return False
        else:
            logger.warning("✗ No albums found")
            return False
        
    except Exception as e:
        logger.error(f"✗ Checking success criteria failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step5_test_neo4j_import():
    """Step 5: Test Neo4j local import"""
    logger.info("=" * 60)
    logger.info("STEP 5: TEST NEO4J LOCAL IMPORT")
    logger.info("=" * 60)
    
    logger.info("Checking Neo4j local connection...")
    if not check_neo4j_connection():
        logger.error("✗ Cannot connect to Neo4j local")
        logger.error("Please fix connection issues before proceeding")
        logger.error("")
        logger.error("Run this to test connection:")
        logger.error("  uv run python check_neo4j_local.py")
        return False
    
    # Check config for local setup
    try:
        with open("config/neo4j_config.json", 'r') as f:
            config = json.load(f)
        
        uri = config.get('uri', '')
        if 'localhost' not in uri and '127.0.0.1' not in uri:
            logger.warning(f"⚠ URI doesn't look like local: {uri}")
            logger.warning("  For Neo4j local, URI should be: bolt://localhost:7687")
        
        logger.info(f"Using Neo4j local:")
        logger.info(f"  URI: {uri}")
        logger.info(f"  Database: {config.get('database', 'neo4j')}")
        logger.info(f"  User: {config.get('user', 'neo4j')}")
    except Exception as e:
        logger.warning(f"Could not read config: {e}")
    
    try:
        config_path = "config/neo4j_config.json"
        logger.info("")
        logger.info("Starting import to Neo4j local...")
        logger.info("⚠ This will CLEAR the database first!")
        logger.info("")
        
        import_to_neo4j(
            data_dir="data/processed",
            config_path=config_path,
            clear_first=True  # Clear database for clean test
        )
        logger.info("")
        logger.info("✓ Neo4j local import completed successfully")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Open Neo4j Browser: http://localhost:7474")
        logger.info("  2. Login with your credentials")
        logger.info("  3. Run Cypher queries to explore the data")
        return True
        
    except Exception as e:
        logger.error(f"✗ Neo4j local import failed: {e}")
        logger.error("")
        logger.error("Common issues:")
        logger.error("  1. Neo4j local not running")
        logger.error("  2. Wrong password in .env file")
        logger.error("  3. Database locked or in use")
        logger.error("  4. Insufficient memory")
        logger.error("")
        logger.error("Check connection:")
        logger.error("  uv run python check_neo4j_local.py")
        import traceback
        traceback.print_exc()
        return False


def step6_verify_with_cypher():
    """Step 6: Run Cypher queries to verify data in Neo4j local"""
    logger.info("=" * 60)
    logger.info("STEP 6: VERIFY DATA WITH CYPHER QUERIES (Neo4j Local)")
    logger.info("=" * 60)
    
    logger.info("Connecting to Neo4j local...")
    if not check_neo4j_connection():
        logger.error("✗ Cannot connect to Neo4j local")
        logger.error("Skipping Cypher verification")
        return False
    
    try:
        with open("config/neo4j_config.json", 'r') as f:
            config = json.load(f)
        
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        uri = config.get('uri', 'bolt://localhost:7687')
        database = config.get('database', 'neo4j')
        
        logger.info(f"Querying Neo4j local: {uri} (database: {database})")
        
        driver = GraphDatabase.driver(
            uri,
            auth=(config['user'], password)
        )
        
        with driver.session(database=database) as session:
            # Query 1: Count Song nodes
            logger.info("\nQuery 1: Count Song nodes")
            result = session.run("""
                MATCH (s:Song)
                RETURN count(s) AS count
            """)
            record = result.single()
            song_count = record['count']
            logger.info(f"  ✓ Found {song_count} Song nodes")
            
            if song_count == 0:
                logger.warning("✗ No Song nodes found!")
                driver.close()
                return False
            
            # Query 2: Count PART_OF relationships
            logger.info("\nQuery 2: Count PART_OF relationships (Song → Album)")
            result = session.run("""
                MATCH ()-[r:PART_OF]->()
                RETURN count(r) AS count
            """)
            record = result.single()
            part_of_count = record['count']
            logger.info(f"  ✓ Found {part_of_count} PART_OF relationships")
            
            if part_of_count == 0:
                logger.warning("✗ No PART_OF relationships found!")
                driver.close()
                return False
            
            # Query 3: Count PERFORMS_ON relationships (Artist → Song)
            logger.info("\nQuery 3: Count PERFORMS_ON relationships (Artist → Song)")
            result = session.run("""
                MATCH (a:Artist)-[:PERFORMS_ON]->(s:Song)
                RETURN count(*) AS count
            """)
            record = result.single()
            performs_on_song_count = record['count']
            logger.info(f"  ✓ Found {performs_on_song_count} PERFORMS_ON relationships (Artist → Song)")
            
            if performs_on_song_count == 0:
                logger.warning("✗ No PERFORMS_ON relationships (Artist → Song) found!")
                driver.close()
                return False
            
            # Query 4: Sample Song nodes
            logger.info("\nQuery 4: Sample Song nodes")
            result = session.run("""
                MATCH (s:Song)
                RETURN s.id AS id, s.title AS title, s.album_id AS album_id
                LIMIT 10
            """)
            songs = [record.values() for record in result]
            for song_id, title, album_id in songs:
                logger.info(f"  • {title} (id: {song_id}, album: {album_id})")
            
            # Query 5: Songs with track numbers
            logger.info("\nQuery 5: Songs with track numbers")
            result = session.run("""
                MATCH (s:Song)
                WHERE s.track_number IS NOT NULL AND s.track_number <> ''
                RETURN count(s) AS count
            """)
            record = result.single()
            songs_with_track = record['count']
            logger.info(f"  ✓ Found {songs_with_track} songs with track numbers")
            
            # Query 6: Albums with most songs
            logger.info("\nQuery 6: Albums with most songs (top 10)")
            result = session.run("""
                MATCH (s:Song)-[:PART_OF]->(a:Album)
                RETURN a.title AS album, count(s) AS song_count
                ORDER BY song_count DESC
                LIMIT 10
            """)
            for record in result:
                logger.info(f"  • {record['album']}: {record['song_count']} songs")
            
            # Query 7: Artists with most songs
            logger.info("\nQuery 7: Artists with most songs (top 10)")
            result = session.run("""
                MATCH (a:Artist)-[:PERFORMS_ON]->(s:Song)
                RETURN a.name AS artist, count(s) AS song_count
                ORDER BY song_count DESC
                LIMIT 10
            """)
            for record in result:
                logger.info(f"  • {record['artist']}: {record['song_count']} songs")
            
            # Query 8: Songs with featured artists
            logger.info("\nQuery 8: Songs with featured artists")
            result = session.run("""
                MATCH (s:Song)
                WHERE s.featured_artists IS NOT NULL AND s.featured_artists <> ''
                RETURN count(s) AS count
            """)
            record = result.single()
            songs_with_featured = record['count']
            logger.info(f"  ✓ Found {songs_with_featured} songs with featured artists")
            
            # Query 9: Percentage of albums with songs
            logger.info("\nQuery 9: Percentage of albums with songs")
            result = session.run("""
                MATCH (a:Album)
                OPTIONAL MATCH (s:Song)-[:PART_OF]->(a)
                WITH a, count(s) AS song_count
                RETURN 
                    count(a) AS total_albums,
                    sum(CASE WHEN song_count > 0 THEN 1 ELSE 0 END) AS albums_with_songs,
                    toFloat(sum(CASE WHEN song_count > 0 THEN 1 ELSE 0 END)) / count(a) * 100 AS percentage
            """)
            record = result.single()
            total_albums = record['total_albums']
            albums_with_songs = record['albums_with_songs']
            percentage = record['percentage']
            logger.info(f"  Total albums: {total_albums}")
            logger.info(f"  Albums with songs: {albums_with_songs}")
            logger.info(f"  Percentage: {percentage:.2f}%")
            
            if percentage >= 40.0:
                logger.info(f"  ✓ SUCCESS CRITERIA MET: {percentage:.2f}% >= 40%")
            else:
                logger.warning(f"  ✗ SUCCESS CRITERIA NOT MET: {percentage:.2f}% < 40%")
            
            # Query 10: Sample PART_OF relationships
            logger.info("\nQuery 10: Sample PART_OF relationships")
            result = session.run("""
                MATCH (s:Song)-[r:PART_OF]->(a:Album)
                RETURN s.title AS song, a.title AS album, r.track_number AS track_number
                LIMIT 10
            """)
            for record in result:
                track_info = f" (track {record['track_number']})" if record['track_number'] else ""
                logger.info(f"  • {record['song']} -> {record['album']}{track_info}")
            
            # Query 11: Sample PERFORMS_ON relationships (Artist → Song)
            logger.info("\nQuery 11: Sample PERFORMS_ON relationships (Artist → Song)")
            result = session.run("""
                MATCH (a:Artist)-[:PERFORMS_ON]->(s:Song)
                RETURN a.name AS artist, s.title AS song
                LIMIT 10
            """)
            for record in result:
                logger.info(f"  • {record['artist']} -> {record['song']}")
        
        driver.close()
        logger.info("\n✓ All Cypher queries executed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Cypher verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation steps
    
    NOTE: Script này KHÔNG scrape lại raw data từ Wikipedia!
    Chỉ làm việc với data đã processed:
    - albums.json (đã có sẵn)
    - nodes.csv (đã có sẵn)
    - songs.json (sẽ extract nếu chưa có, từ albums.json)
    
    Nếu cần scrape lại raw data, chạy riêng:
      uv run python src/main.py collect
    """
    logger.info("=" * 60)
    logger.info("PHASE 3 VALIDATION: SONGS + PART_OF RELATIONSHIPS")
    logger.info("Task 3.7: Test và Validate")
    logger.info("=" * 60)
    logger.info("")
    logger.info("⚠  IMPORTANT: Script này KHÔNG scrape lại raw data!")
    logger.info("    Chỉ làm việc với data đã processed sẵn.")
    logger.info("    Nếu cần scrape lại: uv run python src/main.py collect")
    logger.info("")
    
    steps = [
        ("Extract songs from albums", step1_extract_songs),
        ("Create songs.csv", step2_create_songs_csv),
        ("Build graph and verify Song nodes", step3_build_graph),
        ("Check success criteria (≥40% albums have songs)", step4_check_success_criteria),
        ("Test Neo4j import", step5_test_neo4j_import),
        ("Verify with Cypher queries", step6_verify_with_cypher),
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        try:
            success = step_func()
            results[step_name] = success
            if not success:
                logger.error(f"\n✗ Step '{step_name}' failed. Stopping validation.")
                break
        except Exception as e:
            logger.error(f"\n✗ Step '{step_name}' raised exception: {e}")
            results[step_name] = False
            break
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    for step_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {step_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ Phase 3 validation completed successfully!")
        logger.info("✓ Song nodes and PART_OF relationships are working correctly")
        logger.info("✓ PERFORMS_ON relationships (Artist → Song) are working correctly")
        logger.info("✓ Success criteria met: ≥40% albums have songs")
    else:
        logger.error("\n✗ Phase 3 validation failed")
        logger.error("Please check the errors above and fix issues before proceeding")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


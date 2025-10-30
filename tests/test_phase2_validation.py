#!/usr/bin/env python3
"""
Test và Validate Phase 2: Record Label Nodes + SIGNED_WITH Relationships
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
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please run with: uv run python test_phase2_validation.py")
    sys.exit(1)


def check_neo4j_connection(config_path: str = "config/neo4j_config.json"):
    """Check if Neo4j is accessible"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], password)
        )
        
        # Test connection
        with driver.session(database=config.get('database', 'neo4j')) as session:
            result = session.run("RETURN 1 as test")
            result.single()
        
        driver.close()
        logger.info("✓ Neo4j connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Neo4j connection failed: {e}")
        logger.error("Make sure Neo4j is running:")
        logger.error("  - Docker: docker-compose up -d")
        logger.error("  - Local: sudo systemctl start neo4j")
        logger.error("  - Or check Neo4j Desktop is running")
        logger.error("Check Neo4j Browser: http://localhost:7474")
        return False


def step1_reprocess_data():
    """Step 1: Re-process data to include record labels"""
    logger.info("=" * 60)
    logger.info("STEP 1: RE-PROCESS DATA TO INCLUDE RECORD LABELS")
    logger.info("=" * 60)
    
    try:
        # Parse infoboxes
        logger.info("Parsing artist infoboxes...")
        parsed_count = parse_all(
            input_path="data/raw/artists.json",
            output_path="data/processed/parsed_artists.json"
        )
        logger.info(f"✓ Parsed {parsed_count} artists")
        
        # Check if labels were extracted
        with open("data/processed/parsed_artists.json", 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        artists_with_labels = [a for a in parsed_data if 'labels' in a and a.get('labels')]
        logger.info(f"✓ Found {len(artists_with_labels)} artists with record labels")
        
        if len(artists_with_labels) > 0:
            sample = artists_with_labels[0]
            logger.info(f"Sample artist with labels: {sample.get('name', 'Unknown')}")
            logger.info(f"  Labels: {sample.get('labels', [])}")
        
        # Clean and filter data
        logger.info("Cleaning and filtering data...")
        clean_count = clean_all(
            input_path="data/processed/parsed_artists.json",
            nodes_output="data/processed/nodes.csv",
            albums_output="data/processed/albums.json"
        )
        logger.info(f"✓ Cleaned data: {clean_count} artists ready")
        
        # Verify labels column exists in nodes.csv
        df = pd.read_csv("data/processed/nodes.csv")
        if 'labels' in df.columns:
            labels_count = df['labels'].notna().sum()
            logger.info(f"✓ Found 'labels' column in nodes.csv with {labels_count} non-empty values")
            
            # Count unique labels
            all_labels = set()
            for labels_str in df['labels'].dropna():
                if labels_str:
                    labels = [l.strip() for l in str(labels_str).split(';') if l.strip()]
                    all_labels.update(labels)
            logger.info(f"✓ Found {len(all_labels)} unique record labels")
            if len(all_labels) > 0:
                logger.info(f"  Sample labels: {list(all_labels)[:5]}")
        else:
            logger.warning("✗ 'labels' column not found in nodes.csv")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Data processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step2_build_graph():
    """Step 2: Build graph and verify RecordLabel nodes"""
    logger.info("=" * 60)
    logger.info("STEP 2: BUILD GRAPH AND VERIFY RECORD LABEL NODES")
    logger.info("=" * 60)
    
    try:
        # Check if genre files exist
        genres_path = "data/migrations/genres.csv" if os.path.exists("data/migrations/genres.csv") else None
        has_genre_path = "data/migrations/has_genre_relationships.csv" if os.path.exists("data/migrations/has_genre_relationships.csv") else None
        band_classifications_path = "data/processed/band_classifications.json" if os.path.exists("data/processed/band_classifications.json") else None
        
        if genres_path:
            logger.info(f"✓ Found genres file: {genres_path}")
        if has_genre_path:
            logger.info(f"✓ Found HAS_GENRE relationships: {has_genre_path}")
        if band_classifications_path:
            logger.info(f"✓ Found band classifications: {band_classifications_path}")
        
        # Build graph
        node_count = build_graph(
            nodes_path="data/processed/nodes.csv",
            albums_path="data/processed/albums.json",
            output_dir="data/processed",
            genres_path=genres_path,
            has_genre_path=has_genre_path,
            band_classifications_path=band_classifications_path
        )
        logger.info(f"✓ Built graph with {node_count} nodes")
        
        # Verify record_labels.csv was created
        record_labels_path = "data/processed/record_labels.csv"
        if os.path.exists(record_labels_path):
            df_labels = pd.read_csv(record_labels_path)
            logger.info(f"✓ RecordLabel nodes CSV created: {len(df_labels)} labels")
            logger.info(f"  Sample labels: {df_labels.head(5)['name'].tolist()}")
        else:
            logger.warning("✗ record_labels.csv not found")
            return False
        
        # Verify edges.csv contains SIGNED_WITH edges
        edges_path = "data/processed/edges.csv"
        if os.path.exists(edges_path):
            df_edges = pd.read_csv(edges_path)
            signed_with_count = len(df_edges[df_edges['type'] == 'SIGNED_WITH'])
            logger.info(f"✓ Found {signed_with_count} SIGNED_WITH edges in edges.csv")
            
            if signed_with_count > 0:
                sample_edges = df_edges[df_edges['type'] == 'SIGNED_WITH'].head(3)
                logger.info("  Sample SIGNED_WITH edges:")
                for idx, row in sample_edges.iterrows():
                    logger.info(f"    {row['from']} -> {row['to']}")
            else:
                logger.warning("✗ No SIGNED_WITH edges found")
                return False
        else:
            logger.warning("✗ edges.csv not found")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Graph building failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step3_test_neo4j_import():
    """Step 3: Test Neo4j import"""
    logger.info("=" * 60)
    logger.info("STEP 3: TEST NEO4J IMPORT")
    logger.info("=" * 60)
    
    logger.info("Checking Neo4j connection (local or Docker)...")
    if not check_neo4j_connection():
        logger.warning("Neo4j connection check failed. Continuing anyway...")
        logger.info("If using Neo4j local, make sure:")
        logger.info("  1. Neo4j is running (check: http://localhost:7474)")
        logger.info("  2. Password is set in .env file")
        logger.info("  3. Connection details in config/neo4j_config.json are correct")
    
    try:
        config_path = "config/neo4j_config.json"
        import_to_neo4j(
            data_dir="data/processed",
            config_path=config_path,
            clear_first=True  # Clear database for clean test
        )
        logger.info("✓ Neo4j import completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Neo4j import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def step4_verify_with_cypher():
    """Step 4: Run Cypher queries to verify data"""
    logger.info("=" * 60)
    logger.info("STEP 4: VERIFY DATA WITH CYPHER QUERIES")
    logger.info("=" * 60)
    
    if not check_neo4j_connection():
        return False
    
    try:
        with open("config/neo4j_config.json", 'r') as f:
            config = json.load(f)
        
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], password)
        )
        
        with driver.session(database=config.get('database', 'neo4j')) as session:
            # Query 1: Count RecordLabel nodes
            logger.info("\nQuery 1: Count RecordLabel nodes")
            result = session.run("""
                MATCH (r:RecordLabel)
                RETURN count(r) AS count
            """)
            record = result.single()
            label_count = record['count']
            logger.info(f"  ✓ Found {label_count} RecordLabel nodes")
            
            if label_count == 0:
                logger.warning("✗ No RecordLabel nodes found!")
                driver.close()
                return False
            
            # Query 2: Count SIGNED_WITH relationships
            logger.info("\nQuery 2: Count SIGNED_WITH relationships")
            result = session.run("""
                MATCH ()-[r:SIGNED_WITH]->()
                RETURN count(r) AS count
            """)
            record = result.single()
            signed_count = record['count']
            logger.info(f"  ✓ Found {signed_count} SIGNED_WITH relationships")
            
            if signed_count == 0:
                logger.warning("✗ No SIGNED_WITH relationships found!")
                driver.close()
                return False
            
            # Query 3: Get sample RecordLabel nodes
            logger.info("\nQuery 3: Sample RecordLabel nodes")
            result = session.run("""
                MATCH (r:RecordLabel)
                RETURN r.id AS id, r.name AS name
                LIMIT 10
            """)
            labels = [record.values() for record in result]
            for label_id, label_name in labels:
                logger.info(f"  • {label_name} (id: {label_id})")
            
            # Query 4: Get artists signed with labels
            logger.info("\nQuery 4: Artists signed with record labels (sample)")
            result = session.run("""
                MATCH (a:Artist)-[:SIGNED_WITH]->(r:RecordLabel)
                RETURN a.name AS artist, r.name AS label
                LIMIT 10
            """)
            relationships = [record.values() for record in result]
            for artist, label in relationships:
                logger.info(f"  • {artist} -> {label}")
            
            # Query 5: Most popular record labels (by number of artists)
            logger.info("\nQuery 5: Top 10 record labels by number of artists")
            result = session.run("""
                MATCH (a:Artist)-[:SIGNED_WITH]->(r:RecordLabel)
                RETURN r.name AS label, count(a) AS artist_count
                ORDER BY artist_count DESC
                LIMIT 10
            """)
            for record in result:
                logger.info(f"  • {record['label']}: {record['artist_count']} artists")
            
            # Query 6: Artists with multiple labels
            logger.info("\nQuery 6: Artists signed with multiple labels (sample)")
            result = session.run("""
                MATCH (a:Artist)-[:SIGNED_WITH]->(r:RecordLabel)
                WITH a, collect(r.name) AS labels
                WHERE size(labels) > 1
                RETURN a.name AS artist, labels
                LIMIT 10
            """)
            for record in result:
                logger.info(f"  • {record['artist']}: {', '.join(record['labels'])}")
            
            # Query 7: Record labels with most collaborations
            logger.info("\nQuery 7: Record labels network connections")
            result = session.run("""
                MATCH (r:RecordLabel)
                OPTIONAL MATCH (a:Artist)-[:SIGNED_WITH]->(r)
                OPTIONAL MATCH (a)-[:COLLABORATES_WITH]-(other:Artist)
                RETURN r.name AS label, 
                       count(DISTINCT a) AS artists,
                       count(DISTINCT other) AS collaborators
                ORDER BY artists DESC
                LIMIT 10
            """)
            for record in result:
                logger.info(f"  • {record['label']}: {record['artists']} artists, {record['collaborators']} collaborators")
        
        driver.close()
        logger.info("\n✓ All Cypher queries executed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Cypher verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation steps"""
    logger.info("=" * 60)
    logger.info("PHASE 2 VALIDATION: RECORD LABEL NODES + SIGNED_WITH RELATIONSHIPS")
    logger.info("=" * 60)
    
    steps = [
        ("Re-process data", step1_reprocess_data),
        ("Build graph", step2_build_graph),
        ("Test Neo4j import", step3_test_neo4j_import),
        ("Verify with Cypher", step4_verify_with_cypher),
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
        logger.info("\n✓ Phase 2 validation completed successfully!")
        logger.info("✓ RecordLabel nodes and SIGNED_WITH relationships are working correctly")
    else:
        logger.error("\n✗ Phase 2 validation failed")
        logger.error("Please check the errors above and fix issues before proceeding")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


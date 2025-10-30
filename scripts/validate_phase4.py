"""
Validation script for Phase 4: Awards + AWARD_NOMINATION Relationships
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from graph_building.builder import GraphBuilder
from graph_building.importer import Neo4jImporter
from data_collection.utils import logger
from neo4j import GraphDatabase
from dotenv import load_dotenv


def validate_award_files():
    """Validate that award files exist and have correct format"""
    logger.info("=" * 60)
    logger.info("VALIDATING AWARD FILES")
    logger.info("=" * 60)
    
    awards_csv = "data/processed/awards.csv"
    awards_json = "data/processed/awards.json"
    
    results = {
        "awards_csv_exists": False,
        "awards_json_exists": False,
        "awards_csv_count": 0,
        "awards_json_artists": 0,
        "awards_json_total_awards": 0
    }
    
    # Check awards.csv
    if os.path.exists(awards_csv):
        results["awards_csv_exists"] = True
        try:
            df = pd.read_csv(awards_csv, encoding='utf-8')
            results["awards_csv_count"] = len(df)
            logger.info(f"✓ Found awards.csv with {len(df)} award nodes")
            
            # Validate required columns
            required_cols = ['id', 'name', 'ceremony', 'category', 'year']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"✗ Missing columns in awards.csv: {missing_cols}")
            else:
                logger.info(f"✓ All required columns present in awards.csv")
        except Exception as e:
            logger.error(f"✗ Error reading awards.csv: {e}")
    else:
        logger.warning(f"✗ awards.csv not found at {awards_csv}")
    
    # Check awards.json
    if os.path.exists(awards_json):
        results["awards_json_exists"] = True
        try:
            with open(awards_json, 'r', encoding='utf-8') as f:
                awards_data = json.load(f)
            results["awards_json_artists"] = len(awards_data)
            
            # Count total awards
            total_awards = sum(len(awards) for awards in awards_data.values())
            results["awards_json_total_awards"] = total_awards
            
            logger.info(f"✓ Found awards.json with {len(awards_data)} artists")
            logger.info(f"✓ Total awards in JSON: {total_awards}")
        except Exception as e:
            logger.error(f"✗ Error reading awards.json: {e}")
    else:
        logger.warning(f"✗ awards.json not found at {awards_json}")
    
    return results


def validate_graph_building():
    """Validate that graph building creates Award nodes and AWARD_NOMINATION edges"""
    logger.info("=" * 60)
    logger.info("VALIDATING GRAPH BUILDING")
    logger.info("=" * 60)
    
    results = {
        "award_nodes_created": 0,
        "award_nomination_edges_created": 0,
        "errors": []
    }
    
    try:
        # Check if files exist
        nodes_path = "data/processed/nodes.csv"
        albums_path = "data/processed/albums.json"
        awards_csv = "data/processed/awards.csv"
        awards_json = "data/processed/awards.json"
        
        if not os.path.exists(nodes_path):
            logger.error(f"✗ nodes.csv not found: {nodes_path}")
            results["errors"].append("nodes.csv missing")
            return results
        
        if not os.path.exists(albums_path):
            logger.error(f"✗ albums.json not found: {albums_path}")
            results["errors"].append("albums.json missing")
            return results
        
        if not os.path.exists(awards_csv):
            logger.error(f"✗ awards.csv not found: {awards_csv}")
            results["errors"].append("awards.csv missing")
            return results
        
        if not os.path.exists(awards_json):
            logger.error(f"✗ awards.json not found: {awards_json}")
            results["errors"].append("awards.json missing")
            return results
        
        # Build graph
        builder = GraphBuilder()
        
        # Load basic nodes
        df = builder.load_nodes(nodes_path)
        album_map = builder.load_albums(albums_path)
        
        if df.empty:
            logger.error("✗ No nodes to build graph")
            results["errors"].append("No nodes in CSV")
            return results
        
        # Build basic graph
        graph = builder.build_graph(nodes_path, albums_path)
        
        # Load and add award nodes
        awards_df = builder.load_awards(awards_csv)
        if not awards_df.empty:
            builder.add_award_nodes(awards_df)
            results["award_nodes_created"] = len(builder.award_nodes)
            logger.info(f"✓ Created {results['award_nodes_created']} award nodes")
        else:
            logger.warning("✗ No award nodes to add")
            results["errors"].append("No award nodes in CSV")
        
        # Add AWARD_NOMINATION relationships
        builder.add_award_nomination_relationships(awards_json, awards_csv)
        
        # Count AWARD_NOMINATION edges
        award_nomination_count = sum(
            1 for u, v, data in graph.edges(data=True)
            if data.get('relationship') == 'AWARD_NOMINATION'
        )
        results["award_nomination_edges_created"] = award_nomination_count
        logger.info(f"✓ Created {results['award_nomination_edges_created']} AWARD_NOMINATION edges")
        
        # Export to verify
        builder.export_nodes_for_neo4j("data/processed")
        builder.export_edges_csv("data/processed/edges.csv")
        
        logger.info("✓ Graph building validation completed")
        
    except Exception as e:
        logger.error(f"✗ Error during graph building validation: {e}")
        results["errors"].append(str(e))
    
    return results


def validate_csv_export():
    """Validate that CSV exports include Award nodes and AWARD_NOMINATION edges"""
    logger.info("=" * 60)
    logger.info("VALIDATING CSV EXPORTS")
    logger.info("=" * 60)
    
    results = {
        "awards_csv_exported": False,
        "edges_csv_has_award_nominations": False,
        "award_count_in_csv": 0,
        "award_nomination_count_in_csv": 0
    }
    
    # Check awards.csv export
    awards_csv = "data/processed/awards.csv"
    if os.path.exists(awards_csv):
        try:
            df = pd.read_csv(awards_csv, encoding='utf-8')
            results["awards_csv_exported"] = True
            results["award_count_in_csv"] = len(df)
            logger.info(f"✓ awards.csv exported with {len(df)} awards")
        except Exception as e:
            logger.error(f"✗ Error reading exported awards.csv: {e}")
    else:
        logger.warning("✗ awards.csv not found after export")
    
    # Check edges.csv for AWARD_NOMINATION
    edges_csv = "data/processed/edges.csv"
    if os.path.exists(edges_csv):
        try:
            df = pd.read_csv(edges_csv, encoding='utf-8')
            award_nomination_edges = df[df['type'] == 'AWARD_NOMINATION']
            results["edges_csv_has_award_nominations"] = len(award_nomination_edges) > 0
            results["award_nomination_count_in_csv"] = len(award_nomination_edges)
            
            if results["edges_csv_has_award_nominations"]:
                logger.info(f"✓ edges.csv contains {len(award_nomination_edges)} AWARD_NOMINATION edges")
                
                # Check for optional properties
                if 'status' in award_nomination_edges.columns:
                    status_count = award_nomination_edges['status'].notna().sum()
                    logger.info(f"  - Edges with status: {status_count}")
                
                if 'year' in award_nomination_edges.columns:
                    year_count = award_nomination_edges['year'].notna().sum()
                    logger.info(f"  - Edges with year: {year_count}")
            else:
                logger.warning("✗ No AWARD_NOMINATION edges found in edges.csv")
        except Exception as e:
            logger.error(f"✗ Error reading exported edges.csv: {e}")
    else:
        logger.warning("✗ edges.csv not found after export")
    
    return results


def validate_neo4j_import():
    """Validate Neo4j import of Award nodes and AWARD_NOMINATION relationships"""
    logger.info("=" * 60)
    logger.info("VALIDATING NEO4J IMPORT")
    logger.info("=" * 60)
    
    results = {
        "connected": False,
        "award_nodes_imported": 0,
        "award_nomination_edges_imported": 0,
        "errors": []
    }
    
    try:
        # Load config
        config_path = "config/neo4j_config.json"
        if not os.path.exists(config_path):
            logger.warning(f"✗ Neo4j config not found: {config_path}")
            results["errors"].append("Config file missing")
            return results
        
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Connect to Neo4j
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], password)
        )
        
        results["connected"] = True
        logger.info("✓ Connected to Neo4j")
        
        with driver.session(database=config.get('database', 'neo4j')) as session:
            # Count Award nodes
            result = session.run("MATCH (a:Award) RETURN count(a) AS count")
            award_count = result.single()['count']
            results["award_nodes_imported"] = award_count
            logger.info(f"✓ Found {award_count} Award nodes in Neo4j")
            
            # Count AWARD_NOMINATION relationships
            result = session.run("MATCH ()-[r:AWARD_NOMINATION]->() RETURN count(r) AS count")
            edge_count = result.single()['count']
            results["award_nomination_edges_imported"] = edge_count
            logger.info(f"✓ Found {edge_count} AWARD_NOMINATION relationships in Neo4j")
            
            # Check for optional properties
            result = session.run("""
                MATCH ()-[r:AWARD_NOMINATION]->()
                RETURN 
                    count(r) AS total,
                    count(r.status) AS with_status,
                    count(r.year) AS with_year
            """)
            props = result.single()
            logger.info(f"  - Total relationships: {props['total']}")
            logger.info(f"  - With status property: {props['with_status']}")
            logger.info(f"  - With year property: {props['with_year']}")
        
        driver.close()
        
    except Exception as e:
        logger.error(f"✗ Error validating Neo4j import: {e}")
        results["errors"].append(str(e))
    
    return results


def check_success_criteria():
    """Check success criteria: ≥80% seed artists have awards"""
    logger.info("=" * 60)
    logger.info("CHECKING SUCCESS CRITERIA")
    logger.info("=" * 60)
    
    results = {
        "seed_artists_count": 0,
        "artists_with_awards": 0,
        "percentage": 0.0,
        "meets_criteria": False
    }
    
    try:
        # Load seed artists
        seed_file = "config/seed_artists.json"
        if not os.path.exists(seed_file):
            logger.warning(f"✗ Seed artists file not found: {seed_file}")
            return results
        
        with open(seed_file, 'r', encoding='utf-8') as f:
            seed_artists = json.load(f)
        
        results["seed_artists_count"] = len(seed_artists)
        logger.info(f"✓ Found {len(seed_artists)} seed artists")
        
        # Load awards data
        awards_json = "data/processed/awards.json"
        if not os.path.exists(awards_json):
            logger.warning(f"✗ Awards JSON not found: {awards_json}")
            return results
        
        with open(awards_json, 'r', encoding='utf-8') as f:
            awards_data = json.load(f)
        
        # Count artists with awards
        artists_with_awards = sum(1 for artist in seed_artists if artist in awards_data and awards_data[artist])
        results["artists_with_awards"] = artists_with_awards
        
        if results["seed_artists_count"] > 0:
            results["percentage"] = (artists_with_awards / results["seed_artists_count"]) * 100
            results["meets_criteria"] = results["percentage"] >= 80.0
        
        logger.info(f"✓ Artists with awards: {artists_with_awards} / {results['seed_artists_count']}")
        logger.info(f"✓ Percentage: {results['percentage']:.1f}%")
        
        if results["meets_criteria"]:
            logger.info("✓ SUCCESS CRITERIA MET: ≥80% seed artists have awards")
        else:
            logger.warning(f"✗ SUCCESS CRITERIA NOT MET: {results['percentage']:.1f}% < 80%")
        
    except Exception as e:
        logger.error(f"✗ Error checking success criteria: {e}")
    
    return results


def run_cypher_queries():
    """Run Cypher queries to verify data"""
    logger.info("=" * 60)
    logger.info("RUNNING CYPHER QUERIES")
    logger.info("=" * 60)
    
    queries = {
        "1. Count Award nodes": "MATCH (a:Award) RETURN count(a) AS count",
        "2. Count AWARD_NOMINATION relationships": "MATCH ()-[r:AWARD_NOMINATION]->() RETURN count(r) AS count",
        "3. Artists with most awards": """
            MATCH (a:Artist)-[:AWARD_NOMINATION]->(aw:Award)
            RETURN a.name AS artist, count(aw) AS award_count
            ORDER BY award_count DESC
            LIMIT 10
        """,
        "4. Awards by ceremony": """
            MATCH (a:Award)
            RETURN a.ceremony AS ceremony, count(a) AS count
            ORDER BY count DESC
        """,
        "5. Won vs Nominated": """
            MATCH ()-[r:AWARD_NOMINATION]->()
            RETURN 
                COALESCE(r.status, 'unknown') AS status,
                count(r) AS count
            ORDER BY count DESC
        """,
        "6. Awards by year": """
            MATCH (a:Award)
            WHERE a.year IS NOT NULL AND a.year <> ''
            RETURN a.year AS year, count(a) AS count
            ORDER BY year DESC
            LIMIT 10
        """
    }
    
    results = {}
    
    try:
        # Load config
        config_path = "config/neo4j_config.json"
        if not os.path.exists(config_path):
            logger.warning(f"✗ Neo4j config not found: {config_path}")
            return results
        
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Connect to Neo4j
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], password)
        )
        
        with driver.session(database=config.get('database', 'neo4j')) as session:
            for query_name, query in queries.items():
                try:
                    logger.info(f"\n{query_name}:")
                    result = session.run(query)
                    
                    records = list(result)
                    if records:
                        for record in records[:10]:  # Limit to 10 results
                            logger.info(f"  {dict(record)}")
                        results[query_name] = "success"
                    else:
                        logger.warning(f"  No results")
                        results[query_name] = "no_results"
                except Exception as e:
                    logger.error(f"  Error: {e}")
                    results[query_name] = f"error: {str(e)}"
        
        driver.close()
        
    except Exception as e:
        logger.error(f"✗ Error running Cypher queries: {e}")
    
    return results


def main():
    """Run all validation tests"""
    logger.info("=" * 60)
    logger.info("PHASE 4 VALIDATION")
    logger.info("=" * 60)
    
    all_results = {}
    
    # 1. Validate award files
    all_results["file_validation"] = validate_award_files()
    
    # 2. Validate graph building
    all_results["graph_building"] = validate_graph_building()
    
    # 3. Validate CSV export
    all_results["csv_export"] = validate_csv_export()
    
    # 4. Validate Neo4j import
    all_results["neo4j_import"] = validate_neo4j_import()
    
    # 5. Check success criteria
    all_results["success_criteria"] = check_success_criteria()
    
    # 6. Run Cypher queries
    all_results["cypher_queries"] = run_cypher_queries()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    print("\nFile Validation:")
    print(f"  - Awards CSV exists: {all_results['file_validation']['awards_csv_exists']}")
    print(f"  - Awards JSON exists: {all_results['file_validation']['awards_json_exists']}")
    print(f"  - Award nodes in CSV: {all_results['file_validation']['awards_csv_count']}")
    
    print("\nGraph Building:")
    print(f"  - Award nodes created: {all_results['graph_building']['award_nodes_created']}")
    print(f"  - AWARD_NOMINATION edges created: {all_results['graph_building']['award_nomination_edges_created']}")
    
    print("\nCSV Export:")
    print(f"  - Awards CSV exported: {all_results['csv_export']['awards_csv_exported']}")
    print(f"  - AWARD_NOMINATION in edges.csv: {all_results['csv_export']['edges_csv_has_award_nominations']}")
    
    print("\nNeo4j Import:")
    print(f"  - Award nodes imported: {all_results['neo4j_import']['award_nodes_imported']}")
    print(f"  - AWARD_NOMINATION edges imported: {all_results['neo4j_import']['award_nomination_edges_imported']}")
    
    print("\nSuccess Criteria:")
    print(f"  - Artists with awards: {all_results['success_criteria']['artists_with_awards']} / {all_results['success_criteria']['seed_artists_count']}")
    print(f"  - Percentage: {all_results['success_criteria']['percentage']:.1f}%")
    print(f"  - Meets criteria (≥80%): {all_results['success_criteria']['meets_criteria']}")
    
    # Overall status
    success = (
        all_results['file_validation']['awards_csv_exists'] and
        all_results['file_validation']['awards_json_exists'] and
        all_results['graph_building']['award_nodes_created'] > 0 and
        all_results['graph_building']['award_nomination_edges_created'] > 0 and
        all_results['csv_export']['awards_csv_exported'] and
        all_results['success_criteria']['meets_criteria']
    )
    
    if success:
        logger.info("\n✓ PHASE 4 VALIDATION PASSED")
        return 0
    else:
        logger.error("\n✗ PHASE 4 VALIDATION FAILED")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())


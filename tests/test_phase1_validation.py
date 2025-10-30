"""
Task 1.7: Test và Validate Phase 1
Mục tiêu: Verify toàn bộ Phase 1 hoạt động đúng
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Add src to path (same pattern as other scripts)
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph_building.builder import GraphBuilder
from graph_building.importer import Neo4jImporter
from data_collection.utils import logger


class Phase1Validator:
    """Validate Phase 1: Band nodes and MEMBER_OF relationships"""
    
    def __init__(self):
        self.results = {
            'band_nodes_created': False,
            'member_of_edges_created': False,
            'bands_csv_exported': False,
            'member_of_in_edges_csv': False,
            'neo4j_import_success': False,
            'neo4j_band_nodes': False,
            'neo4j_member_of_edges': False,
            'cypher_queries_passed': False
        }
        self.errors = []
        self.stats = {}
    
    def test_1_build_graph(self):
        """Test 1: Build graph and verify Band nodes are created"""
        logger.info("=" * 60)
        logger.info("TEST 1: Build Graph and Verify Band Nodes")
        logger.info("=" * 60)
        
        try:
            builder = GraphBuilder()
            
            # Load data
            nodes_path = "data/processed/nodes.csv"
            albums_path = "data/processed/albums.json"
            band_classifications_path = "data/processed/band_classifications.json"
            
            if not os.path.exists(nodes_path):
                raise FileNotFoundError(f"Nodes file not found: {nodes_path}")
            if not os.path.exists(albums_path):
                raise FileNotFoundError(f"Albums file not found: {albums_path}")
            if not os.path.exists(band_classifications_path):
                raise FileNotFoundError(f"Band classifications file not found: {band_classifications_path}")
            
            # Build base graph
            df = builder.load_nodes(nodes_path)
            album_map = builder.load_albums(albums_path)
            
            if df.empty:
                raise ValueError("No nodes to build graph")
            
            builder.add_artist_nodes(df)
            builder.add_album_nodes_and_edges(album_map)
            
            # Load and add band classifications
            classifications = builder.load_band_classifications(band_classifications_path)
            builder.add_band_nodes(classifications)
            
            # Verify Band nodes
            band_count = len(builder.band_nodes)
            logger.info(f"✓ Created {band_count} Band nodes")
            
            # Verify nodes in graph
            band_nodes_in_graph = [
                node_id for node_id in builder.graph.nodes()
                if builder.graph.nodes[node_id].get('node_type') == 'Band'
            ]
            
            logger.info(f"✓ Found {len(band_nodes_in_graph)} Band nodes in graph")
            
            if band_count > 0 and len(band_nodes_in_graph) > 0:
                self.results['band_nodes_created'] = True
                self.stats['band_nodes_count'] = band_count
                
                # Show sample bands
                logger.info("Sample Band nodes:")
                for i, (band_name, band_id) in enumerate(list(builder.band_nodes.items())[:5]):
                    node_data = builder.graph.nodes[band_id]
                    logger.info(f"  {i+1}. {band_name} (id: {band_id}, confidence: {node_data.get('classification_confidence', 0):.2f})")
            else:
                self.errors.append("No Band nodes created")
            
            return builder
            
        except Exception as e:
            logger.error(f"✗ Test 1 failed: {e}")
            self.errors.append(f"Test 1: {str(e)}")
            return None
    
    def test_2_member_of_edges(self, builder: GraphBuilder):
        """Test 2: Verify MEMBER_OF edges are created"""
        logger.info("=" * 60)
        logger.info("TEST 2: Verify MEMBER_OF Edges")
        logger.info("=" * 60)
        
        try:
            if builder is None:
                raise ValueError("Builder not available")
            
            # Load classifications again
            band_classifications_path = "data/processed/band_classifications.json"
            classifications = builder.load_band_classifications(band_classifications_path)
            
            # Add MEMBER_OF relationships
            builder.add_member_of_relationships(classifications)
            
            # Count MEMBER_OF edges
            member_of_edges = [
                (u, v, data) for u, v, data in builder.graph.edges(data=True)
                if data.get('relationship') == 'MEMBER_OF'
            ]
            
            edge_count = len(member_of_edges)
            logger.info(f"✓ Created {edge_count} MEMBER_OF edges")
            
            if edge_count > 0:
                self.results['member_of_edges_created'] = True
                self.stats['member_of_edges_count'] = edge_count
                
                # Show sample edges
                logger.info("Sample MEMBER_OF edges:")
                for i, (u, v, data) in enumerate(member_of_edges[:5]):
                    artist_data = builder.graph.nodes[u]
                    band_data = builder.graph.nodes[v]
                    logger.info(f"  {i+1}. {artist_data.get('name', u)} -> MEMBER_OF -> {band_data.get('name', v)}")
            else:
                self.errors.append("No MEMBER_OF edges created")
            
            return builder
            
        except Exception as e:
            logger.error(f"✗ Test 2 failed: {e}")
            self.errors.append(f"Test 2: {str(e)}")
            return builder
    
    def test_3_csv_export(self, builder: GraphBuilder):
        """Test 3: Verify CSV export"""
        logger.info("=" * 60)
        logger.info("TEST 3: Verify CSV Export")
        logger.info("=" * 60)
        
        try:
            if builder is None:
                raise ValueError("Builder not available")
            
            output_dir = "data/processed"
            builder.export_nodes_for_neo4j(output_dir)
            builder.export_edges_csv(f"{output_dir}/edges.csv")
            
            # Check bands.csv
            bands_csv_path = f"{output_dir}/bands.csv"
            if os.path.exists(bands_csv_path):
                df_bands = pd.read_csv(bands_csv_path)
                logger.info(f"✓ bands.csv exported with {len(df_bands)} bands")
                self.results['bands_csv_exported'] = True
                
                # Show sample
                logger.info("Sample from bands.csv:")
                for i, row in df_bands.head(3).iterrows():
                    logger.info(f"  {i+1}. {row['name']} (id: {row['id']})")
            else:
                self.errors.append("bands.csv not found")
            
            # Check edges.csv for MEMBER_OF
            edges_csv_path = f"{output_dir}/edges.csv"
            if os.path.exists(edges_csv_path):
                df_edges = pd.read_csv(edges_csv_path)
                member_of_count = len(df_edges[df_edges['type'] == 'MEMBER_OF'])
                logger.info(f"✓ edges.csv contains {member_of_count} MEMBER_OF edges")
                
                if member_of_count > 0:
                    self.results['member_of_in_edges_csv'] = True
                    self.stats['member_of_in_csv'] = member_of_count
                else:
                    self.errors.append("No MEMBER_OF edges in edges.csv")
            else:
                self.errors.append("edges.csv not found")
            
        except Exception as e:
            logger.error(f"✗ Test 3 failed: {e}")
            self.errors.append(f"Test 3: {str(e)}")
    
    def test_4_neo4j_import(self):
        """Test 4: Test Neo4j import"""
        logger.info("=" * 60)
        logger.info("TEST 4: Test Neo4j Import")
        logger.info("=" * 60)
        
        try:
            load_dotenv()
            config_path = "config/neo4j_config.json"
            
            if not os.path.exists(config_path):
                logger.warning(f"Config file not found: {config_path}, using defaults")
                config = {
                    "uri": "bolt://localhost:7687",
                    "user": "neo4j",
                    "database": "neo4j"
                }
            else:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            password = os.getenv('NEO4J_PASS', 'password')
            driver = GraphDatabase.driver(
                config['uri'],
                auth=(config['user'], password)
            )
            
            # Test connection
            with driver.session(database=config.get('database', 'neo4j')) as session:
                result = session.run("RETURN 1 as test")
                result.single()
                logger.info("✓ Neo4j connection successful")
            
            # Check if bands exist
            with driver.session(database=config.get('database', 'neo4j')) as session:
                result = session.run("MATCH (b:Band) RETURN count(b) as count")
                band_count = result.single()['count']
                logger.info(f"✓ Found {band_count} Band nodes in Neo4j")
                
                if band_count > 0:
                    self.results['neo4j_band_nodes'] = True
                    self.stats['neo4j_band_count'] = band_count
                    
                    # Show sample bands
                    result = session.run("""
                        MATCH (b:Band)
                        RETURN b.name as name, b.id as id, b.classification_confidence as confidence
                        LIMIT 5
                    """)
                    logger.info("Sample Band nodes in Neo4j:")
                    for i, record in enumerate(result, 1):
                        logger.info(f"  {i}. {record['name']} (id: {record['id']}, confidence: {record['confidence']:.2f})")
                else:
                    self.errors.append("No Band nodes in Neo4j")
            
            # Check MEMBER_OF relationships
            with driver.session(database=config.get('database', 'neo4j')) as session:
                result = session.run("""
                    MATCH ()-[r:MEMBER_OF]->()
                    RETURN count(r) as count
                """)
                member_of_count = result.single()['count']
                logger.info(f"✓ Found {member_of_count} MEMBER_OF relationships in Neo4j")
                
                if member_of_count > 0:
                    self.results['neo4j_member_of_edges'] = True
                    self.stats['neo4j_member_of_count'] = member_of_count
                    
                    # Show sample relationships
                    result = session.run("""
                        MATCH (a:Artist)-[r:MEMBER_OF]->(b:Band)
                        RETURN a.name as artist, b.name as band
                        LIMIT 5
                    """)
                    logger.info("Sample MEMBER_OF relationships in Neo4j:")
                    for i, record in enumerate(result, 1):
                        logger.info(f"  {i}. {record['artist']} -> MEMBER_OF -> {record['band']}")
                else:
                    self.errors.append("No MEMBER_OF relationships in Neo4j")
            
            driver.close()
            self.results['neo4j_import_success'] = True
            
        except Exception as e:
            logger.error(f"✗ Test 4 failed: {e}")
            logger.error("Make sure Neo4j is running: docker-compose up -d")
            self.errors.append(f"Test 4: {str(e)}")
    
    def test_5_cypher_queries(self):
        """Test 5: Run Cypher queries to verify data"""
        logger.info("=" * 60)
        logger.info("TEST 5: Run Cypher Queries")
        logger.info("=" * 60)
        
        try:
            load_dotenv()
            config_path = "config/neo4j_config.json"
            
            if not os.path.exists(config_path):
                config = {
                    "uri": "bolt://localhost:7687",
                    "user": "neo4j",
                    "database": "neo4j"
                }
            else:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            password = os.getenv('NEO4J_PASS', 'password')
            driver = GraphDatabase.driver(
                config['uri'],
                auth=(config['user'], password)
            )
            
            queries_passed = 0
            total_queries = 0
            
            queries = [
                ("Count all Band nodes", "MATCH (b:Band) RETURN count(b) as count"),
                ("Count all MEMBER_OF relationships", "MATCH ()-[r:MEMBER_OF]->() RETURN count(r) as count"),
                ("Bands with most members", """
                    MATCH (a:Artist)-[:MEMBER_OF]->(b:Band)
                    RETURN b.name as band, count(a) as member_count
                    ORDER BY member_count DESC
                    LIMIT 5
                """),
                ("Artists who are members of bands", """
                    MATCH (a:Artist)-[:MEMBER_OF]->(b:Band)
                    RETURN a.name as artist, b.name as band
                    LIMIT 10
                """),
                ("Band nodes with attributes", """
                    MATCH (b:Band)
                    RETURN b.name as name, b.id as id, b.url as url, b.classification_confidence as confidence
                    LIMIT 5
                """)
            ]
            
            with driver.session(database=config.get('database', 'neo4j')) as session:
                for query_name, query in queries:
                    total_queries += 1
                    try:
                        logger.info(f"\nQuery: {query_name}")
                        result = session.run(query)
                        
                        records = list(result)
                        if records:
                            queries_passed += 1
                            logger.info(f"✓ Query passed - Results:")
                            for i, record in enumerate(records[:5], 1):
                                logger.info(f"  {i}. {dict(record)}")
                        else:
                            logger.warning(f"⚠ Query returned no results")
                    except Exception as e:
                        logger.error(f"✗ Query failed: {e}")
            
            driver.close()
            
            if queries_passed == total_queries:
                self.results['cypher_queries_passed'] = True
            
            logger.info(f"\n✓ Passed {queries_passed}/{total_queries} queries")
            
        except Exception as e:
            logger.error(f"✗ Test 5 failed: {e}")
            self.errors.append(f"Test 5: {str(e)}")
    
    def print_summary(self):
        """Print validation summary"""
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 1 VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for v in self.results.values() if v)
        
        logger.info(f"\nTests Passed: {passed_tests}/{total_tests}")
        logger.info("\nResults:")
        for test_name, passed in self.results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"  {status}: {test_name}")
        
        if self.stats:
            logger.info("\nStatistics:")
            for key, value in self.stats.items():
                logger.info(f"  - {key}: {value}")
        
        if self.errors:
            logger.error("\nErrors:")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        logger.info("\n" + "=" * 60)
        
        if passed_tests == total_tests:
            logger.info("✓ PHASE 1 VALIDATION SUCCESSFUL")
            logger.info("✓ Phase 1 hoàn thành, sẵn sàng cho Phase 2")
            return True
        else:
            logger.error("✗ PHASE 1 VALIDATION FAILED")
            logger.error(f"✗ {total_tests - passed_tests} test(s) failed")
            return False
    
    def run_all_tests(self):
        """Run all validation tests"""
        logger.info("=" * 60)
        logger.info("PHASE 1 VALIDATION TEST SUITE")
        logger.info("=" * 60)
        
        # Test 1: Build graph
        builder = self.test_1_build_graph()
        
        # Test 2: MEMBER_OF edges
        builder = self.test_2_member_of_edges(builder)
        
        # Test 3: CSV export
        if builder:
            self.test_3_csv_export(builder)
        
        # Test 4: Neo4j import
        self.test_4_neo4j_import()
        
        # Test 5: Cypher queries
        self.test_5_cypher_queries()
        
        # Print summary
        return self.print_summary()


def main():
    """Main function"""
    validator = Phase1Validator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""Test shortest path algorithm between 2 nodes in Neo4j graph"""

import sys
import os
import json
import argparse
from typing import Dict, List, Optional, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from neo4j import GraphDatabase
from dotenv import load_dotenv
from data_collection.utils import logger


class ShortestPathFinder:
    """Find shortest paths between nodes in Neo4j graph"""
    
    def __init__(self, config_path: str = "config/neo4j_config.json"):
        """Initialize Neo4j connection"""
        self.config = self._load_config(config_path)
        
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        self.driver = GraphDatabase.driver(
            self.config['uri'],
            auth=(self.config['user'], password)
        )
        
        logger.info(f"Connected to Neo4j at {self.config['uri']}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load Neo4j configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading Neo4j config: {e}, using defaults")
            return {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "database": "neo4j"
            }
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")
    
    def find_node_by_name(self, name: str, node_type: Optional[str] = None) -> Optional[Dict]:
        """
        Find a node by name
        
        Args:
            name: Name of the node
            node_type: Optional node type (Artist, Band, Album, etc.)
            
        Returns:
            Dictionary with node info or None if not found
        """
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            if node_type:
                query = f"""
                    MATCH (n:{node_type})
                    WHERE n.name = $name OR n.title = $name
                    RETURN n, labels(n)[0] AS label
                    LIMIT 1
                """
            else:
                query = """
                    MATCH (n)
                    WHERE n.name = $name OR n.title = $name
                    RETURN n, labels(n)[0] AS label
                    LIMIT 1
                """
            
            result = session.run(query, name=name)
            record = result.single()
            
            if record:
                node = record['n']
                return {
                    'id': node.get('id'),
                    'name': node.get('name') or node.get('title'),
                    'label': record['label'],
                    'properties': dict(node)
                }
            return None
    
    def find_node_by_id(self, node_id: str) -> Optional[Dict]:
        """
        Find a node by ID
        
        Args:
            node_id: ID of the node
            
        Returns:
            Dictionary with node info or None if not found
        """
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            query = """
                MATCH (n {id: $node_id})
                RETURN n, labels(n)[0] AS label
                LIMIT 1
            """
            
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if record:
                node = record['n']
                return {
                    'id': node.get('id'),
                    'name': node.get('name') or node.get('title'),
                    'label': record['label'],
                    'properties': dict(node)
                }
            return None
    
    def find_shortest_path(self, 
                          node1_id: str, 
                          node2_id: str,
                          max_depth: int = 10,
                          relationship_types: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Find shortest path between two nodes
        
        Args:
            node1_id: ID of first node
            node2_id: ID of second node
            max_depth: Maximum path depth to search
            relationship_types: Optional list of relationship types to follow
            
        Returns:
            Dictionary with path information or None if no path exists
        """
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Build relationship pattern
            if relationship_types:
                rel_pattern = '|'.join(relationship_types)
                rel_pattern = f'[:{rel_pattern}*1..{max_depth}]'
            else:
                rel_pattern = f'[*1..{max_depth}]'
            
            query = f"""
                MATCH path = shortestPath(
                    (start {{id: $node1_id}})-{rel_pattern}-(end {{id: $node2_id}})
                )
                RETURN path, length(path) AS path_length
                LIMIT 1
            """
            
            result = session.run(query, node1_id=node1_id, node2_id=node2_id)
            record = result.single()
            
            if record:
                path = record['path']
                path_length = record['path_length']
                
                # Extract nodes and relationships from path
                nodes_in_path = []
                relationships_in_path = []
                
                for i, node in enumerate(path.nodes):
                    node_label = list(node.labels)[0] if node.labels else 'Unknown'
                    node_name = node.get('name') or node.get('title') or node.get('id')
                    
                    nodes_in_path.append({
                        'id': node.get('id'),
                        'name': node_name,
                        'label': node_label,
                        'position': i
                    })
                
                for i, rel in enumerate(path.relationships):
                    relationships_in_path.append({
                        'type': rel.type,
                        'start_node': rel.start_node.get('id'),
                        'end_node': rel.end_node.get('id'),
                        'properties': dict(rel)
                    })
                
                return {
                    'path_exists': True,
                    'path_length': path_length,
                    'nodes': nodes_in_path,
                    'relationships': relationships_in_path,
                    'num_nodes': len(nodes_in_path),
                    'num_relationships': len(relationships_in_path)
                }
            else:
                return {
                    'path_exists': False,
                    'path_length': None,
                    'nodes': [],
                    'relationships': []
                }
    
    def find_all_shortest_paths(self,
                               node1_id: str,
                               node2_id: str,
                               max_depth: int = 10,
                               relationship_types: Optional[List[str]] = None,
                               max_paths: int = 10) -> List[Dict]:
        """
        Find all shortest paths between two nodes
        
        Args:
            node1_id: ID of first node
            node2_id: ID of second node
            max_depth: Maximum path depth to search
            relationship_types: Optional list of relationship types to follow
            max_paths: Maximum number of paths to return
            
        Returns:
            List of dictionaries with path information
        """
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Build relationship pattern
            if relationship_types:
                rel_pattern = '|'.join(relationship_types)
                rel_pattern = f'[:{rel_pattern}*1..{max_depth}]'
            else:
                rel_pattern = f'[*1..{max_depth}]'
            
            # First find the shortest path length
            query_length = f"""
                MATCH path = shortestPath(
                    (start {{id: $node1_id}})-{rel_pattern}-(end {{id: $node2_id}})
                )
                RETURN length(path) AS shortest_length
                LIMIT 1
            """
            
            result = session.run(query_length, node1_id=node1_id, node2_id=node2_id)
            record = result.single()
            
            if not record:
                return []
            
            shortest_length = record['shortest_length']
            
            # Now find all paths with that length
            query_all = f"""
                MATCH path = (start {{id: $node1_id}})-{rel_pattern}-(end {{id: $node2_id}})
                WHERE length(path) = $shortest_length
                RETURN path, length(path) AS path_length
                LIMIT $max_paths
            """
            
            result = session.run(query_all, 
                               node1_id=node1_id, 
                               node2_id=node2_id,
                               shortest_length=shortest_length,
                               max_paths=max_paths)
            
            paths = []
            for record in result:
                path = record['path']
                path_length = record['path_length']
                
                nodes_in_path = []
                relationships_in_path = []
                
                for i, node in enumerate(path.nodes):
                    node_label = list(node.labels)[0] if node.labels else 'Unknown'
                    node_name = node.get('name') or node.get('title') or node.get('id')
                    
                    nodes_in_path.append({
                        'id': node.get('id'),
                        'name': node_name,
                        'label': node_label,
                        'position': i
                    })
                
                for rel in path.relationships:
                    relationships_in_path.append({
                        'type': rel.type,
                        'start_node': rel.start_node.get('id'),
                        'end_node': rel.end_node.get('id'),
                        'properties': dict(rel)
                    })
                
                paths.append({
                    'path_length': path_length,
                    'nodes': nodes_in_path,
                    'relationships': relationships_in_path,
                    'num_nodes': len(nodes_in_path),
                    'num_relationships': len(relationships_in_path)
                })
            
            return paths
    
    def list_sample_nodes(self, node_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        List sample nodes from the graph
        
        Args:
            node_type: Optional node type filter
            limit: Maximum number of nodes to return
            
        Returns:
            List of node dictionaries
        """
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            if node_type:
                query = f"""
                    MATCH (n:{node_type})
                    RETURN n, labels(n)[0] AS label
                    LIMIT $limit
                """
            else:
                query = """
                    MATCH (n)
                    RETURN n, labels(n)[0] AS label
                    LIMIT $limit
                """
            
            result = session.run(query, limit=limit)
            nodes = []
            
            for record in result:
                node = record['n']
                nodes.append({
                    'id': node.get('id'),
                    'name': node.get('name') or node.get('title'),
                    'label': record['label']
                })
            
            return nodes


def print_path_result(result: Dict, node1_name: str, node2_name: str):
    """Print path result in a readable format"""
    print("\n" + "=" * 80)
    print(f"SHORTEST PATH: {node1_name} → {node2_name}")
    print("=" * 80)
    
    if not result.get('path_exists'):
        print("❌ No path found between these nodes")
        return
    
    print(f"\n✓ Path found! Length: {result['path_length']} relationships")
    print(f"  Total nodes in path: {result['num_nodes']}")
    print(f"  Total relationships: {result['num_relationships']}")
    
    print("\n📊 Path Details:")
    print("-" * 80)
    
    nodes = result['nodes']
    relationships = result['relationships']
    
    for i, node in enumerate(nodes):
        print(f"\n[{i+1}] {node['label']}: {node['name']}")
        print(f"    ID: {node['id']}")
        
        if i < len(relationships):
            rel = relationships[i]
            print(f"    └─[{rel['type']}]─→")
    
    print("\n" + "=" * 80)


def print_all_paths(paths: List[Dict], node1_name: str, node2_name: str):
    """Print all shortest paths"""
    print("\n" + "=" * 80)
    print(f"ALL SHORTEST PATHS: {node1_name} → {node2_name}")
    print("=" * 80)
    
    if not paths:
        print("❌ No paths found")
        return
    
    print(f"\n✓ Found {len(paths)} shortest path(s) with length {paths[0]['path_length']}")
    
    for idx, path in enumerate(paths, 1):
        print(f"\n--- Path {idx} ---")
        nodes = path['nodes']
        relationships = path['relationships']
        
        for i, node in enumerate(nodes):
            print(f"[{i+1}] {node['label']}: {node['name']}")
            if i < len(relationships):
                rel = relationships[i]
                print(f"    └─[{rel['type']}]─→")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Find shortest path between 2 nodes in Neo4j graph'
    )
    parser.add_argument('--node1', type=str, help='Name or ID of first node')
    parser.add_argument('--node2', type=str, help='Name or ID of second node')
    parser.add_argument('--type1', type=str, help='Type of first node (Artist, Band, Album, etc.)')
    parser.add_argument('--type2', type=str, help='Type of second node')
    parser.add_argument('--max-depth', type=int, default=10, help='Maximum path depth')
    parser.add_argument('--relationships', type=str, nargs='+', 
                       help='Relationship types to follow (e.g., COLLABORATES_WITH PERFORMS_ON)')
    parser.add_argument('--all-paths', action='store_true', 
                       help='Find all shortest paths instead of just one')
    parser.add_argument('--max-paths', type=int, default=10, 
                       help='Maximum number of paths to return (for --all-paths)')
    parser.add_argument('--list-nodes', type=str, 
                       help='List sample nodes of a specific type (e.g., Artist, Band)')
    parser.add_argument('--config', type=str, default='config/neo4j_config.json',
                       help='Path to Neo4j config file')
    
    args = parser.parse_args()
    
    finder = ShortestPathFinder(config_path=args.config)
    
    try:
        # List nodes if requested
        if args.list_nodes:
            print(f"\n📋 Sample {args.list_nodes} nodes:")
            print("-" * 80)
            nodes = finder.list_sample_nodes(node_type=args.list_nodes, limit=20)
            for node in nodes:
                print(f"  • {node['name']} (ID: {node['id']}, Type: {node['label']})")
            return
        
        # Require both nodes
        if not args.node1 or not args.node2:
            print("❌ Error: Both --node1 and --node2 are required")
            print("\nUsage examples:")
            print("  python test_shortest_path.py --node1 'Taylor Swift' --node2 'Ed Sheeran'")
            print("  python test_shortest_path.py --node1 artist_123 --node2 artist_456")
            print("  python test_shortest_path.py --list-nodes Artist")
            return
        
        # Find nodes
        logger.info(f"Looking for node 1: {args.node1}")
        if args.node1.startswith(('artist_', 'album_', 'band_', 'song_', 'genre_', 'award_', 'recordlabel_')):
            node1 = finder.find_node_by_id(args.node1)
        else:
            node1 = finder.find_node_by_name(args.node1, args.type1)
        
        if not node1:
            print(f"❌ Node 1 not found: {args.node1}")
            return
        
        logger.info(f"Found node 1: {node1['name']} ({node1['label']}, ID: {node1['id']})")
        
        logger.info(f"Looking for node 2: {args.node2}")
        if args.node2.startswith(('artist_', 'album_', 'band_', 'song_', 'genre_', 'award_', 'recordlabel_')):
            node2 = finder.find_node_by_id(args.node2)
        else:
            node2 = finder.find_node_by_name(args.node2, args.type2)
        
        if not node2:
            print(f"❌ Node 2 not found: {args.node2}")
            return
        
        logger.info(f"Found node 2: {node2['name']} ({node2['label']}, ID: {node2['id']})")
        
        # Find shortest path(s)
        if args.all_paths:
            logger.info("Finding all shortest paths...")
            paths = finder.find_all_shortest_paths(
                node1['id'],
                node2['id'],
                max_depth=args.max_depth,
                relationship_types=args.relationships,
                max_paths=args.max_paths
            )
            print_all_paths(paths, node1['name'], node2['name'])
        else:
            logger.info("Finding shortest path...")
            result = finder.find_shortest_path(
                node1['id'],
                node2['id'],
                max_depth=args.max_depth,
                relationship_types=args.relationships
            )
            print_path_result(result, node1['name'], node2['name'])
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        finder.close()


if __name__ == "__main__":
    main()


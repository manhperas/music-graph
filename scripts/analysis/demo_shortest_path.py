#!/usr/bin/env python3
"""Demo script to test shortest path algorithm with example nodes"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test_shortest_path import ShortestPathFinder
from data_collection.utils import logger


def demo_shortest_path():
    """Demo shortest path finding"""
    print("=" * 80)
    print("DEMO: Shortest Path Algorithm Test")
    print("=" * 80)
    
    finder = ShortestPathFinder()
    
    try:
        # List some sample artists
        print("\n📋 Sample Artists in the graph:")
        print("-" * 80)
        artists = finder.list_sample_nodes(node_type='Artist', limit=10)
        
        if not artists:
            print("❌ No artists found. Make sure Neo4j is running and data is imported.")
            return
        
        for i, artist in enumerate(artists[:10], 1):
            print(f"  {i}. {artist['name']} (ID: {artist['id']})")
        
        # Try to find path between first two artists
        if len(artists) >= 2:
            node1_name = artists[0]['name']
            node2_name = artists[1]['name']
            node1_id = artists[0]['id']
            node2_id = artists[1]['id']
            
            print(f"\n🔍 Finding shortest path between:")
            print(f"   Node 1: {node1_name} (ID: {node1_id})")
            print(f"   Node 2: {node2_name} (ID: {node2_id})")
            print("-" * 80)
            
            # Find shortest path
            result = finder.find_shortest_path(
                node1_id,
                node2_id,
                max_depth=10
            )
            
            if result and result.get('path_exists'):
                print(f"\n✅ Path found! Length: {result['path_length']} relationships")
                print(f"\n📊 Path Details:")
                print("-" * 80)
                
                nodes = result['nodes']
                relationships = result['relationships']
                
                for i, node in enumerate(nodes):
                    print(f"\n[{i+1}] {node['label']}: {node['name']}")
                    print(f"    ID: {node['id']}")
                    
                    if i < len(relationships):
                        rel = relationships[i]
                        print(f"    └─[{rel['type']}]─→")
                
                # Try finding all shortest paths
                print(f"\n🔍 Finding all shortest paths...")
                all_paths = finder.find_all_shortest_paths(
                    node1_id,
                    node2_id,
                    max_depth=10,
                    max_paths=5
                )
                
                if len(all_paths) > 1:
                    print(f"\n✅ Found {len(all_paths)} shortest paths:")
                    for idx, path in enumerate(all_paths, 1):
                        print(f"\n--- Path {idx} (length: {path['path_length']}) ---")
                        for i, node in enumerate(path['nodes']):
                            print(f"  [{i+1}] {node['label']}: {node['name']}")
                            if i < len(path['relationships']):
                                rel = path['relationships'][i]
                                print(f"      └─[{rel['type']}]─→")
                else:
                    print(f"✅ Only 1 shortest path found")
            else:
                print(f"\n❌ No path found between {node1_name} and {node2_name}")
                print("   This might mean:")
                print("   - The nodes are in disconnected components")
                print("   - The path is longer than max_depth (10)")
                print("   - There are no relationships connecting these nodes")
        
        # Try with different relationship types
        if len(artists) >= 2:
            print("\n" + "=" * 80)
            print("🔍 Testing with COLLABORATES_WITH relationships only:")
            print("=" * 80)
            
            node1_id = artists[0]['id']
            node2_id = artists[1]['id']
            
            result = finder.find_shortest_path(
                node1_id,
                node2_id,
                max_depth=10,
                relationship_types=['COLLABORATES_WITH']
            )
            
            if result and result.get('path_exists'):
                print(f"✅ Path found via COLLABORATES_WITH! Length: {result['path_length']}")
                print("\nPath:")
                for i, node in enumerate(result['nodes']):
                    print(f"  [{i+1}] {node['name']} ({node['label']})")
            else:
                print("❌ No path found via COLLABORATES_WITH relationships")
        
        print("\n" + "=" * 80)
        print("Demo completed!")
        print("=" * 80)
        print("\n💡 Tip: Use test_shortest_path.py for more options:")
        print("   python scripts/analysis/test_shortest_path.py --node1 'Artist Name' --node2 'Another Artist'")
        print("   python scripts/analysis/test_shortest_path.py --list-nodes Artist")
        
    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)
    finally:
        finder.close()


if __name__ == "__main__":
    demo_shortest_path()


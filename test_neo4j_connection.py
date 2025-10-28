#!/usr/bin/env python3
"""
Test Neo4j connection script
Helps verify that local Neo4j is running and accessible
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from neo4j import GraphDatabase
from dotenv import load_dotenv
import json

def test_connection():
    """Test connection to Neo4j"""
    print("=" * 60)
    print("Neo4j Connection Test")
    print("=" * 60)
    print()
    
    # Load config
    config_path = "config/neo4j_config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✓ Loaded config from {config_path}")
        print(f"  URI: {config['uri']}")
        print(f"  User: {config['user']}")
        print(f"  Database: {config.get('database', 'neo4j')}")
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return False
    
    # Load password
    load_dotenv()
    password = os.getenv('NEO4J_PASS', 'password')
    print(f"  Password: {'*' * len(password)}")
    print()
    
    # Test connection
    print("Testing connection...")
    try:
        driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], password)
        )
        
        with driver.session(database=config.get('database', 'neo4j')) as session:
            # Test query
            result = session.run("RETURN 1 as test")
            record = result.single()
            
            if record['test'] == 1:
                print("✓ Connection successful!")
                print()
                
                # Get Neo4j version
                try:
                    version_result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
                    print("Neo4j Components:")
                    for record in version_result:
                        print(f"  • {record['name']}: {record['version']}")
                except:
                    print("  • Unable to get version info")
                
                print()
                
                # Count nodes
                try:
                    node_result = session.run("MATCH (n) RETURN count(n) as count")
                    node_count = node_result.single()['count']
                    print(f"Current database:")
                    print(f"  • Total nodes: {node_count}")
                    
                    if node_count > 0:
                        # Count by label
                        label_result = session.run("""
                            MATCH (n)
                            RETURN labels(n)[0] AS label, count(n) AS count
                            ORDER BY count DESC
                        """)
                        print(f"  • Nodes by label:")
                        for record in label_result:
                            print(f"    - {record['label']}: {record['count']}")
                    
                except Exception as e:
                    print(f"  • Unable to get node count: {e}")
                
                driver.close()
                return True
            else:
                print("✗ Connection test failed")
                driver.close()
                return False
                
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check if Neo4j is running:")
        print("     sudo systemctl status neo4j")
        print("  2. Check Neo4j Browser:")
        print("     http://localhost:7474")
        print("  3. Verify password in .env file")
        print("  4. Check config in config/neo4j_config.json")
        return False

if __name__ == "__main__":
    success = test_connection()
    print()
    print("=" * 60)
    if success:
        print("✓ All checks passed! Ready to import data.")
        print()
        print("Next steps:")
        print("  ./run.sh import    # Import data to Neo4j")
        print("  ./run.sh analyze   # Analyze and visualize")
    else:
        print("✗ Connection failed. Please fix the issues above.")
    print("=" * 60)
    sys.exit(0 if success else 1)


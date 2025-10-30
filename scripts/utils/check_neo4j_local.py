#!/usr/bin/env python3
"""
Kiểm tra Neo4j Local Connection
Có thể chạy với: uv run python check_neo4j_local.py
"""

import sys
import os
import json
from pathlib import Path

# Add src directory to path
src_dir = str(Path(__file__).parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: {e}")
    print("\nInstall dependencies:")
    print("  uv pip install neo4j python-dotenv")
    print("  hoặc")
    print("  pip install neo4j python-dotenv")
    print("\nSau đó chạy lại với:")
    print("  uv run python check_neo4j_local.py")
    sys.exit(1)


def check_local_neo4j():
    """Check Neo4j local connection"""
    print("=" * 60)
    print("CHECKING NEO4J LOCAL CONNECTION")
    print("=" * 60)
    
    # Load config
    config_path = "config/neo4j_config.json"
    if not os.path.exists(config_path):
        print(f"✗ Config file not found: {config_path}")
        return False
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"Config URI: {config['uri']}")
    print(f"User: {config['user']}")
    print(f"Database: {config.get('database', 'neo4j')}")
    
    # Load password
    load_dotenv()
    password = os.getenv('NEO4J_PASS', 'password')
    
    print(f"\nAttempting connection...")
    print(f"Password: {'*' * len(password)}")
    
    try:
        driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], password)
        )
        
        # Test connection
        with driver.session(database=config.get('database', 'neo4j')) as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record['test'] == 1:
                print("✓ Connection successful!")
        
        # Get Neo4j version
        with driver.session(database=config.get('database', 'neo4j')) as session:
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
            versions = [record.values() for record in result]
            if versions:
                print("\nNeo4j Components:")
                for name, version in versions:
                    print(f"  • {name}: {version}")
        
        # Check node counts
        print("\nCurrent database status:")
        with driver.session(database=config.get('database', 'neo4j')) as session:
            # Count nodes
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
                ORDER BY count DESC
            """)
            node_counts = [(record['label'], record['count']) for record in result]
            if node_counts:
                print("\nNode counts:")
                for label, count in node_counts:
                    print(f"  • {label}: {count}")
            else:
                print("  • Database is empty")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(r) AS count
                ORDER BY count DESC
            """)
            rel_counts = [(record['type'], record['count']) for record in result]
            if rel_counts:
                print("\nRelationship counts:")
                for rel_type, count in rel_counts:
                    print(f"  • {rel_type}: {count}")
            else:
                print("  • No relationships")
        
        driver.close()
        print("\n✓ Neo4j local connection is working!")
        print("\nNext steps:")
        print("  1. Run: uv run python src/main.py import")
        print("  2. Open Neo4j Browser: http://localhost:7474")
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check Neo4j is running:")
        print("     - Docker: docker-compose ps")
        print("     - Local: sudo systemctl status neo4j")
        print("     - Desktop: Check Neo4j Desktop app")
        print("  2. Check Neo4j Browser: http://localhost:7474")
        print("  3. Verify password in .env file")
        print("  4. Check config/neo4j_config.json")
        return False


if __name__ == "__main__":
    success = check_local_neo4j()
    sys.exit(0 if success else 1)


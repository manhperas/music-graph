#!/usr/bin/env python3
"""Clear Neo4j database"""

from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv

def clear_database():
    """Clear all nodes and relationships from Neo4j"""
    load_dotenv()
    
    # Load config
    with open('config/neo4j_config.json', 'r') as f:
        config = json.load(f)
    
    # Get password from environment
    password = os.getenv('NEO4J_PASS', 'password')
    
    try:
        driver = GraphDatabase.driver(config['uri'], auth=(config['user'], password))
        with driver.session() as session:
            # Get node counts before deletion
            result = session.run('MATCH (n) RETURN count(n) as count')
            count = result.single()['count']
            
            if count > 0:
                print(f"Found {count} nodes. Deleting...")
                session.run('MATCH (n) DETACH DELETE n')
                print('✓ Neo4j database cleared successfully')
            else:
                print('✓ Database is already empty')
        driver.close()
    except Exception as e:
        print(f'❌ Error clearing Neo4j: {e}')
        print('   Make sure Neo4j is running and credentials are correct')
        return False
    
    return True

if __name__ == "__main__":
    clear_database()

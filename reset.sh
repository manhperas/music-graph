#!/bin/bash

# Reset script for Music Network Pop US-UK project
# This script will clean all data and reset Neo4j (Local installation)

set -e  # Exit on error

echo "=========================================="
echo "Music Network Pop US-UK - Reset (Local Neo4j)"
echo "=========================================="
echo ""

# Ask for confirmation
read -p "⚠️  This will delete ALL data. Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Reset cancelled."
    exit 0
fi

echo ""
echo "Starting reset process..."

# Clean data folders
echo ""
echo "1. Cleaning data folders..."
rm -rf data/raw/*
rm -rf data/processed/*
mkdir -p data/raw
mkdir -p data/processed/figures
mkdir -p data/processed/filtered

# Clean logs
echo "2. Cleaning logs..."
rm -f data_collection.log
rm -f src/data_collection.log
rm -f *.log

# Clear Neo4j database
echo "3. Clearing Neo4j database..."
python3 -c "
from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Load config
with open('config/neo4j_config.json', 'r') as f:
    config = json.load(f)

# Get password from environment
password = os.getenv('NEO4J_PASS', 'password')

try:
    driver = GraphDatabase.driver(config['uri'], auth=(config['user'], password))
    with driver.session() as session:
        # Delete all nodes and relationships
        session.run('MATCH (n) DETACH DELETE n')
        print('✓ Neo4j database cleared')
    driver.close()
except Exception as e:
    print(f'⚠️  Error clearing Neo4j: {e}')
    print('   Make sure Neo4j is running and credentials are correct')
" || echo "⚠️  Warning: Could not clear Neo4j database (might be already empty or not running)"

echo ""
echo "=========================================="
echo "Reset Complete!"
echo "=========================================="
echo ""
echo "Data has been cleaned and Neo4j has been reset."
echo ""
echo "Next steps:"
echo "  Run: uv run python src/main.py all"
echo "  Or run individual stages:"
echo "    uv run python src/main.py collect   # Collect data from Wikipedia"
echo "    uv run python src/main.py process   # Process and clean data"
echo "    uv run python src/main.py build     # Build graph network"
echo "    uv run python src/main.py import    # Import to Neo4j"
echo "    uv run python src/main.py analyze   # Analyze and visualize"
echo ""


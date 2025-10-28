#!/bin/bash

# Run script for Music Network Pop US-UK project
# Usage: ./run.sh <command> [options]

set -e  # Exit on error

# Check if virtual environment exists (venv or .venv)
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./setup.sh first or use uv venv"
    exit 1
fi

# Try to activate virtual environment (support both venv and .venv)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if command provided
if [ $# -eq 0 ]; then
    echo "Usage: ./run.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  collect   - Collect data from Wikipedia"
    echo "  process   - Process and clean collected data"
    echo "  build     - Build graph network"
    echo "  import    - Import data to Neo4j"
    echo "  analyze   - Analyze network and create visualizations"
    echo "  all       - Run complete pipeline"
    echo ""
    echo "Examples:"
    echo "  ./run.sh collect"
    echo "  ./run.sh all"
    echo "  ./run.sh analyze --config config/neo4j_config.json"
    exit 1
fi

# Run main.py with all arguments
# Run as module from root directory  
python3 -m src.main "$@"



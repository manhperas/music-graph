#!/bin/bash

# Setup script for Music Network Pop US-UK project
# This script sets up the environment and starts Neo4j

set -e  # Exit on error

echo "=========================================="
echo "Music Network Pop US-UK - Setup"
echo "=========================================="
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not found"
    exit 1
fi
echo "✓ Found pip3"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker not found. You'll need Docker to run Neo4j"
    echo "Install Docker: https://docs.docker.com/engine/install/"
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Warning: docker-compose not found"
    echo "Install docker-compose: https://docs.docker.com/compose/install/"
fi

echo ""
echo "Setting up Python virtual environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Created virtual environment"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1
echo "✓ Upgraded pip"

# Install requirements
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ All dependencies installed"
else
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Neo4j Configuration
NEO4J_PASS=password
EOF
    echo "✓ Created .env file with default password"
    echo "  You can edit .env to change the Neo4j password"
else
    echo "✓ .env file already exists"
fi

# Start Neo4j with Docker Compose
echo ""
echo "Starting Neo4j database..."

if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo "✓ Neo4j started successfully"
        echo ""
        echo "Neo4j is now running:"
        echo "  • Browser: http://localhost:7474"
        echo "  • Bolt: bolt://localhost:7687"
        echo "  • Username: neo4j"
        echo "  • Password: password (or your .env value)"
        echo ""
        echo "Waiting for Neo4j to be ready (this may take 10-20 seconds)..."
        sleep 15
        echo "✓ Neo4j should be ready now"
    else
        echo "Error: Failed to start Neo4j"
        exit 1
    fi
else
    echo "⚠ Docker Compose not available, skipping Neo4j startup"
    echo "  You'll need to start Neo4j manually"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the pipeline: ./run.sh all"
echo "  or run individual stages:"
echo "    ./run.sh collect   # Collect data from Wikipedia"
echo "    ./run.sh process   # Process and clean data"
echo "    ./run.sh build     # Build graph network"
echo "    ./run.sh import    # Import to Neo4j"
echo "    ./run.sh analyze   # Analyze and visualize"
echo ""



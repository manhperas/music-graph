# Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Navigate to project directory
cd music-network-pop-us-uk

# 2. Create .env file with Neo4j password
echo "NEO4J_PASS=password" > .env

# 3. Run setup script
./setup.sh
```

## Run Complete Pipeline (30-60 minutes)

```bash
./run.sh all
```

## Or Run Individual Stages

```bash
# Collect data from Wikipedia (~15 minutes)
./run.sh collect

# Process and clean data (~2 minutes)
./run.sh process

# Build graph network (~1 minute)
./run.sh build

# Import to Neo4j (~2 minutes)
./run.sh import

# Analyze and visualize (~3 minutes)
./run.sh analyze
```

## View Results

### Neo4j Browser
- URL: http://localhost:7474
- Username: `neo4j`
- Password: `password`

### Sample Cypher Queries

```cypher
// Count nodes by type
MATCH (n) 
RETURN labels(n)[0] AS type, count(n) AS count

// Top 10 connected artists
MATCH (a:Artist)-[r]-()
WITH a, count(r) AS degree
ORDER BY degree DESC
LIMIT 10
RETURN a.name, degree

// Find collaborations (artists sharing albums)
MATCH (a1:Artist)-[:PERFORMS_ON]->(album:Album)<-[:PERFORMS_ON]-(a2:Artist)
WHERE id(a1) < id(a2)
RETURN a1.name, a2.name, album.title
LIMIT 20
```

### Generated Files

- **Statistics**: `data/processed/stats.json`
- **Network Graph**: `data/processed/network.graphml`
- **Visualizations**: `data/processed/figures/*.png`
  - degree_distribution.png
  - network_sample.png
  - genre_distribution.png
  - top_artists.png
  - pagerank.png

## Project Commands

```bash
# Help
./run.sh

# Run with custom config
./run.sh collect --config config/wikipedia_config.json
./run.sh import --config config/neo4j_config.json

# Import without clearing database
./run.sh import --no-clear
```

## Troubleshooting

### Neo4j won't start
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f neo4j
```

### Connection refused
Wait 15-20 seconds after starting Neo4j, then retry.

### Python module errors
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Clean and restart
```bash
# Remove all data
rm -rf data/

# Stop Neo4j
docker-compose down

# Restart everything
./setup.sh
./run.sh all
```

## Customization

### Collect more/fewer artists

Edit `config/wikipedia_config.json`:
```json
{
  "max_artists": 2000  // Increase this
}
```

### Add more categories

Edit `config/wikipedia_config.json`:
```json
{
  "categories": [
    "Danh sách nghệ sĩ nhạc pop Mỹ",
    "Nhạc pop Anh",
    "Your new category here"
  ]
}
```

### Change Neo4j password

1. Edit `.env`:
```bash
NEO4J_PASS=your_new_password
```

2. Edit `config/neo4j_config.json` if needed

3. Restart Neo4j:
```bash
docker-compose down
docker-compose up -d
```

## Expected Output

After running `./run.sh all`:

```
==========================================
STAGE 1: DATA COLLECTION
==========================================
Loaded configuration from config/wikipedia_config.json
Found 1000+ unique artists to collect
✓ Successfully collected 1000+ artists

==========================================
STAGE 2: DATA PROCESSING
==========================================
Parsed 1000+ artists
Cleaned data: 1000+ artists remaining
✓ Data processing complete

==========================================
STAGE 3: GRAPH BUILDING
==========================================
Added 1000+ artist nodes to graph
Added 500+ album nodes
✓ Built graph with 1500+ nodes

==========================================
STAGE 4: NEO4J IMPORT
==========================================
Imported 1000+ artists
Imported 500+ albums
Imported 2000+ relationships
✓ Successfully imported data to Neo4j

==========================================
STAGE 5: NETWORK ANALYSIS
==========================================
Computing network statistics...
Creating visualizations...
✓ Analysis complete

NETWORK SUMMARY
==========================================
Nodes:
  • Artist: 1000+
  • Album: 500+

Relationships:
  • PERFORMS_ON: 2000+

Degree Statistics:
  • Average: 2-5
  • Max: 20-50+

Top 5 Connected Artists:
  [List of artists]
```

## File Locations

```
music-network-pop-us-uk/
├── Raw data:        data/raw/artists.json
├── Processed:       data/processed/nodes.csv
├── Graph:           data/processed/network.graphml
├── Statistics:      data/processed/stats.json
├── Visualizations:  data/processed/figures/*.png
└── Logs:            data_collection.log
```


# Music Network Pop US-UK

A comprehensive graph network analysis project that scrapes Wikipedia Vietnamese pages for US-UK pop musicians and singers, builds a collaboration network, imports it to Neo4j, and performs statistical analysis and visualization.

## 🔗 Repository

**GitHub**: https://github.com/[username]/music-network-pop-us-uk

```bash
git clone https://github.com/[username]/music-network-pop-us-uk.git
cd music-network-pop-us-uk
```

## 🎯 Project Overview

This project collects data about pop music artists from the United States and United Kingdom using Vietnamese Wikipedia pages. It extracts artist information including genres, instruments, active years, and album/song data, then builds a graph network where:

- **Nodes**: Artists and Albums/Songs
- **Edges**: Artist-[:PERFORMS_ON]->Album/Song relationships (collaborations)

The network is imported into Neo4j for graph database analysis and visualized using NetworkX and Matplotlib.

## 📊 Key Features

- **Data Collection**: Automated scraping of 1000+ artists from Wikipedia Vietnamese categories
- **Data Processing**: Parse infobox data, clean and normalize artist information
- **Graph Building**: Create network with artists as nodes, shared albums as collaboration edges
- **Neo4j Integration**: Import graph to Neo4j with proper constraints and indexes
- **Network Analysis**: Compute degree statistics, PageRank, and genre distributions
- **Visualization**: Generate degree distributions, network plots, and top artists charts

## 🛠 Technology Stack

- **Python 3.10+**: Core programming language
- **wikipedia-api**: Wikipedia data retrieval
- **mwparserfromhell**: MediaWiki wikitext parsing
- **pandas**: Data cleaning and transformation
- **networkx**: Graph building and analysis
- **neo4j**: Graph database driver
- **matplotlib**: Data visualization
- **Docker**: Neo4j containerization

## 📁 Project Structure

```
music-network-pop-us-uk/
├── README.md                              # This file
├── TEAM_CONTRIBUTION_TEMPLATE.md          # Team contribution and work allocation
├── LIMITATIONS_AND_FUTURE_WORK.md         # Project limitations and future work
├── requirements.txt                       # Python dependencies
├── setup.sh                               # Setup script (install deps, start Neo4j)
├── run.sh                                 # Run pipeline stages
├── docker-compose.yml                     # Neo4j Docker configuration
├── .env                                   # Environment variables (create from .env.example)
├── .gitignore                             # Git ignore rules
│
├── config/
│   ├── wikipedia_config.json              # Wikipedia scraping configuration
│   └── neo4j_config.json                  # Neo4j connection settings
│
├── docs/                                  # Documentation (organized by category)
│   ├── README.md                          # Documentation index
│   ├── guides/                            # User guides and instructions
│   ├── analysis/                          # Analysis reports
│   ├── implementation/                    # Implementation details
│   └── technical/                         # Technical documentation
│
├── src/
│   ├── main.py                            # Main entry point with CLI
│   ├── data_collection/                   # Wikipedia scraping modules
│   │   ├── scraper.py                     # Article and infobox scraper
│   │   └── utils.py                       # Logging and rate limiting
│   ├── data_processing/                   # Data parsing and cleaning
│   │   ├── parser.py                      # Infobox parser
│   │   └── cleaner.py                     # Data cleaning and filtering
│   ├── graph_building/                    # Graph construction and import
│   │   ├── builder.py                     # NetworkX graph builder
│   │   └── importer.py                    # Neo4j importer
│   └── analysis/                          # Analysis and visualization
│       ├── stats.py                       # Network statistics
│       ├── communities.py                 # Community detection
│       ├── paths.py                       # Path analysis
│       └── viz.py                         # Visualization generation
│
└── data/                                  # Data directory (gitignored)
    ├── raw/                               # Raw scraped data
    │   └── artists.json
    └── processed/                         # Processed data and outputs
        ├── nodes.csv
        ├── edges.csv
        ├── albums.csv
        ├── artists.csv
        ├── network.graphml
        ├── stats.json
        └── figures/                       # Generated visualizations
            ├── degree_distribution.png
            ├── network_sample.png
            ├── genre_distribution.png
            ├── top_artists.png
            └── pagerank.png
```

## 📚 Documentation

All project documentation is organized in the `docs/` directory:

- **User Guides** (`docs/guides/`): How to run the project, quick start guides
- **Analysis** (`docs/analysis/`): Community detection and network analysis reports
- **Implementation** (`docs/implementation/`): Implementation details and improvements
- **Technical** (`docs/technical/`): Graph relationships, queries, and technical details

See [docs/README.md](docs/README.md) for complete documentation index.

## 🚀 Quick Start

### Prerequisites

- Linux operating system
- Python 3.10 or higher
- Docker and Docker Compose
- Internet connection for Wikipedia scraping

### Installation

1. **Clone or download this project**

```bash
cd music-network-pop-us-uk
```

2. **Create environment file**

```bash
cat > .env << EOF
NEO4J_PASS=password
EOF
```

3. **Run setup script**

```bash
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Start Neo4j in Docker (accessible at http://localhost:7474)

For detailed instructions, see [docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md) or [docs/guides/HOW_TO_RUN.md](docs/guides/HOW_TO_RUN.md).

### Running the Pipeline

#### Option 1: Run Complete Pipeline

```bash
./run.sh all
```

This runs all stages in sequence:
1. Collect data from Wikipedia
2. Process and clean data
3. Build graph network
4. Import to Neo4j
5. Analyze and visualize

#### Option 2: Run Individual Stages

```bash
# Stage 1: Collect data from Wikipedia
./run.sh collect

# Stage 2: Process collected data
./run.sh process

# Stage 3: Build graph network
./run.sh build

# Stage 4: Import to Neo4j
./run.sh import

# Stage 5: Analyze and visualize
./run.sh analyze
```

### Viewing Results

**Neo4j Browser:**
- Open http://localhost:7474 in your browser
- Username: `neo4j`
- Password: `password` (or your custom password from .env)

**Query Examples:**

```cypher
// Count all nodes
MATCH (n) RETURN labels(n), count(n)

// Find top connected artists
MATCH (a:Artist)-[r]-()
WITH a, count(r) AS degree
ORDER BY degree DESC
LIMIT 10
RETURN a.name, degree

// Find artists by genre
MATCH (a:Artist)
WHERE a.genres CONTAINS 'pop'
RETURN a.name, a.genres
LIMIT 10
```

**Generated Files:**
- Statistics: `data/processed/stats.json`
- Visualizations: `data/processed/figures/*.png`
- Network graph: `data/processed/network.graphml`

## 📋 Configuration

### Wikipedia Configuration (`config/wikipedia_config.json`)

```json
{
  "categories": [
    "Danh sách nghệ sĩ nhạc pop Mỹ",
    "Nhạc pop Anh"
  ],
  "max_artists": 1000,
  "language": "vi",
  "rate_limit_delay": 1.0,
  "recursive_depth": 3
}
```

- `categories`: Wikipedia Vietnamese categories to scrape
- `max_artists`: Maximum number of artists to collect
- `language`: Wikipedia language code
- `rate_limit_delay`: Delay between requests (seconds)
- `recursive_depth`: How deep to traverse subcategories

### Neo4j Configuration (`config/neo4j_config.json`)

```json
{
  "uri": "bolt://localhost:7687",
  "user": "neo4j",
  "database": "neo4j"
}
```

## 🔧 Troubleshooting

### Neo4j Connection Issues

If you get connection errors:

1. Check Neo4j is running:
```bash
docker-compose ps
```

2. Restart Neo4j:
```bash
docker-compose restart
```

3. Check logs:
```bash
docker-compose logs neo4j
```

### Rate Limiting

If Wikipedia blocks your requests:
- Increase `rate_limit_delay` in config
- Reduce `max_artists` for testing
- Wait a few minutes before retrying

### Memory Issues

For large datasets:
- Increase Docker memory limits in `docker-compose.yml`
- Process data in smaller batches
- Reduce `max_artists` in configuration

## 📊 Expected Results

After running the complete pipeline, you should have:

- **~1000+ artist nodes** from US and UK pop music categories
- **~500+ album nodes** representing shared albums
- **~2000+ relationships** connecting artists to albums
- **Network statistics** including degree distribution, PageRank rankings
- **5 visualizations** showing network structure and key metrics

## 🤝 Contributing

This is an academic assignment project. For improvements:

1. Modify configuration files for different categories
2. Extend parsers to extract more infobox fields
3. Add new analysis metrics in `src/analysis/stats.py`
4. Create additional visualizations in `src/analysis/viz.py`

## 📝 License

This project is for educational purposes. Wikipedia data is used under Creative Commons licensing.

## 👤 Author

Manh Nguyen - Graph Network Analysis Assignment

## 🙏 Acknowledgments

- Wikipedia Vietnamese community for maintaining artist pages
- Neo4j for the graph database platform
- Python community for excellent libraries

---

**Note**: Data collection may take 15-30 minutes depending on network speed and Wikipedia response times. The complete pipeline typically takes 30-60 minutes to run.



"""
Main entry point for the Music Network Pop US-UK project
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add src directory to path
src_dir = str(Path(__file__).parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from data_collection import scrape_all
from data_processing import parse_all, clean_all
from graph_building import build_graph, import_to_neo4j
from analysis import compute_stats, create_visualizations
from data_collection.utils import logger


def collect_data(args):
    """Run data collection from Wikipedia"""
    logger.info("=" * 60)
    logger.info("STAGE 1: DATA COLLECTION")
    logger.info("=" * 60)
    
    config_path = args.config or "config/wikipedia_config.json"
    output_path = "data/raw/artists.json"
    
    try:
        count = scrape_all(config_path, output_path)
        logger.info(f"✓ Successfully collected {count} artists")
        return True
    except Exception as e:
        logger.error(f"✗ Data collection failed: {e}")
        return False


def process_data(args):
    """Run data processing (parsing and cleaning)"""
    logger.info("=" * 60)
    logger.info("STAGE 2: DATA PROCESSING")
    logger.info("=" * 60)
    
    try:
        # Parse infoboxes
        logger.info("Parsing artist infoboxes...")
        parsed_count = parse_all(
            input_path="data/raw/artists.json",
            output_path="data/processed/parsed_artists.json"
        )
        logger.info(f"✓ Parsed {parsed_count} artists")
        
        # Clean and filter data
        logger.info("Cleaning and filtering data...")
        clean_count = clean_all(
            input_path="data/processed/parsed_artists.json",
            nodes_output="data/processed/nodes.csv",
            albums_output="data/processed/albums.json"
        )
        logger.info(f"✓ Cleaned data: {clean_count} artists ready")
        
        return True
    except Exception as e:
        logger.error(f"✗ Data processing failed: {e}")
        return False


def build_network(args):
    """Build graph network"""
    logger.info("=" * 60)
    logger.info("STAGE 3: GRAPH BUILDING")
    logger.info("=" * 60)
    
    try:
        # Check if genre files exist
        genres_path = "data/migrations/genres.csv" if os.path.exists("data/migrations/genres.csv") else None
        has_genre_path = "data/migrations/has_genre_relationships.csv" if os.path.exists("data/migrations/has_genre_relationships.csv") else None
        
        # Check if band classifications exist
        band_classifications_path = "data/processed/band_classifications.json" if os.path.exists("data/processed/band_classifications.json") else None
        
        # Check if songs file exists
        songs_path = "data/processed/songs.csv" if os.path.exists("data/processed/songs.csv") else None
        
        # Check if awards files exist
        awards_csv_path = "data/processed/awards.csv" if os.path.exists("data/processed/awards.csv") else None
        awards_json_path = "data/processed/awards.json" if os.path.exists("data/processed/awards.json") else None
        
        if genres_path:
            logger.info(f"✓ Found genres file: {genres_path}")
        if has_genre_path:
            logger.info(f"✓ Found HAS_GENRE relationships: {has_genre_path}")
        if band_classifications_path:
            logger.info(f"✓ Found band classifications: {band_classifications_path}")
        if songs_path:
            logger.info(f"✓ Found songs file: {songs_path}")
        if awards_csv_path:
            logger.info(f"✓ Found awards CSV: {awards_csv_path}")
        if awards_json_path:
            logger.info(f"✓ Found awards JSON: {awards_json_path}")
        
        node_count = build_graph(
            nodes_path="data/processed/nodes.csv",
            albums_path="data/processed/albums.json",
            output_dir="data/processed",
            genres_path=genres_path,
            has_genre_path=has_genre_path,
            band_classifications_path=band_classifications_path,
            songs_path=songs_path,
            awards_csv_path=awards_csv_path,
            awards_json_path=awards_json_path
        )
        logger.info(f"✓ Built graph with {node_count} nodes")
        return True
    except Exception as e:
        logger.error(f"✗ Graph building failed: {e}")
        return False


def import_data(args):
    """Import data to Neo4j"""
    logger.info("=" * 60)
    logger.info("STAGE 4: NEO4J IMPORT")
    logger.info("=" * 60)
    
    config_path = args.config or "config/neo4j_config.json"
    
    try:
        import_to_neo4j(
            data_dir="data/processed",
            config_path=config_path,
            clear_first=not args.no_clear
        )
        logger.info("✓ Successfully imported data to Neo4j")
        return True
    except Exception as e:
        logger.error(f"✗ Neo4j import failed: {e}")
        logger.error("Make sure Neo4j is running: docker-compose up -d")
        return False


def analyze_network(args):
    """Analyze network and create visualizations"""
    logger.info("=" * 60)
    logger.info("STAGE 5: NETWORK ANALYSIS")
    logger.info("=" * 60)
    
    config_path = args.config or "config/neo4j_config.json"
    
    try:
        # Compute statistics
        logger.info("Computing network statistics...")
        stats = compute_stats(
            config_path=config_path,
            output_path="data/processed/stats.json"
        )
        logger.info("✓ Statistics computed")
        
        # Create visualizations
        logger.info("Creating visualizations...")
        create_visualizations(
            graph_path="data/processed/network.graphml",
            stats_path="data/processed/stats.json",
            output_dir="data/processed/figures"
        )
        logger.info("✓ Visualizations created")
        
        # Print summary
        print_summary(stats)
        
        return True
    except Exception as e:
        logger.error(f"✗ Analysis failed: {e}")
        return False


def run_all(args):
    """Run complete pipeline"""
    logger.info("=" * 60)
    logger.info("RUNNING COMPLETE PIPELINE")
    logger.info("=" * 60)
    
    stages = [
        ("collect", collect_data),
        ("process", process_data),
        ("build", build_network),
        ("import", import_data),
        ("analyze", analyze_network)
    ]
    
    for stage_name, stage_func in stages:
        logger.info(f"\nStarting stage: {stage_name}")
        success = stage_func(args)
        
        if not success:
            logger.error(f"Pipeline failed at stage: {stage_name}")
            return False
        
        logger.info(f"Stage {stage_name} completed successfully\n")
    
    logger.info("=" * 60)
    logger.info("✓ COMPLETE PIPELINE FINISHED SUCCESSFULLY")
    logger.info("=" * 60)
    return True


def print_summary(stats: dict):
    """Print summary of network statistics"""
    print("\n" + "=" * 60)
    print("NETWORK SUMMARY")
    print("=" * 60)
    
    # Node counts
    node_counts = stats.get('node_counts', {})
    print(f"\nNodes:")
    for label, count in node_counts.items():
        print(f"  • {label}: {count}")
    
    # Edge counts
    edge_counts = stats.get('edge_counts', {})
    print(f"\nRelationships:")
    for rel_type, count in edge_counts.items():
        print(f"  • {rel_type}: {count}")
    
    # Degree stats
    degree_stats = stats.get('degree_stats', {})
    if degree_stats:
        print(f"\nDegree Statistics:")
        print(f"  • Average: {degree_stats.get('avg_degree', 0):.2f}")
        print(f"  • Median: {degree_stats.get('median_degree', 0):.2f}")
        print(f"  • Max: {degree_stats.get('max_degree', 0)}")
    
    # Top artists
    top_connected = stats.get('top_connected', [])[:5]
    if top_connected:
        print(f"\nTop 5 Connected Artists:")
        for i, artist in enumerate(top_connected, 1):
            print(f"  {i}. {artist['name']}: {artist['degree']} connections")
    
    # Top collaborators
    top_collaborators = stats.get('top_collaborators', [])[:5]
    if top_collaborators:
        print(f"\nTop 5 Collaborating Artists:")
        for i, artist in enumerate(top_collaborators, 1):
            collab_count = artist['collaborations']
            shared = artist.get('total_shared_albums', 0)
            print(f"  {i}. {artist['name']}: {collab_count} collaborations ({shared} shared albums)")
    
    # Strongest collaborations
    strongest = stats.get('strongest_collaborations', [])[:5]
    if strongest:
        print(f"\nTop 5 Strongest Artist Collaborations:")
        for i, collab in enumerate(strongest, 1):
            print(f"  {i}. {collab['artist1']} ↔ {collab['artist2']}: {collab['shared_albums']} shared albums")
    
    # PageRank
    top_pagerank = stats.get('top_pagerank', [])[:5]
    if top_pagerank:
        print(f"\nTop 5 Artists by PageRank:")
        for i, artist in enumerate(top_pagerank, 1):
            print(f"  {i}. {artist['name']}: {artist['pagerank']:.6f}")
    
    print("\n" + "=" * 60)


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Music Network Pop US-UK: Graph network analysis of pop musicians',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py collect              # Collect data from Wikipedia
  python main.py process              # Process collected data
  python main.py build                # Build graph network
  python main.py import               # Import to Neo4j
  python main.py analyze              # Analyze and visualize
  python main.py all                  # Run complete pipeline
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect data from Wikipedia')
    collect_parser.add_argument('--config', help='Path to Wikipedia config file')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process collected data')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build graph network')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import data to Neo4j')
    import_parser.add_argument('--config', help='Path to Neo4j config file')
    import_parser.add_argument('--no-clear', action='store_true', 
                              help='Do not clear database before import')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze network and create visualizations')
    analyze_parser.add_argument('--config', help='Path to Neo4j config file')
    
    # All command
    all_parser = subparsers.add_parser('all', help='Run complete pipeline')
    all_parser.add_argument('--config', help='Path to config file')
    all_parser.add_argument('--no-clear', action='store_true',
                           help='Do not clear database before import')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Map commands to functions
    commands = {
        'collect': collect_data,
        'process': process_data,
        'build': build_network,
        'import': import_data,
        'analyze': analyze_network,
        'all': run_all
    }
    
    func = commands.get(args.command)
    if func:
        success = func(args)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()


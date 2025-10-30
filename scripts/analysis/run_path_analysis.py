#!/usr/bin/env python3
"""Run shortest path analysis on the music network"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analysis.paths import analyze_paths
from data_collection.utils import logger


def main():
    """Run path analysis"""
    logger.info("=" * 60)
    logger.info("SHORTEST PATH ANALYSIS")
    logger.info("=" * 60)
    
    # Run path analysis
    results = analyze_paths(
        graph_path="data/processed/network.graphml",
        output_path="data/processed/path_analysis.json"
    )
    
    # Print summary
    if results:
        logger.info("\n" + "=" * 60)
        logger.info("PATH ANALYSIS RESULTS")
        logger.info("=" * 60)
        
        if 'average_path_length' in results and results['average_path_length']:
            logger.info(f"Average Shortest Path Length: {results['average_path_length']:.2f}")
        
        if 'diameter_radius' in results:
            diam = results['diameter_radius']
            logger.info(f"Network Diameter: {diam.get('diameter', 'N/A')}")
            logger.info(f"Network Radius: {diam.get('radius', 'N/A')}")
            logger.info(f"Largest Component Size: {diam.get('component_size', 'N/A')}")
        
        if 'sample_paths' in results:
            sample = results['sample_paths']
            logger.info(f"\nSample Path Analysis:")
            logger.info(f"  Pairs analyzed: {sample.get('num_pairs_analyzed', 0)}")
            logger.info(f"  Paths found: {sample.get('num_paths_found', 0)}")
            if sample.get('avg_path_length'):
                logger.info(f"  Average path length: {sample['avg_path_length']:.2f}")
                logger.info(f"  Min/Max path length: {sample.get('min_path_length')}/{sample.get('max_path_length')}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Analysis complete! Results saved to data/processed/path_analysis.json")
        logger.info("=" * 60)
    else:
        logger.error("No results returned from analysis")


if __name__ == "__main__":
    main()


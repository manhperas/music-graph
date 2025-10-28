"""Network visualization module"""

import json
import os
from typing import Dict, List, Optional
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from data_collection.utils import logger


class NetworkVisualizer:
    """Create visualizations of the network"""
    
    def __init__(self, output_dir: str = "data/processed/figures"):
        """Initialize visualizer"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('default')
    
    def load_graph(self, graph_path: str) -> nx.Graph:
        """Load graph from file"""
        try:
            graph = nx.read_graphml(graph_path)
            logger.info(f"Loaded graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
            return graph
        except Exception as e:
            logger.error(f"Error loading graph: {e}")
            return nx.Graph()
    
    def load_stats(self, stats_path: str) -> Dict:
        """Load statistics from file"""
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            logger.info(f"Loaded statistics from {stats_path}")
            return stats
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            return {}
    
    def plot_degree_distribution(self, graph: nx.Graph):
        """Plot degree distribution histogram"""
        try:
            degrees = [d for n, d in graph.degree()]
            
            plt.figure(figsize=(10, 6))
            plt.hist(degrees, bins=50, edgecolor='black', alpha=0.7)
            plt.xlabel('Degree', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.title('Degree Distribution of Music Network', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            
            output_path = os.path.join(self.output_dir, 'degree_distribution.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved degree distribution plot to {output_path}")
            
        except Exception as e:
            logger.error(f"Error plotting degree distribution: {e}")
    
    def plot_network_sample(self, graph: nx.Graph, sample_size: int = 100):
        """Plot a sample of the network"""
        try:
            # Get artist nodes only
            artist_nodes = [n for n, d in graph.nodes(data=True) 
                          if d.get('node_type') == 'Artist']
            
            # Sample if too large
            if len(artist_nodes) > sample_size:
                # Get highest degree nodes
                degrees = [(n, graph.degree(n)) for n in artist_nodes]
                degrees.sort(key=lambda x: x[1], reverse=True)
                sample_nodes = [n for n, d in degrees[:sample_size]]
            else:
                sample_nodes = artist_nodes
            
            # Create subgraph
            subgraph = graph.subgraph(sample_nodes)
            
            # Plot
            plt.figure(figsize=(14, 10))
            
            # Calculate layout
            pos = nx.spring_layout(subgraph, k=0.5, iterations=50, seed=42)
            
            # Draw nodes
            nx.draw_networkx_nodes(
                subgraph, pos,
                node_color='lightblue',
                node_size=300,
                alpha=0.7
            )
            
            # Draw edges
            nx.draw_networkx_edges(
                subgraph, pos,
                alpha=0.2,
                width=1
            )
            
            # Draw labels for high-degree nodes
            high_degree_nodes = [n for n in subgraph.nodes() if subgraph.degree(n) > 3]
            labels = {n: subgraph.nodes[n].get('name', '')[:20] for n in high_degree_nodes}
            nx.draw_networkx_labels(
                subgraph, pos,
                labels=labels,
                font_size=8
            )
            
            plt.title(f'Music Network Visualization (Top {len(sample_nodes)} Artists)', 
                     fontsize=14, fontweight='bold')
            plt.axis('off')
            
            output_path = os.path.join(self.output_dir, 'network_sample.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved network sample plot to {output_path}")
            
        except Exception as e:
            logger.error(f"Error plotting network sample: {e}")
    
    def plot_genre_distribution(self, stats: Dict):
        """Plot genre distribution bar chart"""
        try:
            genre_dist = stats.get('genre_distribution', {})
            
            if not genre_dist:
                logger.warning("No genre distribution data available")
                return
            
            # Prepare data
            genres = list(genre_dist.keys())[:15]  # Top 15
            counts = [genre_dist[g] for g in genres]
            
            # Truncate long genre names
            genres = [g[:30] + '...' if len(g) > 30 else g for g in genres]
            
            plt.figure(figsize=(12, 8))
            plt.barh(genres, counts, color='steelblue', alpha=0.7)
            plt.xlabel('Number of Artists', fontsize=12)
            plt.ylabel('Genre', fontsize=12)
            plt.title('Genre Distribution in Music Network', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='x')
            
            output_path = os.path.join(self.output_dir, 'genre_distribution.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved genre distribution plot to {output_path}")
            
        except Exception as e:
            logger.error(f"Error plotting genre distribution: {e}")
    
    def plot_top_artists(self, stats: Dict):
        """Plot top connected artists"""
        try:
            top_connected = stats.get('top_connected', [])
            
            if not top_connected:
                logger.warning("No top artists data available")
                return
            
            names = [a['name'][:30] for a in top_connected]
            degrees = [a['degree'] for a in top_connected]
            
            plt.figure(figsize=(12, 8))
            plt.barh(names, degrees, color='coral', alpha=0.7)
            plt.xlabel('Degree (Number of Connections)', fontsize=12)
            plt.ylabel('Artist', fontsize=12)
            plt.title('Top 10 Most Connected Artists', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='x')
            
            output_path = os.path.join(self.output_dir, 'top_artists.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved top artists plot to {output_path}")
            
        except Exception as e:
            logger.error(f"Error plotting top artists: {e}")
    
    def plot_pagerank(self, stats: Dict):
        """Plot top PageRank artists"""
        try:
            top_pagerank = stats.get('top_pagerank', [])
            
            if not top_pagerank:
                logger.warning("No PageRank data available")
                return
            
            names = [a['name'][:30] for a in top_pagerank]
            scores = [a['pagerank'] for a in top_pagerank]
            
            plt.figure(figsize=(12, 8))
            plt.barh(names, scores, color='mediumseagreen', alpha=0.7)
            plt.xlabel('PageRank Score', fontsize=12)
            plt.ylabel('Artist', fontsize=12)
            plt.title('Top 10 Artists by PageRank', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='x')
            
            output_path = os.path.join(self.output_dir, 'pagerank.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved PageRank plot to {output_path}")
            
        except Exception as e:
            logger.error(f"Error plotting PageRank: {e}")
    
    def create_all_visualizations(self, graph_path: str, stats_path: str):
        """Create all visualizations"""
        logger.info("Creating visualizations...")
        
        # Load data
        graph = self.load_graph(graph_path)
        stats = self.load_stats(stats_path)
        
        if graph.number_of_nodes() == 0:
            logger.error("Empty graph, cannot create visualizations")
            return
        
        # Create plots
        self.plot_degree_distribution(graph)
        self.plot_network_sample(graph, sample_size=100)
        
        if stats:
            self.plot_genre_distribution(stats)
            self.plot_top_artists(stats)
            self.plot_pagerank(stats)
        
        logger.info(f"All visualizations saved to {self.output_dir}")


def create_visualizations(graph_path: str = "data/processed/network.graphml",
                         stats_path: str = "data/processed/stats.json",
                         output_dir: str = "data/processed/figures"):
    """Main function to create visualizations"""
    visualizer = NetworkVisualizer(output_dir)
    visualizer.create_all_visualizations(graph_path, stats_path)


if __name__ == "__main__":
    create_visualizations()



"""Network community detection and clustering analysis module"""

import json
import os
from typing import Dict, List, Tuple, Optional
import networkx as nx
import numpy as np
from neo4j import GraphDatabase
from dotenv import load_dotenv
from data_collection.utils import logger


class CommunityAnalyzer:
    """Detect communities and clusters in the music network"""
    
    def __init__(self, config_path: str = "config/neo4j_config.json"):
        """Initialize with Neo4j connection"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        self.driver = GraphDatabase.driver(
            self.config['uri'],
            auth=(self.config['user'], password)
        )
        
        logger.info("Connected to Neo4j for community analysis")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def load_graph_from_file(self, graph_path: str = "data/processed/network.graphml") -> nx.Graph:
        """Load NetworkX graph from file"""
        try:
            graph = nx.read_graphml(graph_path)
            logger.info(f"Loaded graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
            return graph
        except Exception as e:
            logger.error(f"Error loading graph: {e}")
            return nx.Graph()
    
    def detect_louvain_communities(self, graph: nx.Graph) -> Tuple[List[set], float]:
        """
        Detect communities using Louvain algorithm
        
        Returns:
            Tuple of (communities list, modularity score)
        """
        try:
            # Convert to undirected graph for community detection
            undirected_graph = graph.to_undirected()
            
            # Detect communities using Louvain algorithm
            communities = nx.community.louvain_communities(undirected_graph, seed=42)
            
            # Calculate modularity
            modularity = nx.community.modularity(undirected_graph, communities)
            
            logger.info(f"Detected {len(communities)} communities using Louvain algorithm")
            logger.info(f"Modularity score: {modularity:.4f}")
            
            return communities, modularity
            
        except Exception as e:
            logger.error(f"Error in Louvain community detection: {e}")
            return [], 0.0
    
    def detect_greedy_modularity_communities(self, graph: nx.Graph) -> Tuple[List[set], float]:
        """
        Detect communities using greedy modularity maximization
        
        Returns:
            Tuple of (communities list, modularity score)
        """
        try:
            undirected_graph = graph.to_undirected()
            
            # Detect communities using greedy modularity
            communities = nx.community.greedy_modularity_communities(undirected_graph)
            
            # Calculate modularity
            modularity = nx.community.modularity(undirected_graph, communities)
            
            logger.info(f"Detected {len(communities)} communities using greedy modularity")
            logger.info(f"Modularity score: {modularity:.4f}")
            
            return communities, modularity
            
        except Exception as e:
            logger.error(f"Error in greedy modularity community detection: {e}")
            return [], 0.0
    
    def detect_label_propagation_communities(self, graph: nx.Graph) -> List[set]:
        """
        Detect communities using label propagation algorithm
        
        Returns:
            List of communities
        """
        try:
            undirected_graph = graph.to_undirected()
            
            # Detect communities using label propagation
            communities = nx.community.label_propagation_communities(undirected_graph)
            communities = list(communities)
            
            logger.info(f"Detected {len(communities)} communities using label propagation")
            
            return communities
            
        except Exception as e:
            logger.error(f"Error in label propagation community detection: {e}")
            return []
    
    def detect_asyn_lpa_communities(self, graph: nx.Graph) -> List[set]:
        """
        Detect communities using asynchronous label propagation
        
        Returns:
            List of communities
        """
        try:
            undirected_graph = graph.to_undirected()
            
            # Detect communities using async LPA
            communities = nx.community.asyn_lpa_communities(undirected_graph, seed=42)
            communities = list(communities)
            
            logger.info(f"Detected {len(communities)} communities using async LPA")
            
            return communities
            
        except Exception as e:
            logger.error(f"Error in async LPA community detection: {e}")
            return []
    
    def analyze_community_sizes(self, communities: List[set]) -> Dict:
        """Analyze size distribution of communities"""
        if not communities:
            return {}
        
        sizes = [len(c) for c in communities]
        
        analysis = {
            'total_communities': len(communities),
            'total_nodes': sum(sizes),
            'avg_size': float(np.mean(sizes)),
            'median_size': float(np.median(sizes)),
            'min_size': int(min(sizes)),
            'max_size': int(max(sizes)),
            'std_size': float(np.std(sizes)),
            'small_communities': sum(1 for s in sizes if s < 5),
            'medium_communities': sum(1 for s in sizes if 5 <= s < 20),
            'large_communities': sum(1 for s in sizes if s >= 20)
        }
        
        logger.info(f"Community size analysis: {analysis}")
        return analysis
    
    def get_community_by_artist(self, communities: List[set], artist_name: str) -> Optional[int]:
        """Get community ID for a specific artist"""
        for idx, community in enumerate(communities):
            if artist_name in community:
                return idx
        return None
    
    def get_largest_communities(self, communities: List[set], top_n: int = 5) -> List[Dict]:
        """Get information about the largest communities"""
        if not communities:
            return []
        
        # Sort communities by size
        sorted_communities = sorted(communities, key=len, reverse=True)
        
        largest = []
        for idx, community in enumerate(sorted_communities[:top_n]):
            largest.append({
                'community_id': idx,
                'size': len(community),
                'members': list(community)[:10]  # First 10 members
            })
        
        return largest
    
    def analyze_community_genres(self, graph: nx.Graph, communities: List[set]) -> List[Dict]:
        """Analyze genre distribution within each community"""
        if not communities:
            return []
        
        community_genres = []
        
        for idx, community in enumerate(communities):
            # Get genres for all artists in this community
            genres = []
            for node_id in community:
                node_data = graph.nodes.get(node_id, {})
                if node_data.get('node_type') == 'Artist':
                    artist_genres = node_data.get('genres', '')
                    if artist_genres:
                        # Split by semicolon or comma
                        genre_list = [g.strip() for g in artist_genres.replace(';', ',').split(',')]
                        genres.extend(genre_list)
            
            # Count genre frequencies
            genre_counts = {}
            for genre in genres:
                if genre and genre != '':
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            # Get top genres
            top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            community_genres.append({
                'community_id': idx,
                'size': len(community),
                'top_genres': {g: c for g, c in top_genres}
            })
        
        return community_genres
    
    def compute_clustering_coefficient(self, graph: nx.Graph) -> Dict:
        """Compute clustering coefficient statistics"""
        try:
            undirected_graph = graph.to_undirected()
            
            # Compute average clustering coefficient
            avg_clustering = nx.average_clustering(undirected_graph)
            
            # Compute overall clustering coefficient
            transitivity = nx.transitivity(undirected_graph)
            
            # Compute individual clustering coefficients
            clustering_dict = nx.clustering(undirected_graph)
            clustering_values = list(clustering_dict.values())
            
            stats = {
                'average_clustering': float(avg_clustering),
                'transitivity': float(transitivity),
                'max_clustering': float(max(clustering_values)) if clustering_values else 0.0,
                'min_clustering': float(min(clustering_values)) if clustering_values else 0.0,
                'median_clustering': float(np.median(clustering_values)) if clustering_values else 0.0
            }
            
            logger.info(f"Clustering coefficient statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error computing clustering coefficient: {e}")
            return {}
    
    def compute_small_world_stats(self, graph: nx.Graph) -> Dict:
        """Compute small-world network statistics"""
        try:
            undirected_graph = graph.to_undirected()
            
            # Get largest connected component
            largest_cc = max(nx.connected_components(undirected_graph), key=len)
            subgraph = undirected_graph.subgraph(largest_cc)
            
            # Compute average shortest path length
            try:
                avg_path_length = nx.average_shortest_path_length(subgraph)
            except:
                avg_path_length = None
            
            # Compute diameter
            try:
                diameter = nx.diameter(subgraph)
            except:
                diameter = None
            
            # Compute radius
            try:
                radius = nx.radius(subgraph)
            except:
                radius = None
            
            stats = {
                'num_connected_components': nx.number_connected_components(undirected_graph),
                'largest_component_size': len(largest_cc),
                'avg_path_length': float(avg_path_length) if avg_path_length else None,
                'diameter': int(diameter) if diameter else None,
                'radius': int(radius) if radius else None
            }
            
            logger.info(f"Small-world statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error computing small-world stats: {e}")
            return {}
    
    def compute_density(self, graph: nx.Graph) -> Dict:
        """Compute network density statistics"""
        try:
            undirected_graph = graph.to_undirected()
            
            # Overall density
            density = nx.density(undirected_graph)
            
            # Density for largest component
            largest_cc = max(nx.connected_components(undirected_graph), key=len)
            subgraph = undirected_graph.subgraph(largest_cc)
            component_density = nx.density(subgraph)
            
            stats = {
                'overall_density': float(density),
                'largest_component_density': float(component_density),
                'num_edges': undirected_graph.number_of_edges(),
                'num_nodes': undirected_graph.number_of_nodes(),
                'max_possible_edges': int(undirected_graph.number_of_nodes() * (undirected_graph.number_of_nodes() - 1) / 2)
            }
            
            logger.info(f"Network density statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error computing density: {e}")
            return {}
    
    def compute_all_community_analysis(self, graph_path: str = "data/processed/network.graphml") -> Dict:
        """Run all community detection and clustering analyses"""
        logger.info("Starting comprehensive community analysis...")
        
        # Load graph
        graph = self.load_graph_from_file(graph_path)
        
        if graph.number_of_nodes() == 0:
            logger.error("Empty graph, cannot perform analysis")
            return {}
        
        results = {}
        
        # Community Detection
        logger.info("Running community detection algorithms...")
        
        # Louvain communities
        louvain_communities, louvain_modularity = self.detect_louvain_communities(graph)
        results['louvain'] = {
            'communities': [list(c) for c in louvain_communities],
            'modularity': louvain_modularity,
            'num_communities': len(louvain_communities),
            'size_analysis': self.analyze_community_sizes(louvain_communities),
            'largest_communities': self.get_largest_communities(louvain_communities, top_n=5),
            'genre_analysis': self.analyze_community_genres(graph, louvain_communities)
        }
        
        # Greedy modularity communities
        greedy_communities, greedy_modularity = self.detect_greedy_modularity_communities(graph)
        results['greedy_modularity'] = {
            'communities': [list(c) for c in greedy_communities],
            'modularity': greedy_modularity,
            'num_communities': len(greedy_communities),
            'size_analysis': self.analyze_community_sizes(greedy_communities)
        }
        
        # Label propagation communities
        lpa_communities = self.detect_label_propagation_communities(graph)
        results['label_propagation'] = {
            'communities': [list(c) for c in lpa_communities],
            'num_communities': len(lpa_communities),
            'size_analysis': self.analyze_community_sizes(lpa_communities)
        }
        
        # Clustering Analysis
        logger.info("Computing clustering coefficients...")
        results['clustering'] = self.compute_clustering_coefficient(graph)
        
        # Small-world Analysis
        logger.info("Computing small-world statistics...")
        results['small_world'] = self.compute_small_world_stats(graph)
        
        # Density Analysis
        logger.info("Computing network density...")
        results['density'] = self.compute_density(graph)
        
        logger.info("Community analysis completed")
        return results
    
    def save_community_analysis(self, analysis: Dict, output_path: str):
        """Save community analysis to JSON"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved community analysis to {output_path}")


def analyze_communities(graph_path: str = "data/processed/network.graphml",
                        output_path: str = "data/processed/community_analysis.json") -> Dict:
    """Main function to analyze communities and clustering"""
    analyzer = CommunityAnalyzer()
    
    try:
        analysis = analyzer.compute_all_community_analysis(graph_path)
        analyzer.save_community_analysis(analysis, output_path)
        return analysis
    finally:
        analyzer.close()


if __name__ == "__main__":
    analyze_communities()


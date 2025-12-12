import json
import os
from typing import Dict, List, Optional
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from data_collection.utils import logger

class NetworkVisualizer:

    def __init__(self, output_dir: str='data/processed/figures'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        plt.style.use('default')

    def load_graph(self, graph_path: str) -> nx.Graph:
        try:
            graph = nx.read_graphml(graph_path)
            logger.info(f'Loaded graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges')
            return graph
        except Exception as e:
            logger.error(f'Error loading graph: {e}')
            return nx.Graph()

    def load_stats(self, stats_path: str) -> Dict:
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            logger.info(f'Loaded statistics from {stats_path}')
            return stats
        except Exception as e:
            logger.error(f'Error loading statistics: {e}')
            return {}

    def plot_degree_distribution(self, graph: nx.Graph):
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
            logger.info(f'Saved degree distribution plot to {output_path}')
        except Exception as e:
            logger.error(f'Error plotting degree distribution: {e}')

    def plot_network_sample(self, graph: nx.Graph, sample_size: int=100):
        try:
            artist_nodes = [n for n, d in graph.nodes(data=True) if d.get('node_type') == 'Artist']
            if len(artist_nodes) > sample_size:
                degrees = [(n, graph.degree(n)) for n in artist_nodes]
                degrees.sort(key=lambda x: x[1], reverse=True)
                sample_nodes = [n for n, d in degrees[:sample_size]]
            else:
                sample_nodes = artist_nodes
            subgraph = graph.subgraph(sample_nodes)
            plt.figure(figsize=(14, 10))
            pos = nx.spring_layout(subgraph, k=0.5, iterations=50, seed=42)
            nx.draw_networkx_nodes(subgraph, pos, node_color='lightblue', node_size=300, alpha=0.7)
            nx.draw_networkx_edges(subgraph, pos, alpha=0.2, width=1)
            high_degree_nodes = [n for n in subgraph.nodes() if subgraph.degree(n) > 3]
            labels = {n: subgraph.nodes[n].get('name', '')[:20] for n in high_degree_nodes}
            nx.draw_networkx_labels(subgraph, pos, labels=labels, font_size=8)
            plt.title(f'Music Network Visualization (Top {len(sample_nodes)} Artists)', fontsize=14, fontweight='bold')
            plt.axis('off')
            output_path = os.path.join(self.output_dir, 'network_sample.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f'Saved network sample plot to {output_path}')
        except Exception as e:
            logger.error(f'Error plotting network sample: {e}')

    def plot_genre_distribution(self, stats: Dict):
        try:
            genre_dist = stats.get('genre_distribution', {})
            if not genre_dist:
                logger.warning('No genre distribution data available')
                return
            genres = list(genre_dist.keys())[:15]
            counts = [genre_dist[g] for g in genres]
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
            logger.info(f'Saved genre distribution plot to {output_path}')
        except Exception as e:
            logger.error(f'Error plotting genre distribution: {e}')

    def plot_top_artists(self, stats: Dict):
        try:
            top_connected = stats.get('top_connected', [])
            if not top_connected:
                logger.warning('No top artists data available')
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
            logger.info(f'Saved top artists plot to {output_path}')
        except Exception as e:
            logger.error(f'Error plotting top artists: {e}')

    def plot_pagerank(self, stats: Dict):
        try:
            top_pagerank = stats.get('top_pagerank', [])
            if not top_pagerank:
                logger.warning('No PageRank data available')
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
            logger.info(f'Saved PageRank plot to {output_path}')
        except Exception as e:
            logger.error(f'Error plotting PageRank: {e}')

    def plot_communities(self, graph: nx.Graph, communities: List[set], title: str='Community Structure', output_filename: str='communities.png'):
        try:
            node_colors = {}
            colors = plt.cm.tab20(range(len(communities)))
            for idx, community in enumerate(communities):
                color = colors[idx]
                for node in community:
                    node_colors[node] = color
            artist_nodes = [n for n, d in graph.nodes(data=True) if d.get('node_type') == 'Artist']
            nodes_in_communities = set()
            for c in communities:
                nodes_in_communities.update(c)
            filtered_nodes = [n for n in artist_nodes if n in nodes_in_communities]
            if len(filtered_nodes) > 200:
                degrees = [(n, graph.degree(n)) for n in filtered_nodes]
                degrees.sort(key=lambda x: x[1], reverse=True)
                filtered_nodes = [n for n, d in degrees[:200]]
            subgraph = graph.subgraph(filtered_nodes)
            subgraph_colors = [node_colors.get(n, 'lightgray') for n in subgraph.nodes()]
            plt.figure(figsize=(16, 12))
            pos = nx.spring_layout(subgraph, k=1, iterations=50, seed=42)
            nx.draw_networkx_nodes(subgraph, pos, node_color=subgraph_colors, node_size=300, alpha=0.8)
            nx.draw_networkx_edges(subgraph, pos, alpha=0.2, width=0.5)
            high_degree_nodes = [n for n in subgraph.nodes() if subgraph.degree(n) > 5]
            labels = {n: subgraph.nodes[n].get('name', '')[:15] for n in high_degree_nodes}
            nx.draw_networkx_labels(subgraph, pos, labels=labels, font_size=7)
            plt.title(title, fontsize=16, fontweight='bold')
            plt.axis('off')
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f'Saved community visualization to {output_path}')
        except Exception as e:
            logger.error(f'Error plotting communities: {e}')

    def plot_community_sizes(self, communities: List[set], output_filename: str='community_sizes.png'):
        try:
            sizes = [len(c) for c in communities]
            plt.figure(figsize=(12, 8))
            plt.hist(sizes, bins=30, edgecolor='black', alpha=0.7, color='steelblue')
            plt.xlabel('Community Size', fontsize=12)
            plt.ylabel('Number of Communities', fontsize=12)
            plt.title('Community Size Distribution', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            output_path = os.path.join(self.output_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f'Saved community size distribution to {output_path}')
        except Exception as e:
            logger.error(f'Error plotting community sizes: {e}')

    def plot_clustering_coefficient_distribution(self, graph: nx.Graph):
        try:
            undirected_graph = graph.to_undirected()
            clustering_dict = nx.clustering(undirected_graph)
            clustering_values = list(clustering_dict.values())
            plt.figure(figsize=(10, 6))
            plt.hist(clustering_values, bins=50, edgecolor='black', alpha=0.7, color='mediumseagreen')
            plt.xlabel('Clustering Coefficient', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.title('Clustering Coefficient Distribution', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            output_path = os.path.join(self.output_dir, 'clustering_coefficient_distribution.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f'Saved clustering coefficient distribution to {output_path}')
        except Exception as e:
            logger.error(f'Error plotting clustering coefficient distribution: {e}')

    def create_all_visualizations(self, graph_path: str, stats_path: str):
        logger.info('Creating visualizations...')
        graph = self.load_graph(graph_path)
        stats = self.load_stats(stats_path)
        if graph.number_of_nodes() == 0:
            logger.error('Empty graph, cannot create visualizations')
            return
        self.plot_degree_distribution(graph)
        self.plot_network_sample(graph, sample_size=100)
        if stats:
            self.plot_genre_distribution(stats)
            self.plot_top_artists(stats)
            self.plot_pagerank(stats)
        logger.info(f'All visualizations saved to {self.output_dir}')

    def create_community_visualizations(self, graph_path: str, community_analysis_path: str):
        logger.info('Creating community visualizations...')
        graph = self.load_graph(graph_path)
        try:
            with open(community_analysis_path, 'r', encoding='utf-8') as f:
                community_data = json.load(f)
        except Exception as e:
            logger.error(f'Error loading community analysis: {e}')
            return
        if graph.number_of_nodes() == 0:
            logger.error('Empty graph, cannot create visualizations')
            return
        if 'louvain' in community_data:
            louvain_communities = community_data['louvain']['communities']
            communities = [set(c) for c in louvain_communities]
            self.plot_communities(graph, communities, title=f'Louvain Communities (Modularity: {community_data['louvain']['modularity']:.3f})', output_filename='louvain_communities.png')
            self.plot_community_sizes(communities, 'louvain_community_sizes.png')
        self.plot_clustering_coefficient_distribution(graph)
        logger.info(f'Community visualizations saved to {self.output_dir}')

def create_visualizations(graph_path: str='data/processed/network.graphml', stats_path: str='data/processed/stats.json', output_dir: str='data/processed/figures'):
    visualizer = NetworkVisualizer(output_dir)
    visualizer.create_all_visualizations(graph_path, stats_path)

def create_community_visualizations(graph_path: str='data/processed/network.graphml', community_analysis_path: str='data/processed/community_analysis.json', output_dir: str='data/processed/figures'):
    visualizer = NetworkVisualizer(output_dir)
    visualizer.create_community_visualizations(graph_path, community_analysis_path)
if __name__ == '__main__':
    create_visualizations()

import json
import os
from typing import Dict, List, Optional, Tuple
import networkx as nx
from neo4j import GraphDatabase
from dotenv import load_dotenv
from data_collection.utils import logger

class PathAnalyzer:

    def __init__(self, config_path: str='config/neo4j_config.json'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        self.driver = GraphDatabase.driver(self.config['uri'], auth=(self.config['user'], password))
        logger.info('Connected to Neo4j for path analysis')

    def close(self):
        if self.driver:
            self.driver.close()

    def load_graph_from_file(self, graph_path: str='data/processed/network.graphml') -> nx.Graph:
        try:
            graph = nx.read_graphml(graph_path)
            logger.info(f'Loaded graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges')
            return graph
        except Exception as e:
            logger.error(f'Error loading graph: {e}')
            return nx.Graph()

    def find_shortest_path(self, graph: nx.Graph, artist1_name: str, artist2_name: str) -> Optional[Dict]:
        try:
            undirected_graph = graph.to_undirected()
            artist1_node = None
            artist2_node = None
            for node_id, node_data in graph.nodes(data=True):
                if node_data.get('node_type') == 'Artist':
                    if node_data.get('name') == artist1_name:
                        artist1_node = node_id
                    if node_data.get('name') == artist2_name:
                        artist2_node = node_id
            if not artist1_node or not artist2_node:
                logger.warning(f'Could not find artists: {artist1_name} or {artist2_name}')
                return None
            if not nx.has_path(undirected_graph, artist1_node, artist2_node):
                logger.info(f'No path exists between {artist1_name} and {artist2_name}')
                return {'artist1': artist1_name, 'artist2': artist2_name, 'path_exists': False, 'path_length': None, 'path': None}
            path = nx.shortest_path(undirected_graph, artist1_node, artist2_node)
            path_length = len(path) - 1
            path_artists = []
            for node_id in path:
                node_data = graph.nodes[node_id]
                if node_data.get('node_type') == 'Artist':
                    path_artists.append({'name': node_data.get('name', node_id), 'node_id': node_id})
                elif node_data.get('node_type') == 'Album':
                    path_artists.append({'name': node_data.get('title', node_id), 'node_id': node_id, 'type': 'Album'})
            result = {'artist1': artist1_name, 'artist2': artist2_name, 'path_exists': True, 'path_length': path_length, 'path': path_artists, 'path_size': len(path_artists)}
            logger.info(f'Found path between {artist1_name} and {artist2_name}: length={path_length}')
            return result
        except Exception as e:
            logger.error(f'Error finding shortest path: {e}')
            return None

    def find_all_shortest_paths(self, graph: nx.Graph, artist1_name: str, artist2_name: str) -> List[Dict]:
        try:
            undirected_graph = graph.to_undirected()
            artist1_node = None
            artist2_node = None
            for node_id, node_data in graph.nodes(data=True):
                if node_data.get('node_type') == 'Artist':
                    if node_data.get('name') == artist1_name:
                        artist1_node = node_id
                    if node_data.get('name') == artist2_name:
                        artist2_node = node_id
            if not artist1_node or not artist2_node:
                return []
            all_paths = list(nx.all_shortest_paths(undirected_graph, artist1_node, artist2_node))
            result_paths = []
            for path in all_paths:
                path_artists = []
                for node_id in path:
                    node_data = graph.nodes[node_id]
                    if node_data.get('node_type') == 'Artist':
                        path_artists.append({'name': node_data.get('name', node_id), 'node_id': node_id})
                    elif node_data.get('node_type') == 'Album':
                        path_artists.append({'name': node_data.get('title', node_id), 'node_id': node_id, 'type': 'Album'})
                result_paths.append({'path': path_artists, 'path_length': len(path) - 1})
            logger.info(f'Found {len(result_paths)} shortest paths between {artist1_name} and {artist2_name}')
            return result_paths
        except Exception as e:
            logger.error(f'Error finding all shortest paths: {e}')
            return []

    def get_artist_shortest_paths_summary(self, graph: nx.Graph, limit: int=20) -> Dict:
        try:
            undirected_graph = graph.to_undirected()
            artist_nodes = [n for n, d in graph.nodes(data=True) if d.get('node_type') == 'Artist']
            largest_cc = max(nx.connected_components(undirected_graph), key=len)
            cc_artists = [n for n in artist_nodes if n in largest_cc]
            artist_names = [graph.nodes[n].get('name', n) for n in cc_artists]
            import random
            random.seed(42)
            if len(artist_names) < 2:
                return {}
            pairs = []
            attempts = 0
            max_attempts = limit * 10
            while len(pairs) < limit and attempts < max_attempts:
                attempts += 1
                a1, a2 = random.sample(artist_names, 2)
                if (a1, a2) not in pairs and (a2, a1) not in pairs:
                    pairs.append((a1, a2))
            path_lengths = []
            path_examples = []
            for a1, a2 in pairs[:limit]:
                result = self.find_shortest_path(graph, a1, a2)
                if result and result.get('path_exists'):
                    path_lengths.append(result['path_length'])
                    if len(path_examples) < 5:
                        path_examples.append(result)
            if not path_lengths:
                return {'num_pairs_analyzed': len(pairs), 'num_paths_found': 0, 'avg_path_length': None, 'min_path_length': None, 'max_path_length': None, 'examples': []}
            summary = {'num_pairs_analyzed': len(pairs), 'num_paths_found': len(path_lengths), 'avg_path_length': float(sum(path_lengths) / len(path_lengths)), 'min_path_length': int(min(path_lengths)), 'max_path_length': int(max(path_lengths)), 'median_path_length': float(sorted(path_lengths)[len(path_lengths) // 2]), 'examples': path_examples[:5]}
            logger.info(f'Path summary: {summary}')
            return summary
        except Exception as e:
            logger.error(f'Error computing path summary: {e}')
            return {}

    def compute_average_path_length(self, graph: nx.Graph) -> Optional[float]:
        try:
            undirected_graph = graph.to_undirected()
            largest_cc = max(nx.connected_components(undirected_graph), key=len)
            subgraph = undirected_graph.subgraph(largest_cc)
            avg_path_length = nx.average_shortest_path_length(subgraph)
            logger.info(f'Average shortest path length: {avg_path_length:.2f}')
            return float(avg_path_length)
        except Exception as e:
            logger.error(f'Error computing average path length: {e}')
            return None

    def compute_diameter_and_radius(self, graph: nx.Graph) -> Dict:
        try:
            undirected_graph = graph.to_undirected()
            largest_cc = max(nx.connected_components(undirected_graph), key=len)
            subgraph = undirected_graph.subgraph(largest_cc)
            diameter = nx.diameter(subgraph)
            radius = nx.radius(subgraph)
            result = {'diameter': int(diameter), 'radius': int(radius), 'component_size': len(largest_cc)}
            logger.info(f'Network diameter: {diameter}, radius: {radius}')
            return result
        except Exception as e:
            logger.error(f'Error computing diameter/radius: {e}')
            return {}

    def compute_all_path_analysis(self, graph_path: str='data/processed/network.graphml') -> Dict:
        logger.info('Starting path analysis...')
        graph = self.load_graph_from_file(graph_path)
        if graph.number_of_nodes() == 0:
            logger.error('Empty graph, cannot perform analysis')
            return {}
        results = {}
        logger.info('Computing average shortest path length...')
        avg_path = self.compute_average_path_length(graph)
        results['average_path_length'] = avg_path
        logger.info('Computing diameter and radius...')
        results['diameter_radius'] = self.compute_diameter_and_radius(graph)
        logger.info('Analyzing sample artist paths...')
        results['sample_paths'] = self.get_artist_shortest_paths_summary(graph, limit=20)
        logger.info('Path analysis completed')
        return results

    def save_path_analysis(self, analysis: Dict, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        logger.info(f'Saved path analysis to {output_path}')

def analyze_paths(graph_path: str='data/processed/network.graphml', output_path: str='data/processed/path_analysis.json') -> Dict:
    analyzer = PathAnalyzer()
    try:
        analysis = analyzer.compute_all_path_analysis(graph_path)
        analyzer.save_path_analysis(analysis, output_path)
        return analysis
    finally:
        analyzer.close()
if __name__ == '__main__':
    analyze_paths()

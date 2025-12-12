import json
import os
from typing import Dict, List
import networkx as nx
from neo4j import GraphDatabase
from dotenv import load_dotenv
from data_collection.utils import logger

class NetworkStats:

    def __init__(self, config_path: str='config/neo4j_config.json'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        self.driver = GraphDatabase.driver(self.config['uri'], auth=(self.config['user'], password))
        logger.info('Connected to Neo4j for statistics')

    def close(self):
        if self.driver:
            self.driver.close()

    def get_node_counts(self) -> Dict[str, int]:
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            result = session.run('\n                MATCH (n)\n                RETURN labels(n)[0] AS label, count(n) AS count\n                ORDER BY count DESC\n            ')
            counts = {}
            for record in result:
                counts[record['label']] = record['count']
            logger.info(f'Node counts: {counts}')
            return counts

    def get_edge_counts(self) -> Dict[str, int]:
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            result = session.run('\n                MATCH ()-[r]->()\n                RETURN type(r) AS type, count(r) AS count\n                ORDER BY count DESC\n            ')
            counts = {}
            for record in result:
                counts[record['type']] = record['count']
            logger.info(f'Edge counts: {counts}')
            return counts

    def get_degree_stats(self) -> Dict:
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            result = session.run('\n                MATCH (a:Artist)-[r]-()\n                WITH a, count(r) AS degree\n                RETURN \n                    avg(degree) AS avg_degree,\n                    max(degree) AS max_degree,\n                    min(degree) AS min_degree,\n                    percentileCont(degree, 0.5) AS median_degree\n            ')
            record = result.single()
            if record:
                stats = {'avg_degree': float(record['avg_degree'] or 0), 'max_degree': int(record['max_degree'] or 0), 'min_degree': int(record['min_degree'] or 0), 'median_degree': float(record['median_degree'] or 0)}
                logger.info(f'Degree statistics: {stats}')
                return stats
            return {}

    def get_top_connected_artists(self, limit: int=10) -> List[Dict]:
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            result = session.run('\n                MATCH (a:Artist)-[r]-()\n                WITH a, count(r) AS degree\n                ORDER BY degree DESC\n                LIMIT $limit\n                RETURN a.name AS name, degree\n            ', limit=limit)
            top_artists = []
            for record in result:
                top_artists.append({'name': record['name'], 'degree': record['degree']})
            logger.info(f'Top {limit} connected artists retrieved')
            return top_artists

    def get_top_collaborators(self, limit: int=10) -> List[Dict]:
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            result = session.run('\n                MATCH (a:Artist)-[r:COLLABORATES_WITH]-()\n                WITH a, count(r) AS collaborations, sum(r.shared_albums) AS total_shared\n                ORDER BY collaborations DESC\n                LIMIT $limit\n                RETURN a.name AS name, collaborations, total_shared\n            ', limit=limit)
            top_collaborators = []
            for record in result:
                top_collaborators.append({'name': record['name'], 'collaborations': record['collaborations'], 'total_shared_albums': record['total_shared']})
            logger.info(f'Top {limit} collaborating artists retrieved')
            return top_collaborators

    def get_strongest_collaborations(self, limit: int=10) -> List[Dict]:
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            result = session.run('\n                MATCH (a1:Artist)-[r:COLLABORATES_WITH]-(a2:Artist)\n                WHERE id(a1) < id(a2)\n                WITH a1, a2, r.shared_albums AS shared\n                ORDER BY shared DESC\n                LIMIT $limit\n                RETURN a1.name AS artist1, a2.name AS artist2, shared\n            ', limit=limit)
            collaborations = []
            for record in result:
                collaborations.append({'artist1': record['artist1'], 'artist2': record['artist2'], 'shared_albums': record['shared']})
            logger.info(f'Top {limit} strongest collaborations retrieved')
            return collaborations

    def get_genre_distribution(self) -> Dict[str, int]:
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            result = session.run("\n                MATCH (a:Artist)\n                WHERE a.genres IS NOT NULL AND a.genres <> ''\n                RETURN a.genres AS genres, count(*) AS count\n                ORDER BY count DESC\n                LIMIT 20\n            ")
            distribution = {}
            for record in result:
                distribution[record['genres']] = record['count']
            logger.info(f'Retrieved genre distribution for {len(distribution)} genres')
            return distribution

    def compute_pagerank_neo4j(self, limit: int=10) -> List[Dict]:
        try:
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                session.run("\n                    CALL gds.graph.project(\n                        'music-network',\n                        ['Artist', 'Album'],\n                        {PERFORMS_ON: {orientation: 'UNDIRECTED'}}\n                    )\n                ")
                result = session.run("\n                    CALL gds.pageRank.stream('music-network')\n                    YIELD nodeId, score\n                    WITH gds.util.asNode(nodeId) AS node, score\n                    WHERE 'Artist' IN labels(node)\n                    RETURN node.name AS name, score\n                    ORDER BY score DESC\n                    LIMIT $limit\n                ", limit=limit)
                pagerank = []
                for record in result:
                    pagerank.append({'name': record['name'], 'pagerank': float(record['score'])})
                session.run("CALL gds.graph.drop('music-network')")
                logger.info(f'Computed PageRank for top {limit} artists')
                return pagerank
        except Exception as e:
            logger.warning(f'Neo4j GDS not available, falling back to NetworkX: {e}')
            return []

    def compute_local_pagerank(self, graph_path: str='data/processed/network.graphml', limit: int=10) -> List[Dict]:
        try:
            graph = nx.read_graphml(graph_path)
            artist_nodes = [n for n, d in graph.nodes(data=True) if d.get('node_type') == 'Artist']
            pagerank = nx.pagerank(graph)
            artist_pagerank = [(n, pagerank[n]) for n in artist_nodes]
            artist_pagerank.sort(key=lambda x: x[1], reverse=True)
            top_pagerank = []
            for node_id, score in artist_pagerank[:limit]:
                name = graph.nodes[node_id].get('name', node_id)
                top_pagerank.append({'name': name, 'pagerank': float(score)})
            logger.info(f'Computed local PageRank for top {limit} artists')
            return top_pagerank
        except Exception as e:
            logger.error(f'Error computing local PageRank: {e}')
            return []

    def compute_all_stats(self) -> Dict:
        logger.info('Computing network statistics...')
        stats = {'node_counts': self.get_node_counts(), 'edge_counts': self.get_edge_counts(), 'degree_stats': self.get_degree_stats(), 'top_connected': self.get_top_connected_artists(10), 'top_collaborators': self.get_top_collaborators(10), 'strongest_collaborations': self.get_strongest_collaborations(10), 'genre_distribution': self.get_genre_distribution()}
        pagerank = self.compute_pagerank_neo4j(10)
        if not pagerank:
            pagerank = self.compute_local_pagerank(limit=10)
        stats['top_pagerank'] = pagerank
        logger.info('Statistics computation completed')
        return stats

    def save_stats(self, stats: Dict, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logger.info(f'Saved statistics to {output_path}')

def compute_stats(config_path: str='config/neo4j_config.json', output_path: str='data/processed/stats.json') -> Dict:
    stats_computer = NetworkStats(config_path)
    try:
        stats = stats_computer.compute_all_stats()
        stats_computer.save_stats(stats, output_path)
        return stats
    finally:
        stats_computer.close()
if __name__ == '__main__':
    compute_stats()

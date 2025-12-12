from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
import logging
from .cypher_gen import CypherQueryGenerator
from .path_ranker import PathRanker
from .context_builder import ContextBuilder
from .verbalizer import TripleVerbalizer
logger = logging.getLogger(__name__)

class GraphRAGRetriever:

    def __init__(self, neo4j_driver, llm_model=None):
        self.driver = neo4j_driver
        self.llm = llm_model
        self.cypher_gen = CypherQueryGenerator()
        self.path_ranker = PathRanker()
        self.context_builder = ContextBuilder()
        self.verbalizer = TripleVerbalizer()

    def retrieve_context(self, query: str, max_hops: int=3) -> Dict[str, Any]:
        try:
            logger.info(f'Processing query: {query}')
            entities = self._extract_entities(query)
            logger.info(f'Extracted entities: {entities}')
            if not entities:
                return {'context_text': 'No entities found in query to search for.', 'paths': [], 'entities': [], 'error': 'no_entities'}
            paths = self._find_graph_paths(entities, max_hops)
            logger.info(f'Found {len(paths)} paths')
            if not paths:
                return {'context_text': f'No connections found between entities: {', '.join(entities)}', 'paths': [], 'entities': entities, 'error': 'no_paths'}
            ranked_paths = self.path_ranker.rank_paths(paths, query, entities)
            logger.info(f'Ranked {len(ranked_paths)} paths')
            top_paths = self.path_ranker.filter_top_paths(ranked_paths, top_k=5)
            context = self.context_builder.build_context(top_paths, query)
            logger.info(f'Built context with {len(top_paths)} top paths')
            return {'context_text': context, 'paths': top_paths, 'entities': entities, 'all_paths_count': len(paths), 'ranked_paths_count': len(ranked_paths)}
        except Exception as e:
            logger.error(f'Error in retrieve_context: {e}')
            return {'context_text': f'Error retrieving information: {str(e)}', 'paths': [], 'entities': [], 'error': str(e)}

    def _extract_entities(self, query: str) -> List[str]:
        entities = []
        pattern_entities = self.cypher_gen.parse_entities_from_query(query)
        entities.extend(pattern_entities)
        if self.llm:
            llm_entities = self._extract_entities_with_llm(query)
            entities.extend(llm_entities)
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                unique_entities.append(entity)
                seen.add(entity)
        return unique_entities

    def _extract_entities_with_llm(self, query: str) -> List[str]:
        return []

    def _find_graph_paths(self, entities: List[str], max_hops: int) -> List[Dict[str, Any]]:
        paths = []
        try:
            with self.driver.session() as session:
                path_query = self.cypher_gen.generate_path_query(entities, max_hops)
                params = self.cypher_gen.get_query_params(entities)
                result = session.run(path_query, params)
                for record in result:
                    path_data = {'path': record['path'], 'path_length': record['path_length'], 'node_names': record['node_names'], 'rel_types': record['rel_types']}
                    paths.append(path_data)
        except Exception as e:
            logger.error(f'Error finding graph paths: {e}')
        return paths

    def _find_entity_connections(self, entity: str) -> List[Dict[str, Any]]:
        connections = []
        try:
            with self.driver.session() as session:
                entity_pattern = f'(?i).*{entity}.*'
                query = '\n                MATCH (n)\n                WHERE n.name =~ $entity_pattern\n                OPTIONAL MATCH (n)-[r]-(connected)\n                RETURN n, collect({rel: r, connected: connected}) as connections\n                ORDER BY n.name\n                LIMIT 10\n                '
                result = session.run(query, {'entity_pattern': entity_pattern})
                for record in result:
                    node = record['n']
                    node_connections = record['connections']
                    connections.append({'entity': node, 'connections': node_connections})
        except Exception as e:
            logger.error(f'Error finding entity connections: {e}')
        return connections

    def get_entity_info(self, entity_name: str) -> Optional[Dict[str, Any]]:
        try:
            with self.driver.session() as session:
                query = '\n                MATCH (n)\n                WHERE n.name = $entity_name\n                RETURN n, labels(n) as labels\n                '
                result = session.run(query, {'entity_name': entity_name})
                record = result.single()
                if record:
                    return {'node': record['n'], 'labels': record['labels']}
        except Exception as e:
            logger.error(f'Error getting entity info: {e}')
        return None

    def search_similar_entities(self, entity_name: str, limit: int=5) -> List[str]:
        similar_entities = []
        try:
            with self.driver.session() as session:
                pattern = f'(?i).*{entity_name}.*'
                query = '\n                MATCH (n)\n                WHERE n.name =~ $pattern AND n.name <> $exact_name\n                RETURN n.name as name\n                ORDER BY n.name\n                LIMIT $limit\n                '
                result = session.run(query, {'pattern': pattern, 'exact_name': entity_name, 'limit': limit})
                similar_entities = [record['name'] for record in result]
        except Exception as e:
            logger.error(f'Error searching similar entities: {e}')
        return similar_entities

    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        entities = self._extract_entities(query)
        return {'entity_count': len(entities), 'entities': entities, 'estimated_hops': min(len(entities), 3), 'complexity_level': 'simple' if len(entities) <= 2 else 'complex'}

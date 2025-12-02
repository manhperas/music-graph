"""
GraphRAG Retriever - Main component for Graph Retrieval-Augmented Generation.

This module implements the main GraphRAG retrieval pipeline that:
1. Extracts entities from user queries
2. Retrieves relevant graph paths from Neo4j
3. Ranks paths by relevance
4. Builds natural language context
"""

from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
import logging

from .cypher_gen import CypherQueryGenerator
from .path_ranker import PathRanker
from .context_builder import ContextBuilder
from .verbalizer import TripleVerbalizer

logger = logging.getLogger(__name__)


class GraphRAGRetriever:
    """Main GraphRAG retriever for music knowledge graph."""

    def __init__(self, neo4j_driver, llm_model=None):
        """
        Initialize GraphRAG retriever.

        Args:
            neo4j_driver: Neo4j driver instance
            llm_model: Optional LLM model for enhanced entity extraction
        """
        self.driver = neo4j_driver
        self.llm = llm_model

        # Initialize components
        self.cypher_gen = CypherQueryGenerator()
        self.path_ranker = PathRanker()
        self.context_builder = ContextBuilder()
        self.verbalizer = TripleVerbalizer()

    def retrieve_context(self, query: str, max_hops: int = 3) -> Dict[str, Any]:
        """
        Main retrieval pipeline.

        Args:
            query: User query string
            max_hops: Maximum hops for path finding

        Returns:
            Dictionary containing context and metadata
        """
        try:
            logger.info(f"Processing query: {query}")

            # Step 1: Extract entities from query
            entities = self._extract_entities(query)
            logger.info(f"Extracted entities: {entities}")

            if not entities:
                return {
                    'context_text': "No entities found in query to search for.",
                    'paths': [],
                    'entities': [],
                    'error': 'no_entities'
                }

            # Step 2: Find graph paths
            paths = self._find_graph_paths(entities, max_hops)
            logger.info(f"Found {len(paths)} paths")

            if not paths:
                return {
                    'context_text': f"No connections found between entities: {', '.join(entities)}",
                    'paths': [],
                    'entities': entities,
                    'error': 'no_paths'
                }

            # Step 3: Rank paths by relevance
            ranked_paths = self.path_ranker.rank_paths(paths, query, entities)
            logger.info(f"Ranked {len(ranked_paths)} paths")

            # Step 4: Build natural language context
            top_paths = self.path_ranker.filter_top_paths(ranked_paths, top_k=5)
            context = self.context_builder.build_context(top_paths, query)

            logger.info(f"Built context with {len(top_paths)} top paths")

            return {
                'context_text': context,
                'paths': top_paths,
                'entities': entities,
                'all_paths_count': len(paths),
                'ranked_paths_count': len(ranked_paths)
            }

        except Exception as e:
            logger.error(f"Error in retrieve_context: {e}")
            return {
                'context_text': f"Error retrieving information: {str(e)}",
                'paths': [],
                'entities': [],
                'error': str(e)
            }

    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract entities from query using multiple strategies.

        Args:
            query: User query

        Returns:
            List of entity names
        """
        entities = []

        # Strategy 1: Pattern-based extraction
        pattern_entities = self.cypher_gen.parse_entities_from_query(query)
        entities.extend(pattern_entities)

        # Strategy 2: Use LLM if available (future enhancement)
        if self.llm:
            llm_entities = self._extract_entities_with_llm(query)
            entities.extend(llm_entities)

        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                unique_entities.append(entity)
                seen.add(entity)

        return unique_entities

    def _extract_entities_with_llm(self, query: str) -> List[str]:
        """
        Use LLM for entity extraction (placeholder for future implementation).

        Args:
            query: User query

        Returns:
            List of entities extracted by LLM
        """
        # This would use few-shot prompting with Qwen model
        # For now, return empty list
        return []

    def _find_graph_paths(self, entities: List[str], max_hops: int) -> List[Dict[str, Any]]:
        """
        Find paths in graph connecting the entities.

        Args:
            entities: List of entity names
            max_hops: Maximum path length

        Returns:
            List of path dictionaries
        """
        paths = []

        try:
            with self.driver.session() as session:
                # Query for paths between entities
                path_query = self.cypher_gen.generate_path_query(entities, max_hops)
                params = self.cypher_gen.get_query_params(entities)

                result = session.run(path_query, params)

                for record in result:
                    path_data = {
                        'path': record['path'],
                        'path_length': record['path_length'],
                        'node_names': record['node_names'],
                        'rel_types': record['rel_types']
                    }
                    paths.append(path_data)

        except Exception as e:
            logger.error(f"Error finding graph paths: {e}")

        return paths

    def _find_entity_connections(self, entity: str) -> List[Dict[str, Any]]:
        """
        Find all connections for a specific entity.

        Args:
            entity: Entity name

        Returns:
            List of connection data
        """
        connections = []

        try:
            with self.driver.session() as session:
                # Fuzzy search for entity
                entity_pattern = f"(?i).*{entity}.*"
                query = """
                MATCH (n)
                WHERE n.name =~ $entity_pattern
                OPTIONAL MATCH (n)-[r]-(connected)
                RETURN n, collect({rel: r, connected: connected}) as connections
                ORDER BY n.name
                LIMIT 10
                """

                result = session.run(query, {'entity_pattern': entity_pattern})

                for record in result:
                    node = record['n']
                    node_connections = record['connections']
                    connections.append({
                        'entity': node,
                        'connections': node_connections
                    })

        except Exception as e:
            logger.error(f"Error finding entity connections: {e}")

        return connections

    def get_entity_info(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific entity.

        Args:
            entity_name: Name of entity to look up

        Returns:
            Entity information dictionary or None
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n)
                WHERE n.name = $entity_name
                RETURN n, labels(n) as labels
                """

                result = session.run(query, {'entity_name': entity_name})

                record = result.single()
                if record:
                    return {
                        'node': record['n'],
                        'labels': record['labels']
                    }

        except Exception as e:
            logger.error(f"Error getting entity info: {e}")

        return None

    def search_similar_entities(self, entity_name: str, limit: int = 5) -> List[str]:
        """
        Find entities with similar names.

        Args:
            entity_name: Base entity name
            limit: Maximum number of similar entities

        Returns:
            List of similar entity names
        """
        similar_entities = []

        try:
            with self.driver.session() as session:
                # Simple fuzzy matching
                pattern = f"(?i).*{entity_name}.*"
                query = """
                MATCH (n)
                WHERE n.name =~ $pattern AND n.name <> $exact_name
                RETURN n.name as name
                ORDER BY n.name
                LIMIT $limit
                """

                result = session.run(query, {
                    'pattern': pattern,
                    'exact_name': entity_name,
                    'limit': limit
                })

                similar_entities = [record['name'] for record in result]

        except Exception as e:
            logger.error(f"Error searching similar entities: {e}")

        return similar_entities

    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """
        Analyze the complexity of a query.

        Args:
            query: User query

        Returns:
            Complexity analysis
        """
        entities = self._extract_entities(query)

        return {
            'entity_count': len(entities),
            'entities': entities,
            'estimated_hops': min(len(entities), 3),  # Rough estimate
            'complexity_level': 'simple' if len(entities) <= 2 else 'complex'
        }

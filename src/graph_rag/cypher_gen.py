"""
Cypher Query Generator for GraphRAG.

This module generates Cypher queries to retrieve relevant paths
from Neo4j graph database based on user queries.
"""

from typing import List, Dict, Any, Optional
import re


class CypherQueryGenerator:
    """Generates Cypher queries for graph retrieval."""

    def __init__(self):
        self.relation_types = {
            'COLLABORATES_WITH': 'COLLABORATES_WITH',
            'PERFORMS_ON': 'PERFORMS_ON',
            'HAS_GENRE': 'HAS_GENRE',
            'WON_AWARD': 'WON_AWARD',
            'MEMBER_OF': 'MEMBER_OF',
            'RELEASED': 'RELEASED',
            'BELONGS_TO': 'BELONGS_TO'
        }

    def generate_path_query(self, entities: List[str], max_hops: int = 3) -> str:
        """
        Generate Cypher query to find paths between entities.

        Args:
            entities: List of entity names to search for
            max_hops: Maximum number of hops in paths

        Returns:
            Cypher query string
        """
        query = f"""
        MATCH path = (start)-[*1..{max_hops}]-(end)
        WHERE start.name IN $entity_names
        AND end.name IN $entity_names
        AND start <> end
        RETURN path,
               length(path) as path_length,
               [node IN nodes(path) | node.name] as node_names,
               [rel IN relationships(path) | type(rel)] as rel_types
        ORDER BY path_length
        LIMIT 50
        """

        return query

    def generate_entity_search_query(self, entity_name: str) -> str:
        """
        Generate Cypher query to find specific entity and its connections.

        Args:
            entity_name: Name of the entity to search for

        Returns:
            Cypher query string
        """
        query = """
        MATCH (n)
        WHERE n.name =~ $entity_pattern
        OPTIONAL MATCH (n)-[r]-(connected)
        RETURN n, collect({rel: r, connected: connected}) as connections
        ORDER BY n.name
        LIMIT 20
        """

        return query

    def generate_subgraph_query(self, entities: List[str], max_hops: int = 2) -> str:
        """
        Generate Cypher query to extract subgraph around entities.

        Args:
            entities: List of entity names
            max_hops: Maximum hops from entities

        Returns:
            Cypher query string
        """
        query = f"""
        MATCH (center)
        WHERE center.name IN $entity_names
        CALL {{
            WITH center
            MATCH path = (center)-[*1..{max_hops}]-(connected)
            WHERE connected <> center
            RETURN connected, length(path) as distance
        }}
        RETURN DISTINCT connected,
               min(distance) as min_distance,
               labels(connected) as node_labels
        ORDER BY min_distance, connected.name
        LIMIT 100
        """

        return query

    def generate_relation_query(self, entity1: str, entity2: str, relation_type: Optional[str] = None) -> str:
        """
        Generate Cypher query to check relation between two entities.

        Args:
            entity1: First entity name
            entity2: Second entity name
            relation_type: Optional relation type filter

        Returns:
            Cypher query string
        """
        if relation_type:
            query = f"""
            MATCH (a)-[r:{relation_type}]-(b)
            WHERE a.name = $entity1 AND b.name = $entity2
            RETURN a, r, b, type(r) as relation_type
            """
        else:
            query = """
            MATCH (a)-[r]-(b)
            WHERE a.name = $entity1 AND b.name = $entity2
            RETURN a, r, b, type(r) as relation_type
            """

        return query

    def generate_property_query(self, entity_name: str, properties: List[str]) -> str:
        """
        Generate Cypher query to get specific properties of an entity.

        Args:
            entity_name: Entity name
            properties: List of property names to retrieve

        Returns:
            Cypher query string
        """
        prop_string = ", ".join([f"n.{prop} as {prop}" for prop in properties])

        query = f"""
        MATCH (n)
        WHERE n.name = $entity_name
        RETURN n.name as name, {prop_string}
        """

        return query

    def parse_entities_from_query(self, query: str) -> List[str]:
        """
        Extract potential entity names from natural language query.

        Args:
            query: Natural language query

        Returns:
            List of potential entity names
        """
        # Simple entity extraction based on patterns
        # This could be enhanced with NER model

        # Look for quoted names
        quoted_names = re.findall(r'"([^"]+)"', query)
        if quoted_names:
            return quoted_names

        # Look for capitalized words (potential proper names)
        words = re.findall(r'\b[A-Z][a-z]+\b', query)
        potential_entities = []

        for word in words:
            # Skip common question words
            if word.lower() not in ['did', 'who', 'what', 'when', 'where', 'how', 'the', 'and', 'with']:
                potential_entities.append(word)

        # Also look for full names (two capitalized words)
        full_names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query)
        potential_entities.extend(full_names)

        return list(set(potential_entities))  # Remove duplicates

    def get_query_params(self, entities: List[str]) -> Dict[str, Any]:
        """
        Generate parameters for Cypher queries.

        Args:
            entities: List of entity names

        Returns:
            Dictionary of query parameters
        """
        # Create fuzzy matching patterns for entities
        entity_patterns = [f"(?i).*{re.escape(entity)}.*" for entity in entities]

        return {
            'entity_names': entities,
            'entity_patterns': entity_patterns
        }

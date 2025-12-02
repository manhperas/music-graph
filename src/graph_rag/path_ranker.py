"""
Path Ranking for GraphRAG.

This module ranks retrieved graph paths based on their relevance
to the user's query using various scoring mechanisms.
"""

from typing import List, Dict, Any, Tuple
import math
from collections import defaultdict


class PathRanker:
    """Ranks graph paths by relevance to query."""

    def __init__(self):
        self.weights = {
            'length_penalty': 0.1,      # Penalize longer paths
            'entity_match': 0.4,        # Reward paths connecting query entities
            'relation_relevance': 0.3,  # Reward relevant relation types
            'node_importance': 0.2      # Reward important nodes (based on degree/PageRank)
        }

    def rank_paths(self, paths: List[Dict[str, Any]], query: str, entities: List[str]) -> List[Dict[str, Any]]:
        """
        Rank paths by relevance to query.

        Args:
            paths: List of path dictionaries from Neo4j
            query: Original user query
            entities: Extracted entities from query

        Returns:
            Ranked list of paths with scores
        """
        ranked_paths = []

        for path in paths:
            score = self._calculate_path_score(path, query, entities)
            path_data = {
                'path': path,
                'score': score,
                'triples': self._extract_triples(path)
            }
            ranked_paths.append(path_data)

        # Sort by score (descending)
        ranked_paths.sort(key=lambda x: x['score'], reverse=True)

        return ranked_paths

    def _calculate_path_score(self, path: Dict[str, Any], query: str, entities: List[str]) -> float:
        """
        Calculate relevance score for a path.

        Args:
            path: Path data from Neo4j
            query: User query
            entities: Query entities

        Returns:
            Relevance score (0-1)
        """
        score = 0.0

        # Length penalty - shorter paths are better
        path_length = path.get('path_length', len(path.get('node_names', [])) - 1)
        length_score = math.exp(-self.weights['length_penalty'] * path_length)
        score += 0.2 * length_score

        # Entity match score
        node_names = path.get('node_names', [])
        entity_match_score = self._calculate_entity_match_score(node_names, entities)
        score += self.weights['entity_match'] * entity_match_score

        # Relation relevance score
        rel_types = path.get('rel_types', [])
        relation_score = self._calculate_relation_relevance_score(rel_types, query)
        score += self.weights['relation_relevance'] * relation_score

        # Node importance score (placeholder - would use PageRank in real implementation)
        importance_score = self._calculate_node_importance_score(node_names)
        score += self.weights['node_importance'] * importance_score

        return min(1.0, score)  # Cap at 1.0

    def _calculate_entity_match_score(self, node_names: List[str], query_entities: List[str]) -> float:
        """
        Calculate how well path nodes match query entities.

        Args:
            node_names: Names of nodes in path
            query_entities: Entities mentioned in query

        Returns:
            Match score (0-1)
        """
        if not query_entities:
            return 0.5  # Neutral score if no entities

        matches = 0
        for entity in query_entities:
            entity_lower = entity.lower()
            for node_name in node_names:
                if entity_lower in node_name.lower() or node_name.lower() in entity_lower:
                    matches += 1
                    break

        return matches / len(query_entities)

    def _calculate_relation_relevance_score(self, rel_types: List[str], query: str) -> float:
        """
        Calculate relevance of relation types to query.

        Args:
            rel_types: Types of relations in path
            query: User query

        Returns:
            Relevance score (0-1)
        """
        query_lower = query.lower()

        # Keywords that indicate interest in different relation types
        relation_keywords = {
            'COLLABORATES_WITH': ['collaborat', 'work with', 'together', 'feat', 'featuring'],
            'WON_AWARD': ['won', 'award', 'grammy', 'prize', 'winner'],
            'HAS_GENRE': ['genre', 'style', 'type of music', 'kind of'],
            'PERFORMS_ON': ['album', 'song', 'release', 'perform'],
            'MEMBER_OF': ['member', 'band', 'group', 'part of']
        }

        total_relevance = 0.0
        for rel_type in rel_types:
            rel_relevance = 0.0
            if rel_type in relation_keywords:
                keywords = relation_keywords[rel_type]
                for keyword in keywords:
                    if keyword in query_lower:
                        rel_relevance = 1.0
                        break

            # If no specific keyword match, give neutral score
            if rel_relevance == 0.0:
                rel_relevance = 0.5

            total_relevance += rel_relevance

        return total_relevance / len(rel_types) if rel_types else 0.5

    def _calculate_node_importance_score(self, node_names: List[str]) -> float:
        """
        Calculate importance score based on node names/types.
        In a real implementation, this would use PageRank scores.

        Args:
            node_names: Names of nodes in path

        Returns:
            Importance score (0-1)
        """
        # Simple heuristic: award winners and major artists score higher
        importance_indicators = [
            'grammy', 'award', 'winner', 'legend', 'icon',
            'billboard', 'top', 'best', 'famous', 'popular'
        ]

        total_importance = 0.0
        for node_name in node_names:
            node_importance = 0.3  # Base importance

            node_lower = node_name.lower()
            for indicator in importance_indicators:
                if indicator in node_lower:
                    node_importance = 0.8
                    break

            total_importance += node_importance

        return total_importance / len(node_names) if node_names else 0.3

    def _extract_triples(self, path: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        """
        Extract triples from path data.

        Args:
            path: Path dictionary from Neo4j

        Returns:
            List of (subject, relation, object) triples
        """
        triples = []

        # This is a simplified extraction
        # In real implementation, would parse the actual path structure

        node_names = path.get('node_names', [])
        rel_types = path.get('rel_types', [])

        if len(node_names) >= 2 and len(rel_types) >= 1:
            for i in range(len(rel_types)):
                if i + 1 < len(node_names):
                    subject = node_names[i]
                    relation = rel_types[i]
                    obj = node_names[i + 1]
                    triples.append((subject, relation, obj))

        return triples

    def filter_top_paths(self, ranked_paths: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Filter top K most relevant paths.

        Args:
            ranked_paths: Ranked list of paths
            top_k: Number of top paths to keep

        Returns:
            Top K paths
        """
        return ranked_paths[:top_k]

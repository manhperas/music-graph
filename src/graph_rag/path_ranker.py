from typing import List, Dict, Any, Tuple
import math
from collections import defaultdict

class PathRanker:

    def __init__(self):
        self.weights = {'length_penalty': 0.1, 'entity_match': 0.4, 'relation_relevance': 0.3, 'node_importance': 0.2}

    def rank_paths(self, paths: List[Dict[str, Any]], query: str, entities: List[str]) -> List[Dict[str, Any]]:
        ranked_paths = []
        for path in paths:
            score = self._calculate_path_score(path, query, entities)
            path_data = {'path': path, 'score': score, 'triples': self._extract_triples(path)}
            ranked_paths.append(path_data)
        ranked_paths.sort(key=lambda x: x['score'], reverse=True)
        return ranked_paths

    def _calculate_path_score(self, path: Dict[str, Any], query: str, entities: List[str]) -> float:
        score = 0.0
        path_length = path.get('path_length', len(path.get('node_names', [])) - 1)
        length_score = math.exp(-self.weights['length_penalty'] * path_length)
        score += 0.2 * length_score
        node_names = path.get('node_names', [])
        entity_match_score = self._calculate_entity_match_score(node_names, entities)
        score += self.weights['entity_match'] * entity_match_score
        rel_types = path.get('rel_types', [])
        relation_score = self._calculate_relation_relevance_score(rel_types, query)
        score += self.weights['relation_relevance'] * relation_score
        importance_score = self._calculate_node_importance_score(node_names)
        score += self.weights['node_importance'] * importance_score
        return min(1.0, score)

    def _calculate_entity_match_score(self, node_names: List[str], query_entities: List[str]) -> float:
        if not query_entities:
            return 0.5
        matches = 0
        for entity in query_entities:
            entity_lower = entity.lower()
            for node_name in node_names:
                if entity_lower in node_name.lower() or node_name.lower() in entity_lower:
                    matches += 1
                    break
        return matches / len(query_entities)

    def _calculate_relation_relevance_score(self, rel_types: List[str], query: str) -> float:
        query_lower = query.lower()
        relation_keywords = {'COLLABORATES_WITH': ['collaborat', 'work with', 'together', 'feat', 'featuring'], 'WON_AWARD': ['won', 'award', 'grammy', 'prize', 'winner'], 'HAS_GENRE': ['genre', 'style', 'type of music', 'kind of'], 'PERFORMS_ON': ['album', 'song', 'release', 'perform'], 'MEMBER_OF': ['member', 'band', 'group', 'part of']}
        total_relevance = 0.0
        for rel_type in rel_types:
            rel_relevance = 0.0
            if rel_type in relation_keywords:
                keywords = relation_keywords[rel_type]
                for keyword in keywords:
                    if keyword in query_lower:
                        rel_relevance = 1.0
                        break
            if rel_relevance == 0.0:
                rel_relevance = 0.5
            total_relevance += rel_relevance
        return total_relevance / len(rel_types) if rel_types else 0.5

    def _calculate_node_importance_score(self, node_names: List[str]) -> float:
        importance_indicators = ['grammy', 'award', 'winner', 'legend', 'icon', 'billboard', 'top', 'best', 'famous', 'popular']
        total_importance = 0.0
        for node_name in node_names:
            node_importance = 0.3
            node_lower = node_name.lower()
            for indicator in importance_indicators:
                if indicator in node_lower:
                    node_importance = 0.8
                    break
            total_importance += node_importance
        return total_importance / len(node_names) if node_names else 0.3

    def _extract_triples(self, path: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        triples = []
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

    def filter_top_paths(self, ranked_paths: List[Dict[str, Any]], top_k: int=5) -> List[Dict[str, Any]]:
        return ranked_paths[:top_k]

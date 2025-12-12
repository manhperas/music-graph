from typing import List, Dict, Any, Optional
import re

class CypherQueryGenerator:

    def __init__(self):
        self.relation_types = {'COLLABORATES_WITH': 'COLLABORATES_WITH', 'PERFORMS_ON': 'PERFORMS_ON', 'HAS_GENRE': 'HAS_GENRE', 'WON_AWARD': 'WON_AWARD', 'MEMBER_OF': 'MEMBER_OF', 'RELEASED': 'RELEASED', 'BELONGS_TO': 'BELONGS_TO'}

    def generate_path_query(self, entities: List[str], max_hops: int=3) -> str:
        query = f'\n        MATCH path = (start)-[*1..{max_hops}]-(end)\n        WHERE start.name IN $entity_names\n        AND end.name IN $entity_names\n        AND start <> end\n        RETURN path,\n               length(path) as path_length,\n               [node IN nodes(path) | node.name] as node_names,\n               [rel IN relationships(path) | type(rel)] as rel_types\n        ORDER BY path_length\n        LIMIT 50\n        '
        return query

    def generate_entity_search_query(self, entity_name: str) -> str:
        query = '\n        MATCH (n)\n        WHERE n.name =~ $entity_pattern\n        OPTIONAL MATCH (n)-[r]-(connected)\n        RETURN n, collect({rel: r, connected: connected}) as connections\n        ORDER BY n.name\n        LIMIT 20\n        '
        return query

    def generate_subgraph_query(self, entities: List[str], max_hops: int=2) -> str:
        query = f'\n        MATCH (center)\n        WHERE center.name IN $entity_names\n        CALL {{\n            WITH center\n            MATCH path = (center)-[*1..{max_hops}]-(connected)\n            WHERE connected <> center\n            RETURN connected, length(path) as distance\n        }}\n        RETURN DISTINCT connected,\n               min(distance) as min_distance,\n               labels(connected) as node_labels\n        ORDER BY min_distance, connected.name\n        LIMIT 100\n        '
        return query

    def generate_relation_query(self, entity1: str, entity2: str, relation_type: Optional[str]=None) -> str:
        if relation_type:
            query = f'\n            MATCH (a)-[r:{relation_type}]-(b)\n            WHERE a.name = $entity1 AND b.name = $entity2\n            RETURN a, r, b, type(r) as relation_type\n            '
        else:
            query = '\n            MATCH (a)-[r]-(b)\n            WHERE a.name = $entity1 AND b.name = $entity2\n            RETURN a, r, b, type(r) as relation_type\n            '
        return query

    def generate_property_query(self, entity_name: str, properties: List[str]) -> str:
        prop_string = ', '.join([f'n.{prop} as {prop}' for prop in properties])
        query = f'\n        MATCH (n)\n        WHERE n.name = $entity_name\n        RETURN n.name as name, {prop_string}\n        '
        return query

    def parse_entities_from_query(self, query: str) -> List[str]:
        quoted_names = re.findall('"([^"]+)"', query)
        if quoted_names:
            return quoted_names
        words = re.findall('\\b[A-Z][a-z]+\\b', query)
        potential_entities = []
        for word in words:
            if word.lower() not in ['did', 'who', 'what', 'when', 'where', 'how', 'the', 'and', 'with']:
                potential_entities.append(word)
        full_names = re.findall('\\b[A-Z][a-z]+ [A-Z][a-z]+\\b', query)
        potential_entities.extend(full_names)
        return list(set(potential_entities))

    def get_query_params(self, entities: List[str]) -> Dict[str, Any]:
        entity_patterns = [f'(?i).*{re.escape(entity)}.*' for entity in entities]
        return {'entity_names': entities, 'entity_patterns': entity_patterns}

from typing import Tuple, List, Dict, Any

class TripleVerbalizer:

    def __init__(self):
        self.templates = {'COLLABORATES_WITH': ['{subject} collaborated with {object}', '{subject} worked together with {object}', '{subject} and {object} have collaborated', '{subject} has worked with {object}'], 'PERFORMS_ON': ['{subject} performs on the album {object}', '{subject} released {object}', "{subject}'s album {object}", '{object} is an album by {subject}'], 'HAS_GENRE': ['{subject} has the genre {object}', '{subject} is {object} music', '{subject} belongs to {object} genre', '{subject} plays {object}'], 'WON_AWARD': ['{subject} won {object}', '{subject} received the award {object}', '{object} was awarded to {subject}', '{subject} is a {object} winner'], 'MEMBER_OF': ['{subject} is a member of {object}', '{subject} belongs to the band {object}', '{subject} plays in {object}', '{object} includes {subject} as a member'], 'RELEASED': ['{subject} released {object}', '{object} was released by {subject}', '{subject} put out {object}', '{object} is a release by {subject}'], 'BELONGS_TO': ['{subject} belongs to {object}', '{subject} is part of {object}', '{object} contains {subject}']}
        self.default_templates = ['{subject} is connected to {object} through {relation}', '{subject} has a relationship with {object}: {relation}', '{subject} and {object} are linked by {relation}']

    def verbalize_triple(self, triple: Tuple[str, str, str]) -> str:
        subject, relation, obj = triple
        templates = self.templates.get(relation, self.default_templates)
        template = templates[0]
        verbalization = template.format(subject=self._format_entity_name(subject), object=self._format_entity_name(obj), relation=self._format_relation_name(relation))
        return verbalization

    def verbalize_triples(self, triples: List[Tuple[str, str, str]]) -> List[str]:
        return [self.verbalize_triple(triple) for triple in triples]

    def build_context_from_triples(self, triples: List[Tuple[str, str, str]], query: str='') -> str:
        if not triples:
            return 'No relevant information found in the knowledge graph.'
        verbalizations = self.verbalize_triples(triples)
        if len(verbalizations) == 1:
            context = verbalizations[0] + '.'
        elif len(verbalizations) == 2:
            context = verbalizations[0] + '. ' + verbalizations[1] + '.'
        else:
            most = verbalizations[:-1]
            last = verbalizations[-1]
            context = ', '.join(most) + ', and ' + last + '.'
        return context

    def _format_entity_name(self, name: str) -> str:
        if ' ' in name or any((char in name for char in ['(', ')', '"', "'"])):
            return f'"{name}"'
        return name

    def _format_relation_name(self, relation: str) -> str:
        readable = relation.replace('_', ' ').lower()
        return readable.capitalize()

    def get_relation_summary(self, triples: List[Tuple[str, str, str]]) -> Dict[str, Any]:
        relation_counts = {}
        entities = set()
        for subject, relation, obj in triples:
            entities.add(subject)
            entities.add(obj)
            if relation not in relation_counts:
                relation_counts[relation] = 0
            relation_counts[relation] += 1
        return {'total_triples': len(triples), 'unique_entities': len(entities), 'relation_distribution': relation_counts, 'entities': list(entities)}

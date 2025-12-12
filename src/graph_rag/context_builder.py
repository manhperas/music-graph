from typing import List, Dict, Any, Optional
from .verbalizer import TripleVerbalizer

class ContextBuilder:

    def __init__(self, verbalizer: Optional[TripleVerbalizer]=None):
        self.verbalizer = verbalizer or TripleVerbalizer()
        self.max_context_length = 2000
        self.max_triples_per_path = 5

    def build_context(self, ranked_paths: List[Dict[str, Any]], query: str='', max_length: Optional[int]=None) -> str:
        if not ranked_paths:
            return 'No relevant information found in the knowledge graph.'
        max_length = max_length or self.max_context_length
        context_parts = []
        total_length = 0
        for path_data in ranked_paths:
            if total_length >= max_length:
                break
            triples = path_data.get('triples', [])
            score = path_data.get('score', 0.0)
            triples = triples[:self.max_triples_per_path]
            if triples:
                path_context = self._build_path_context(triples, score)
                if total_length + len(path_context) > max_length:
                    remaining_length = max_length - total_length
                    if remaining_length > 100:
                        path_context = self._truncate_context(path_context, remaining_length)
                    else:
                        break
                context_parts.append(path_context)
                total_length += len(path_context)
        full_context = self._join_context_parts(context_parts, query)
        return full_context

    def _build_path_context(self, triples: List[tuple], score: float) -> str:
        verbalizations = self.verbalizer.verbalize_triples(triples)
        if len(verbalizations) == 1:
            context = verbalizations[0] + '.'
        elif len(verbalizations) == 2:
            context = f'{verbalizations[0]} and {verbalizations[1]}.'
        else:
            context = ', '.join(verbalizations[:-1]) + f', and {verbalizations[-1]}.'
        return context

    def _truncate_context(self, context: str, max_length: int) -> str:
        if len(context) <= max_length:
            return context
        truncated = context[:max_length]
        last_period = truncated.rfind('.')
        last_comma = truncated.rfind(',')
        last_space = truncated.rfind(' ')
        break_point = max(last_period, last_comma, last_space)
        if break_point > max_length * 0.8:
            truncated = truncated[:break_point + 1]
        return truncated + '...'

    def _join_context_parts(self, context_parts: List[str], query: str) -> str:
        if not context_parts:
            return 'No relevant information found.'
        if len(context_parts) == 1:
            return context_parts[0]
        joined = '\n'.join(context_parts)
        return joined

    def build_answer_prompt(self, context: str, query: str) -> str:
        prompt = f'\nBased on the following information from the music knowledge graph:\n\n{context}\n\nPlease answer the question: {query}\n\nIf the information above is sufficient, provide a direct answer.\nIf more information is needed, say so clearly.\n'
        return prompt.strip()

    def get_context_stats(self, context: str) -> Dict[str, Any]:
        return {'length': len(context), 'sentences': len(context.split('.')), 'words': len(context.split()), 'lines': len(context.split('\n'))}

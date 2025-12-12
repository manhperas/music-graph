"""
Context Builder for GraphRAG.

This module builds coherent natural language context from
ranked graph paths for use in LLM generation.
"""

from typing import List, Dict, Any, Optional
from .verbalizer import TripleVerbalizer


class ContextBuilder:
    """Builds natural language context from graph paths."""

    def __init__(self, verbalizer: Optional[TripleVerbalizer] = None):
        self.verbalizer = verbalizer or TripleVerbalizer()
        self.max_context_length = 2000  # Maximum context length in characters
        self.max_triples_per_path = 5   # Max triples to include per path

    def build_context(self, ranked_paths: List[Dict[str, Any]],
                     query: str = "", max_length: Optional[int] = None) -> str:
        """
        Build coherent context from ranked paths.

        Args:
            ranked_paths: List of ranked path dictionaries
            query: Original user query
            max_length: Maximum context length (optional)

        Returns:
            Natural language context string
        """
        if not ranked_paths:
            return "No relevant information found in the knowledge graph."

        max_length = max_length or self.max_context_length
        context_parts = []
        total_length = 0

        for path_data in ranked_paths:
            if total_length >= max_length:
                break

            # Extract triples from path
            triples = path_data.get('triples', [])
            score = path_data.get('score', 0.0)

            # Limit triples per path
            triples = triples[:self.max_triples_per_path]

            if triples:
                # Build context for this path
                path_context = self._build_path_context(triples, score)

                # Check if adding this would exceed length
                if total_length + len(path_context) > max_length:
                    # Try to add a truncated version
                    remaining_length = max_length - total_length
                    if remaining_length > 100:  # Minimum useful length
                        path_context = self._truncate_context(path_context, remaining_length)
                    else:
                        break

                context_parts.append(path_context)
                total_length += len(path_context)

        # Join context parts
        full_context = self._join_context_parts(context_parts, query)

        return full_context

    def _build_path_context(self, triples: List[tuple], score: float) -> str:
        """
        Build context for a single path.

        Args:
            triples: List of triples in the path
            score: Relevance score of the path

        Returns:
            Context string for this path
        """
        # Verbalize triples
        verbalizations = self.verbalizer.verbalize_triples(triples)

        # Join into coherent paragraph
        if len(verbalizations) == 1:
            context = verbalizations[0] + "."
        elif len(verbalizations) == 2:
            context = f"{verbalizations[0]} and {verbalizations[1]}."
        else:
            # Join with commas and "and"
            context = ", ".join(verbalizations[:-1]) + f", and {verbalizations[-1]}."

        return context

    def _truncate_context(self, context: str, max_length: int) -> str:
        """
        Truncate context to fit within length limit.

        Args:
            context: Original context
            max_length: Maximum length

        Returns:
            Truncated context
        """
        if len(context) <= max_length:
            return context

        # Find a good break point (sentence end)
        truncated = context[:max_length]

        # Try to break at sentence end
        last_period = truncated.rfind('.')
        last_comma = truncated.rfind(',')
        last_space = truncated.rfind(' ')

        # Prefer breaking at period, then comma, then space
        break_point = max(last_period, last_comma, last_space)

        if break_point > max_length * 0.8:  # Don't truncate too much
            truncated = truncated[:break_point + 1]

        return truncated + "..."

    def _join_context_parts(self, context_parts: List[str], query: str) -> str:
        """
        Join multiple context parts into coherent whole.

        Args:
            context_parts: List of context strings
            query: Original query

        Returns:
            Joined context
        """
        if not context_parts:
            return "No relevant information found."

        if len(context_parts) == 1:
            return context_parts[0]

        # Join with newlines for readability
        joined = "\n".join(context_parts)

        return joined

    def build_answer_prompt(self, context: str, query: str) -> str:
        """
        Build complete prompt for LLM including context and query.

        Args:
            context: Built context from graph
            query: User query

        Returns:
            Complete prompt for LLM
        """
        prompt = f"""
Based on the following information from the music knowledge graph:

{context}

Please answer the question: {query}

If the information above is sufficient, provide a direct answer.
If more information is needed, say so clearly.
"""

        return prompt.strip()

    def get_context_stats(self, context: str) -> Dict[str, Any]:
        """
        Get statistics about the built context.

        Args:
            context: Built context string

        Returns:
            Statistics dictionary
        """
        return {
            'length': len(context),
            'sentences': len(context.split('.')),
            'words': len(context.split()),
            'lines': len(context.split('\n'))
        }

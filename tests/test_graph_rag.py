"""
Unit tests for GraphRAG components.
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_rag.cypher_gen import CypherQueryGenerator
from graph_rag.path_ranker import PathRanker
from graph_rag.verbalizer import TripleVerbalizer
from graph_rag.context_builder import ContextBuilder


class TestCypherQueryGenerator(unittest.TestCase):
    """Test CypherQueryGenerator."""

    def setUp(self):
        self.generator = CypherQueryGenerator()

    def test_parse_entities_from_query(self):
        """Test entity extraction from queries."""
        # Test with quoted names
        query = 'Did "Taylor Swift" collaborate with "Ed Sheeran"?'
        entities = self.generator.parse_entities_from_query(query)
        self.assertIn('Taylor Swift', entities)
        self.assertIn('Ed Sheeran', entities)

        # Test with capitalized words
        query = 'Did Taylor Swift win Grammy?'
        entities = self.generator.parse_entities_from_query(query)
        self.assertIn('Taylor', entities)
        self.assertIn('Swift', entities)

    def test_generate_path_query(self):
        """Test path query generation."""
        entities = ['Taylor Swift', 'Ed Sheeran']
        query = self.generator.generate_path_query(entities, max_hops=3)

        self.assertIn('MATCH path = (start)-[*1..3]-(end)', query)
        self.assertIn('start.name IN $entity_names', query)
        self.assertIn('end.name IN $entity_names', query)


class TestPathRanker(unittest.TestCase):
    """Test PathRanker."""

    def setUp(self):
        self.ranker = PathRanker()

    def test_calculate_entity_match_score(self):
        """Test entity match scoring."""
        node_names = ['Taylor Swift', 'Ed Sheeran', 'Grammy']
        query_entities = ['Taylor Swift', 'Ed Sheeran']

        score = self.ranker._calculate_entity_match_score(node_names, query_entities)
        self.assertEqual(score, 1.0)  # All entities matched

    def test_rank_paths(self):
        """Test path ranking."""
        paths = [
            {
                'node_names': ['Taylor Swift', 'Ed Sheeran'],
                'rel_types': ['COLLABORATES_WITH'],
                'path_length': 1
            },
            {
                'node_names': ['Taylor Swift', 'Unknown Artist', 'Ed Sheeran'],
                'rel_types': ['COLLABORATES_WITH', 'COLLABORATES_WITH'],
                'path_length': 2
            }
        ]

        query = "Did Taylor Swift collaborate with Ed Sheeran?"
        entities = ['Taylor Swift', 'Ed Sheeran']

        ranked = self.ranker.rank_paths(paths, query, entities)

        # First path should have higher score (shorter, direct connection)
        self.assertGreater(ranked[0]['score'], ranked[1]['score'])


class TestTripleVerbalizer(unittest.TestCase):
    """Test TripleVerbalizer."""

    def setUp(self):
        self.verbalizer = TripleVerbalizer()

    def test_verbalize_triple(self):
        """Test triple verbalization."""
        triple = ('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran')
        verbalization = self.verbalizer.verbalize_triple(triple)

        self.assertIn('Taylor Swift', verbalization)
        self.assertIn('collaborated with', verbalization.lower())
        self.assertIn('Ed Sheeran', verbalization)

    def test_verbalize_unknown_relation(self):
        """Test verbalization of unknown relation types."""
        triple = ('Taylor Swift', 'UNKNOWN_RELATION', 'Ed Sheeran')
        verbalization = self.verbalizer.verbalize_triple(triple)

        self.assertIn('Taylor Swift', verbalization)
        self.assertIn('Ed Sheeran', verbalization)
        self.assertIn('connected', verbalization.lower())

    def test_build_context_from_triples(self):
        """Test context building from multiple triples."""
        triples = [
            ('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran'),
            ('Ed Sheeran', 'WON_AWARD', 'Grammy')
        ]

        context = self.verbalizer.build_context_from_triples(triples)
        self.assertIn('Taylor Swift', context)
        self.assertIn('Ed Sheeran', context)
        self.assertIn('Grammy', context)


class TestContextBuilder(unittest.TestCase):
    """Test ContextBuilder."""

    def setUp(self):
        self.builder = ContextBuilder()

    def test_build_context_empty(self):
        """Test context building with no paths."""
        context = self.builder.build_context([])
        self.assertIn('No relevant information', context)

    def test_build_context_single_path(self):
        """Test context building with single path."""
        ranked_paths = [
            {
                'triples': [('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran')],
                'score': 0.8
            }
        ]

        context = self.builder.build_context(ranked_paths)
        self.assertIn('Taylor Swift', context)
        self.assertIn('collaborated', context.lower())

    def test_truncate_context(self):
        """Test context truncation."""
        long_context = "This is a very long context that should be truncated. " * 10
        truncated = self.builder._truncate_context(long_context, 50)

        self.assertLessEqual(len(truncated), 55)  # Allow some tolerance
        self.assertTrue(truncated.endswith('...'))


if __name__ == '__main__':
    unittest.main()

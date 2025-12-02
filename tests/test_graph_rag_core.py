"""
Core functionality tests for GraphRAG components.

This is a simplified test suite focusing on essential functionality.
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


class TestCoreFunctionality(unittest.TestCase):
    """Test core GraphRAG functionality."""

    def setUp(self):
        self.cypher_gen = CypherQueryGenerator()
        self.path_ranker = PathRanker()
        self.verbalizer = TripleVerbalizer()
        self.context_builder = ContextBuilder(self.verbalizer)

    def test_entity_extraction_basic(self):
        """Test basic entity extraction."""

        # Quoted entities
        entities = self.cypher_gen.parse_entities_from_query('Did "Taylor Swift" collaborate with "Ed Sheeran"?')
        self.assertIn('Taylor Swift', entities)
        self.assertIn('Ed Sheeran', entities)

        # Empty query
        entities = self.cypher_gen.parse_entities_from_query("")
        self.assertEqual(entities, [])

    def test_query_generation(self):
        """Test Cypher query generation."""

        entities = ['Taylor Swift', 'Ed Sheeran']
        query = self.cypher_gen.generate_path_query(entities, max_hops=2)

        self.assertIn('MATCH path = (start)-[*1..2]-(end)', query)
        self.assertIn('start.name IN $entity_names', query)
        self.assertIn('end.name IN $entity_names', query)

    def test_path_ranking(self):
        """Test path ranking functionality."""

        paths = [
            {
                'node_names': ['A', 'B'],  # Direct connection
                'rel_types': ['REL'],
                'path_length': 1
            },
            {
                'node_names': ['A', 'C', 'B'],  # 2-hop connection
                'rel_types': ['REL1', 'REL2'],
                'path_length': 2
            }
        ]

        query = "Connect A to B"
        entities = ['A', 'B']

        ranked = self.path_ranker.rank_paths(paths, query, entities)

        # Should return ranked paths
        self.assertEqual(len(ranked), 2)
        self.assertIn('score', ranked[0])
        self.assertIn('path', ranked[0])

    def test_triple_verbalization(self):
        """Test triple verbalization."""

        triple = ('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran')
        verbalization = self.verbalizer.verbalize_triple(triple)

        self.assertIn('Taylor Swift', verbalization)
        self.assertIn('Ed Sheeran', verbalization)
        self.assertIn('collaborated', verbalization.lower())

    def test_context_building(self):
        """Test context building."""

        ranked_paths = [
            {
                'triples': [('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran')],
                'score': 0.8
            }
        ]

        context = self.context_builder.build_context(ranked_paths)

        self.assertIn('Taylor Swift', context)
        self.assertIn('Ed Sheeran', context)
        self.assertIsInstance(context, str)

    def test_empty_context(self):
        """Test context building with no paths."""

        context = self.context_builder.build_context([])
        self.assertIn('No relevant information', context)

    def test_performance_basic(self):
        """Basic performance test."""

        import time

        # Test entity extraction performance
        queries = ['Did "A" work with "B"?' for _ in range(100)]

        start_time = time.time()
        for query in queries:
            entities = self.cypher_gen.parse_entities_from_query(query)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time = total_time / len(queries)

        # Should be fast (< 1ms per query)
        self.assertLess(avg_time, 0.001)
        print(".6f")

    def test_all_relations_supported(self):
        """Test that all relation types are supported."""

        relations = [
            'COLLABORATES_WITH',
            'PERFORMS_ON',
            'HAS_GENRE',
            'WON_AWARD',
            'MEMBER_OF',
            'RELEASED'
        ]

        for relation in relations:
            triple = ('Subject', relation, 'Object')
            verbalization = self.verbalizer.verbalize_triple(triple)

            # Should produce valid output
            self.assertIsInstance(verbalization, str)
            self.assertGreater(len(verbalization), 10)

    def test_path_filtering(self):
        """Test path filtering functionality."""

        ranked_paths = [
            {'score': 0.9, 'path': 'path1'},
            {'score': 0.8, 'path': 'path2'},
            {'score': 0.7, 'path': 'path3'},
            {'score': 0.6, 'path': 'path4'},
        ]

        top_paths = self.path_ranker.filter_top_paths(ranked_paths, top_k=2)

        self.assertEqual(len(top_paths), 2)
        self.assertEqual(top_paths[0]['score'], 0.9)
        self.assertEqual(top_paths[1]['score'], 0.8)


if __name__ == '__main__':
    unittest.main(verbosity=2)

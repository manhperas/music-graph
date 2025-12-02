"""
Integration tests for GraphRAG with mocked Neo4j driver.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_rag.retriever import GraphRAGRetriever


class TestGraphRAGRetrieverIntegration(unittest.TestCase):
    """Integration tests for GraphRAGRetriever with mocked Neo4j."""

    def setUp(self):
        """Set up test fixtures with mocked Neo4j driver."""
        self.mock_driver = MagicMock()

        # Create mock session
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__.return_value = self.mock_session

        # Initialize retriever with mock driver
        self.retriever = GraphRAGRetriever(self.mock_driver)

    def test_retrieve_context_successful_path(self):
        """Test successful retrieval with mock Neo4j data."""

        # Mock Neo4j result for path finding
        mock_result = MagicMock()
        mock_result.data.return_value = [
            {
                'path': Mock(),
                'path_length': 1,
                'node_names': ['Taylor Swift', 'Ed Sheeran'],
                'rel_types': ['COLLABORATES_WITH']
            }
        ]
        self.mock_session.run.return_value = mock_result

        # Test retrieval
        result = self.retriever.retrieve_context("Did Taylor Swift collaborate with Ed Sheeran?")

        # Verify results
        self.assertIn('context_text', result)
        self.assertIn('paths', result)
        self.assertIn('entities', result)
        self.assertIn('Taylor Swift', result['context_text'])
        self.assertIn('Ed Sheeran', result['context_text'])

        # Verify Neo4j was called
        self.assertTrue(self.mock_session.run.called)

    def test_retrieve_context_no_entities(self):
        """Test retrieval when no entities are found."""

        result = self.retriever.retrieve_context("What is music?")

        self.assertIn('No entities found', result['context_text'])
        self.assertEqual(result['entities'], [])
        self.assertEqual(result['error'], 'no_entities')

    def test_retrieve_context_no_paths(self):
        """Test retrieval when no paths are found."""

        # Mock empty result
        mock_result = MagicMock()
        mock_result.data.return_value = []
        self.mock_session.run.return_value = mock_result

        result = self.retriever.retrieve_context("Did Taylor Swift collaborate with Ed Sheeran?")

        self.assertIn('No connections found', result['context_text'])
        self.assertEqual(result['error'], 'no_paths')

    def test_retrieve_context_database_error(self):
        """Test retrieval with database error."""

        # Mock database error
        self.mock_session.run.side_effect = Exception("Database connection failed")

        result = self.retriever.retrieve_context("Did Taylor Swift collaborate with Ed Sheeran?")

        self.assertIn('Error retrieving information', result['context_text'])
        self.assertIn('Database connection failed', result['error'])

    def test_find_graph_paths(self):
        """Test graph path finding with various scenarios."""

        # Mock successful path finding
        mock_result = MagicMock()
        mock_result.data.return_value = [
            {
                'path': Mock(),
                'path_length': 1,
                'node_names': ['A', 'B'],
                'rel_types': ['REL']
            },
            {
                'path': Mock(),
                'path_length': 2,
                'node_names': ['A', 'C', 'B'],
                'rel_types': ['REL1', 'REL2']
            }
        ]
        self.mock_session.run.return_value = mock_result

        entities = ['A', 'B']
        paths = self.retriever._find_graph_paths(entities, max_hops=3)

        self.assertEqual(len(paths), 2)
        self.assertEqual(paths[0]['path_length'], 1)
        self.assertEqual(paths[1]['path_length'], 2)

    def test_get_entity_info(self):
        """Test entity information retrieval."""

        # Mock entity info result
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            'n': {'name': 'Taylor Swift', 'type': 'Artist'},
            'labels': ['Artist']
        }[key]

        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result

        info = self.retriever.get_entity_info("Taylor Swift")

        self.assertIsNotNone(info)
        self.assertEqual(info['labels'], ['Artist'])

    def test_get_entity_info_not_found(self):
        """Test entity information retrieval when entity not found."""

        mock_result = MagicMock()
        mock_result.single.return_value = None
        self.mock_session.run.return_value = mock_result

        info = self.retriever.get_entity_info("Nonexistent Entity")

        self.assertIsNone(info)

    def test_search_similar_entities(self):
        """Test similar entity search."""

        mock_result = MagicMock()
        mock_result.data.return_value = [
            {'name': 'Taylor Swift'},
            {'name': 'Taylor Lautner'},
            {'name': 'Taylor Schilling'}
        ]
        self.mock_session.run.return_value = mock_result

        similar = self.retriever.search_similar_entities("Taylor", limit=5)

        self.assertEqual(len(similar), 3)
        self.assertIn('Taylor Swift', similar)

    def test_analyze_query_complexity(self):
        """Test query complexity analysis."""

        # Simple query
        analysis = self.retriever.analyze_query_complexity("Who is Taylor Swift?")
        self.assertEqual(analysis['complexity_level'], 'simple')
        self.assertEqual(analysis['entity_count'], 1)

        # Complex query
        analysis = self.retriever.analyze_query_complexity(
            "Did Taylor Swift collaborate with Ed Sheeran and Billie Eilish?"
        )
        self.assertEqual(analysis['complexity_level'], 'complex')
        self.assertEqual(analysis['entity_count'], 3)

    def test_different_query_types(self):
        """Test different types of queries."""

        test_queries = [
            "Did Taylor Swift collaborate with Ed Sheeran?",  # Collaboration
            "What awards has Taylor Swift won?",            # Awards
            "What genre does The Beatles play?",             # Genre
            "What albums has Eminem released?",              # Albums
            "Did Taylor Swift work with anyone who won Grammy 2020?",  # Complex
        ]

        for query in test_queries:
            with self.subTest(query=query):
                # Mock some paths for each query
                mock_result = MagicMock()
                mock_result.data.return_value = [
                    {
                        'path': Mock(),
                        'path_length': 1,
                        'node_names': ['Entity1', 'Entity2'],
                        'rel_types': ['RELATION']
                    }
                ]
                self.mock_session.run.return_value = mock_result

                result = self.retriever.retrieve_context(query)

                # Should not crash and return some result
                self.assertIn('context_text', result)
                self.assertIsInstance(result['context_text'], str)


class TestGraphRAGRetrieverWithLLM(unittest.TestCase):
    """Test GraphRAGRetriever with LLM integration (mocked)."""

    def setUp(self):
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__.return_value = self.mock_session

        # Mock LLM
        self.mock_llm = MagicMock()
        self.mock_llm.extract_entities.return_value = ['Mock Entity']

        self.retriever = GraphRAGRetriever(self.mock_driver, self.mock_llm)

    def test_entity_extraction_with_llm(self):
        """Test entity extraction using mocked LLM."""

        entities = self.retriever._extract_entities("Some query")

        # Should call LLM method
        self.assertTrue(self.mock_llm.extract_entities.called)
        self.assertIn('Mock Entity', entities)

    def test_entity_extraction_fallback(self):
        """Test entity extraction fallback when LLM fails."""

        self.mock_llm.extract_entities.side_effect = Exception("LLM failed")

        # Should still work with pattern-based extraction
        entities = self.retriever._extract_entities('Did "Taylor Swift" collaborate?')

        self.assertIn('Taylor Swift', entities)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def setUp(self):
        self.mock_driver = MagicMock()
        self.retriever = GraphRAGRetriever(self.mock_driver)

    def test_driver_initialization_error(self):
        """Test handling of driver initialization errors."""

        with patch('graph_rag.retriever.GraphDatabase.driver', side_effect=Exception("Connection failed")):
            with self.assertRaises(Exception):
                GraphRAGRetriever(None)

    def test_session_creation_error(self):
        """Test handling of session creation errors."""

        self.mock_driver.session.side_effect = Exception("Session creation failed")

        result = self.retriever.retrieve_context("Test query")

        self.assertIn('Error retrieving information', result['context_text'])

    def test_partial_result_handling(self):
        """Test handling of partial results from Neo4j."""

        # Mock result with some missing fields
        mock_result = MagicMock()
        mock_result.data.return_value = [
            {
                'path': Mock(),
                'path_length': 1,
                # Missing node_names and rel_types
            }
        ]
        self.mock_driver.session.return_value.__enter__.return_value.run.return_value = mock_result

        # Should handle gracefully without crashing
        result = self.retriever.retrieve_context("Test query")

        self.assertIn('context_text', result)


class TestPerformanceIntegration(unittest.TestCase):
    """Integration performance tests."""

    def setUp(self):
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__.return_value = self.mock_session

        self.retriever = GraphRAGRetriever(self.mock_driver)

    def test_batch_query_performance(self):
        """Test performance with multiple queries."""

        # Mock consistent response
        mock_result = MagicMock()
        mock_result.data.return_value = [
            {
                'path': Mock(),
                'path_length': 1,
                'node_names': ['Entity1', 'Entity2'],
                'rel_types': ['RELATION']
            }
        ]
        self.mock_session.run.return_value = mock_result

        queries = [
            "Did Artist1 collaborate with Artist2?",
            "What awards has Artist3 won?",
            "What genre does Band1 play?",
        ] * 5  # 15 queries total

        import time
        start_time = time.time()

        for query in queries:
            result = self.retriever.retrieve_context(query)

        end_time = time.time()
        total_time = end_time - start_time

        # Should handle 15 queries reasonably fast
        self.assertLess(total_time, 2.0)  # Less than 2 seconds

        avg_time = total_time / len(queries)
        print(f"\nBatch query performance: {avg_time:.4f}s per query")


if __name__ == '__main__':
    unittest.main(verbosity=2)

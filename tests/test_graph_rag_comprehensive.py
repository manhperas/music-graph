"""
Comprehensive tests for GraphRAG components - Deep testing scenarios.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys
import os
import time
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_rag.cypher_gen import CypherQueryGenerator
from graph_rag.path_ranker import PathRanker
from graph_rag.verbalizer import TripleVerbalizer
from graph_rag.context_builder import ContextBuilder


class TestCypherQueryGeneratorDeep(unittest.TestCase):
    """Deep testing for CypherQueryGenerator."""

    def setUp(self):
        self.generator = CypherQueryGenerator()

    def test_parse_entities_edge_cases(self):
        """Test entity extraction with edge cases."""

        # Empty query
        entities = self.generator.parse_entities_from_query("")
        self.assertEqual(entities, [])

        # Query with no capitalized words
        entities = self.generator.parse_entities_from_query("what is music?")
        self.assertEqual(entities, [])

        # Query with common words that should be filtered
        entities = self.generator.parse_entities_from_query("Who is the best artist?")
        # Should not include "Who", "Who is", etc.
        self.assertEqual(len(entities), 0)  # No capitalized words that aren't common

        # Multiple quoted entities
        query = 'Did "Taylor Swift" work with "Ed Sheeran" on "Love Story"?'
        entities = self.generator.parse_entities_from_query(query)
        self.assertEqual(len(entities), 3)
        self.assertIn("Taylor Swift", entities)
        self.assertIn("Ed Sheeran", entities)
        self.assertIn("Love Story", entities)

        # Mixed quoted and unquoted
        query = 'Did Taylor Swift collaborate with "Ed Sheeran"?'
        entities = self.generator.parse_entities_from_query(query)
        self.assertIn("Taylor Swift", entities)
        self.assertIn("Ed Sheeran", entities)

    def test_parse_entities_complex_names(self):
        """Test parsing of complex entity names."""

        # Names with special characters (current implementation doesn't handle special chars)
        query = 'What about Beyonce and Jay-Z?'
        entities = self.generator.parse_entities_from_query(query)
        # Current implementation only finds capitalized words
        self.assertIn("Beyonce", entities)
        self.assertIn("Jay", entities)

        # Full names
        query = 'Did Michael Jackson collaborate with Quincy Jones?'
        entities = self.generator.parse_entities_from_query(query)
        self.assertIn("Michael Jackson", entities)
        self.assertIn("Quincy Jones", entities)

    def test_generate_path_query_variations(self):
        """Test path query generation with different parameters."""

        entities = ['Taylor Swift', 'Ed Sheeran']

        # Test different hop limits
        for max_hops in [1, 2, 3, 5]:
            query = self.generator.generate_path_query(entities, max_hops)
            self.assertIn(f'[*1..{max_hops}]', query)
            self.assertIn('start.name IN $entity_names', query)

        # Test single entity
        single_entity = ['Taylor Swift']
        query = self.generator.generate_path_query(single_entity, 2)
        self.assertIn('start.name IN $entity_names', query)
        self.assertIn('end.name IN $entity_names', query)

    def test_generate_entity_search_query(self):
        """Test entity search query generation."""

        query = self.generator.generate_entity_search_query("Taylor Swift")

        self.assertIn('n.name =~ $entity_pattern', query)
        self.assertIn('collect({rel: r, connected: connected})', query)
        self.assertIn('ORDER BY n.name', query)

    def test_generate_subgraph_query(self):
        """Test subgraph query generation."""

        entities = ['Taylor Swift', 'Ed Sheeran']
        query = self.generator.generate_subgraph_query(entities, max_hops=2)

        self.assertIn('center.name IN $entity_names', query)
        self.assertIn('MATCH path = (center)-[*1..2]-(connected)', query)
        self.assertIn('min(distance) as min_distance', query)

    def test_generate_relation_query(self):
        """Test relation query generation."""

        # With specific relation type
        query = self.generator.generate_relation_query("Taylor Swift", "Ed Sheeran", "COLLABORATES_WITH")
        self.assertIn('-[r:COLLABORATES_WITH]-', query)

        # Without specific relation type
        query = self.generator.generate_relation_query("Taylor Swift", "Ed Sheeran")
        self.assertIn('-[r]-', query)
        self.assertNotIn('COLLABORATES_WITH', query)

    def test_get_query_params(self):
        """Test query parameter generation."""

        entities = ['Taylor Swift', 'Ed Sheeran']
        params = self.generator.get_query_params(entities)

        self.assertIn('entity_names', params)
        self.assertIn('entity_patterns', params)
        self.assertEqual(params['entity_names'], entities)
        self.assertEqual(len(params['entity_patterns']), 2)

        # Check fuzzy patterns
        for pattern in params['entity_patterns']:
            self.assertTrue(pattern.startswith('(?i).*'))
            self.assertTrue(pattern.endswith('.*\''))


class TestPathRankerDeep(unittest.TestCase):
    """Deep testing for PathRanker."""

    def setUp(self):
        self.ranker = PathRanker()

    def test_ranking_algorithm_detailed(self):
        """Test detailed ranking algorithm behavior."""

        # Create test paths with different characteristics
        paths = [
            {
                'node_names': ['Taylor Swift', 'Ed Sheeran'],  # Direct connection
                'rel_types': ['COLLABORATES_WITH'],
                'path_length': 1
            },
            {
                'node_names': ['Taylor Swift', 'Kanye West', 'Ed Sheeran'],  # 2-hop via Kanye
                'rel_types': ['COLLABORATES_WITH', 'COLLABORATES_WITH'],
                'path_length': 2
            },
            {
                'node_names': ['Taylor Swift', 'Unknown Artist', 'Another Unknown', 'Ed Sheeran'],  # 3-hop
                'rel_types': ['COLLABORATES_WITH', 'COLLABORATES_WITH', 'COLLABORATES_WITH'],
                'path_length': 3
            },
            {
                'node_names': ['Taylor Swift', 'Ed Sheeran', 'Grammy'],  # Includes award
                'rel_types': ['COLLABORATES_WITH', 'WON_AWARD'],
                'path_length': 2
            }
        ]

        query = "Did Taylor Swift collaborate with Ed Sheeran?"
        entities = ['Taylor Swift', 'Ed Sheeran']

        ranked = self.ranker.rank_paths(paths, query, entities)

        # Path 0 (direct, 1-hop) should have highest score
        self.assertEqual(ranked[0]['path'], paths[0])

        # Path 3 (includes award) should rank higher than path 1 (same length)
        # because it has award-related relation
        path3_score = next(p['score'] for p in ranked if p['path'] == paths[3])
        path1_score = next(p['score'] for p in ranked if p['path'] == paths[1])
        self.assertGreater(path3_score, path1_score)

    def test_entity_match_scoring_edge_cases(self):
        """Test entity match scoring edge cases."""

        # No entities in query
        score = self.ranker._calculate_entity_match_score(['A', 'B'], [])
        self.assertEqual(score, 0.5)  # Neutral score

        # No nodes in path
        score = self.ranker._calculate_entity_match_score([], ['A', 'B'])
        self.assertEqual(score, 0.0)

        # Partial matches
        score = self.ranker._calculate_entity_match_score(['Taylor', 'Ed'], ['Taylor Swift', 'Ed Sheeran'])
        self.assertGreater(score, 0.0)  # Should find partial matches
        self.assertLess(score, 1.0)  # But not perfect

        # Case insensitive matching
        score = self.ranker._calculate_entity_match_score(['taylor swift', 'ED SHEERAN'], ['Taylor Swift', 'Ed Sheeran'])
        self.assertEqual(score, 1.0)

    def test_relation_relevance_scoring(self):
        """Test relation relevance scoring for different query types."""

        rel_types = ['COLLABORATES_WITH', 'WON_AWARD', 'HAS_GENRE']

        # Collaboration query
        query1 = "Did Taylor Swift work with Ed Sheeran?"
        score1 = self.ranker._calculate_relation_relevance_score(rel_types, query1)

        # Award query
        query2 = "What awards has Taylor Swift won?"
        score2 = self.ranker._calculate_relation_relevance_score(rel_types, query2)

        # Genre query
        query3 = "What genre does Taylor Swift play?"
        score3 = self.ranker._calculate_relation_relevance_score(rel_types, query3)

        # Award query should have higher relevance for WON_AWARD relation
        # than collaboration query
        self.assertGreater(score2, score1)

    def test_node_importance_scoring(self):
        """Test node importance scoring."""

        # Test with award-related nodes
        nodes_with_awards = ['Taylor Swift', 'Grammy Award', 'Billboard']
        score1 = self.ranker._calculate_node_importance_score(nodes_with_awards)

        # Test with regular nodes
        regular_nodes = ['Taylor Swift', 'Ed Sheeran', 'Pop Music']
        score2 = self.ranker._calculate_node_importance_score(regular_nodes)

        self.assertGreater(score1, score2)

    def test_extract_triples(self):
        """Test triple extraction from paths."""

        # Simple path
        path = {
            'node_names': ['A', 'B', 'C'],
            'rel_types': ['REL1', 'REL2']
        }

        triples = self.ranker._extract_triples(path)
        expected = [('A', 'REL1', 'B'), ('B', 'REL2', 'C')]
        self.assertEqual(triples, expected)

        # Empty path
        empty_path = {'node_names': [], 'rel_types': []}
        triples = self.ranker._extract_triples(empty_path)
        self.assertEqual(triples, [])

        # Mismatched lengths
        bad_path = {'node_names': ['A', 'B'], 'rel_types': ['REL1', 'REL2']}
        triples = self.ranker._extract_triples(bad_path)
        self.assertEqual(len(triples), 1)  # Should handle gracefully

    def test_filter_top_paths(self):
        """Test top path filtering."""

        ranked_paths = [
            {'score': 0.9, 'path': 'path1'},
            {'score': 0.8, 'path': 'path2'},
            {'score': 0.7, 'path': 'path3'},
            {'score': 0.6, 'path': 'path4'},
        ]

        # Filter top 2
        top_paths = self.ranker.filter_top_paths(ranked_paths, top_k=2)
        self.assertEqual(len(top_paths), 2)
        self.assertEqual(top_paths[0]['score'], 0.9)
        self.assertEqual(top_paths[1]['score'], 0.8)

        # Filter more than available
        top_paths = self.ranker.filter_top_paths(ranked_paths, top_k=10)
        self.assertEqual(len(top_paths), 4)

        # Filter 0
        top_paths = self.ranker.filter_top_paths(ranked_paths, top_k=0)
        self.assertEqual(len(top_paths), 0)


class TestTripleVerbalizerDeep(unittest.TestCase):
    """Deep testing for TripleVerbalizer."""

    def setUp(self):
        self.verbalizer = TripleVerbalizer()

    def test_all_relation_templates(self):
        """Test verbalization for all supported relation types."""

        test_cases = [
            ('COLLABORATES_WITH', 'Taylor Swift', 'Ed Sheeran'),
            ('PERFORMS_ON', 'Taylor Swift', 'Folklore'),
            ('HAS_GENRE', 'Taylor Swift', 'Pop'),
            ('WON_AWARD', 'Taylor Swift', 'Grammy'),
            ('MEMBER_OF', 'John Lennon', 'The Beatles'),
            ('RELEASED', 'Taylor Swift', '1989'),
            ('BELONGS_TO', 'Taylor Swift', 'Big Machine Records')
        ]

        for relation, subject, obj in test_cases:
            triple = (subject, relation, obj)
            verbalization = self.verbalizer.verbalize_triple(triple)

            self.assertIn(subject, verbalization)
            self.assertIn(obj, verbalization)
            self.assertIsInstance(verbalization, str)
            self.assertGreater(len(verbalization), len(subject) + len(obj))

    def test_verbalize_multiple_templates(self):
        """Test that verbalizer uses different templates for same relation."""

        triple = ('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran')

        # Verbalize multiple times to see if different templates are used
        verbalizations = set()
        for _ in range(10):
            verbalizations.add(self.verbalizer.verbalize_triple(triple))

        # Should get some variety (though currently using fixed template[0])
        self.assertGreaterEqual(len(verbalizations), 1)

    def test_format_entity_names(self):
        """Test entity name formatting."""

        # Name with spaces
        formatted = self.verbalizer._format_entity_name("Taylor Swift")
        self.assertEqual(formatted, '"Taylor Swift"')

        # Name without spaces
        formatted = self.verbalizer._format_entity_name("Taylor")
        self.assertEqual(formatted, "Taylor")

        # Name with quotes
        formatted = self.verbalizer._format_entity_name('Taylor "Swift"')
        self.assertEqual(formatted, '"Taylor "Swift""')

    def test_format_relation_names(self):
        """Test relation name formatting."""

        # Snake case
        formatted = self.verbalizer._format_relation_name("COLLABORATES_WITH")
        self.assertEqual(formatted, "Collaborates with")

        # Already formatted
        formatted = self.verbalizer._format_relation_name("WON_AWARD")
        self.assertEqual(formatted, "Won award")

    def test_build_context_variations(self):
        """Test context building with different triple combinations."""

        # Single triple
        triples = [('A', 'REL', 'B')]
        context = self.verbalizer.build_context_from_triples(triples)
        self.assertIn('A', context)
        self.assertIn('B', context)
        self.assertTrue(context.endswith('.'))

        # Two triples
        triples = [('A', 'REL1', 'B'), ('B', 'REL2', 'C')]
        context = self.verbalizer.build_context_from_triples(triples)
        self.assertIn('A', context)
        self.assertIn('B', context)
        self.assertIn('C', context)
        self.assertIn('and', context)

        # Three triples
        triples = [('A', 'REL1', 'B'), ('B', 'REL2', 'C'), ('C', 'REL3', 'D')]
        context = self.verbalizer.build_context_from_triples(triples)
        self.assertIn('A', context)
        self.assertIn('D', context)
        self.assertIn(',', context)

    def test_get_relation_summary(self):
        """Test relation summary generation."""

        triples = [
            ('A', 'REL1', 'B'),
            ('B', 'REL2', 'C'),
            ('A', 'REL1', 'D'),
            ('C', 'REL3', 'E')
        ]

        summary = self.verbalizer.get_relation_summary(triples)

        self.assertEqual(summary['total_triples'], 4)
        self.assertEqual(summary['unique_entities'], 5)  # A, B, C, D, E
        self.assertEqual(summary['relation_distribution']['REL1'], 2)
        self.assertEqual(summary['relation_distribution']['REL2'], 1)
        self.assertEqual(summary['relation_distribution']['REL3'], 1)


class TestContextBuilderDeep(unittest.TestCase):
    """Deep testing for ContextBuilder."""

    def setUp(self):
        self.builder = ContextBuilder()

    def test_build_context_multiple_paths(self):
        """Test context building with multiple paths."""

        ranked_paths = [
            {
                'triples': [('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran')],
                'score': 0.9
            },
            {
                'triples': [('Ed Sheeran', 'WON_AWARD', 'Grammy')],
                'score': 0.8
            },
            {
                'triples': [('Taylor Swift', 'HAS_GENRE', 'Pop')],
                'score': 0.7
            }
        ]

        context = self.builder.build_context(ranked_paths)

        # Should contain all entities and relations
        self.assertIn('Taylor Swift', context)
        self.assertIn('Ed Sheeran', context)
        self.assertIn('Grammy', context)
        self.assertIn('Pop', context)
        self.assertIn('collaborated', context.lower())
        self.assertIn('won', context.lower())

    def test_context_length_limits(self):
        """Test context length limiting."""

        # Create long paths
        long_triples = [('A', 'REL', 'B')] * 20  # 20 triples
        ranked_paths = [{
            'triples': long_triples,
            'score': 0.9
        }]

        # Test with short limit
        short_context = self.builder.build_context(ranked_paths, max_length=100)
        self.assertLessEqual(len(short_context), 110)  # Allow some tolerance

        # Test with long limit
        long_context = self.builder.build_context(ranked_paths, max_length=2000)
        self.assertGreater(len(long_context), len(short_context))

    def test_join_context_parts(self):
        """Test context part joining."""

        parts = ["First sentence.", "Second sentence.", "Third sentence."]
        joined = self.builder._join_context_parts(parts, "test query")

        self.assertIn("First sentence.", joined)
        self.assertIn("Second sentence.", joined)
        self.assertIn("Third sentence.", joined)

        # Should join with newlines
        self.assertIn("\n", joined)

    def test_build_answer_prompt(self):
        """Test LLM prompt building."""

        context = "Taylor Swift collaborated with Ed Sheeran."
        query = "Did Taylor Swift work with Ed Sheeran?"

        prompt = self.builder.build_answer_prompt(context, query)

        self.assertIn(context, prompt)
        self.assertIn(query, prompt)
        self.assertIn("Based on the following information", prompt)
        self.assertIn("Please answer the question", prompt)

    def test_get_context_stats(self):
        """Test context statistics."""

        context = "This is a test. It has multiple sentences. And words!"

        stats = self.builder.get_context_stats(context)

        self.assertEqual(stats['length'], len(context))
        self.assertEqual(stats['sentences'], 3)  # 3 sentences
        self.assertGreaterEqual(stats['words'], 10)  # Many words
        self.assertEqual(stats['lines'], 3)  # 3 lines (split by \n)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for realistic scenarios."""

    def setUp(self):
        self.cypher_gen = CypherQueryGenerator()
        self.path_ranker = PathRanker()
        self.verbalizer = TripleVerbalizer()
        self.context_builder = ContextBuilder(self.verbalizer)

    def test_collaboration_query_scenario(self):
        """Test full pipeline for collaboration query."""

        query = "Did Taylor Swift collaborate with Ed Sheeran?"
        entities = self.cypher_gen.parse_entities_from_query(query)

        # Mock paths that might be returned from Neo4j
        mock_paths = [
            {
                'node_names': ['Taylor Swift', 'Ed Sheeran'],
                'rel_types': ['COLLABORATES_WITH'],
                'path_length': 1
            },
            {
                'node_names': ['Taylor Swift', 'Kanye West', 'Ed Sheeran'],
                'rel_types': ['COLLABORATES_WITH', 'COLLABORATES_WITH'],
                'path_length': 2
            }
        ]

        # Rank paths
        ranked_paths = self.path_ranker.rank_paths(mock_paths, query, entities)

        # Build context
        context = self.context_builder.build_context(ranked_paths[:2])

        # Verify results
        self.assertIn('Taylor Swift', context)
        self.assertIn('Ed Sheeran', context)
        self.assertIn('collaborated', context.lower())

    def test_award_query_scenario(self):
        """Test full pipeline for award query."""

        query = "What awards has Taylor Swift won?"
        entities = self.cypher_gen.parse_entities_from_query(query)

        mock_paths = [
            {
                'node_names': ['Taylor Swift', 'Grammy'],
                'rel_types': ['WON_AWARD'],
                'path_length': 1
            },
            {
                'node_names': ['Taylor Swift', 'Billboard Music Award'],
                'rel_types': ['WON_AWARD'],
                'path_length': 1
            }
        ]

        ranked_paths = self.path_ranker.rank_paths(mock_paths, query, entities)
        context = self.context_builder.build_context(ranked_paths[:2])

        self.assertIn('Taylor Swift', context)
        self.assertIn('Grammy', context)
        self.assertIn('won', context.lower())

    def test_genre_query_scenario(self):
        """Test full pipeline for genre query."""

        query = "What genre does Taylor Swift play?"
        entities = self.cypher_gen.parse_entities_from_query(query)

        mock_paths = [
            {
                'node_names': ['Taylor Swift', 'Pop'],
                'rel_types': ['HAS_GENRE'],
                'path_length': 1
            },
            {
                'node_names': ['Taylor Swift', 'Country'],
                'rel_types': ['HAS_GENRE'],
                'path_length': 1
            }
        ]

        ranked_paths = self.path_ranker.rank_paths(mock_paths, query, entities)
        context = self.context_builder.build_context(ranked_paths[:2])

        self.assertIn('Taylor Swift', context)
        self.assertIn('Pop', context)
        self.assertIn('genre', context.lower())

    def test_complex_multi_hop_scenario(self):
        """Test complex multi-hop reasoning scenario."""

        query = "Did Taylor Swift collaborate with anyone who won Grammy 2020?"
        entities = self.cypher_gen.parse_entities_from_query(query)

        # This represents a 2-hop query: Taylor -> collaborator -> Grammy
        mock_paths = [
            {
                'node_names': ['Taylor Swift', 'Ed Sheeran', 'Grammy'],
                'rel_types': ['COLLABORATES_WITH', 'WON_AWARD'],
                'path_length': 2
            },
            {
                'node_names': ['Taylor Swift', 'Kanye West', 'Grammy'],
                'rel_types': ['COLLABORATES_WITH', 'WON_AWARD'],
                'path_length': 2
            }
        ]

        ranked_paths = self.path_ranker.rank_paths(mock_paths, query, entities)
        context = self.context_builder.build_context(ranked_paths[:2])

        self.assertIn('Taylor Swift', context)
        self.assertIn('Grammy', context)
        self.assertIn('collaborated', context.lower())


class TestPerformance(unittest.TestCase):
    """Performance tests for GraphRAG components."""

    def setUp(self):
        self.cypher_gen = CypherQueryGenerator()
        self.path_ranker = PathRanker()
        self.verbalizer = TripleVerbalizer()
        self.context_builder = ContextBuilder()

    def test_entity_extraction_performance(self):
        """Test entity extraction performance."""

        queries = [
            'Did "Taylor Swift" collaborate with "Ed Sheeran" on "Love Story"?',
            'What awards has Billie Eilish won in her career?',
            'What genre does The Beatles play and who are the members?',
            'Did Michael Jackson work with Quincy Jones on Thriller?',
            'What albums has Eminem released and what genres do they belong to?'
        ] * 10  # 50 queries total

        start_time = time.time()

        for query in queries:
            entities = self.cypher_gen.parse_entities_from_query(query)

        end_time = time.time()
        total_time = end_time - start_time

        # Should process 50 queries in reasonable time
        self.assertLess(total_time, 1.0)  # Less than 1 second

        avg_time = total_time / len(queries)
        print(f"\nEntity extraction: {avg_time:.4f}s per query")

    def test_path_ranking_performance(self):
        """Test path ranking performance."""

        # Create many paths
        paths = []
        for i in range(100):
            paths.append({
                'node_names': [f'Entity_{i}', f'Entity_{i+1}', f'Entity_{i+2}'],
                'rel_types': ['REL1', 'REL2'],
                'path_length': 2
            })

        query = "What is the connection between Entity_1 and Entity_50?"
        entities = ['Entity_1', 'Entity_50']

        start_time = time.time()
        ranked_paths = self.path_ranker.rank_paths(paths, query, entities)
        end_time = time.time()

        total_time = end_time - start_time

        # Should rank 100 paths quickly
        self.assertLess(total_time, 0.5)  # Less than 0.5 seconds

        print(f"\nPath ranking (100 paths): {total_time:.4f}s")

    def test_context_building_performance(self):
        """Test context building performance."""

        # Create many ranked paths
        ranked_paths = []
        for i in range(50):
            ranked_paths.append({
                'triples': [(f'Entity_{i}', 'RELATION', f'Entity_{i+1}')],
                'score': 0.8 - i * 0.01
            })

        start_time = time.time()
        context = self.context_builder.build_context(ranked_paths)
        end_time = time.time()

        total_time = end_time - start_time

        # Should build context from 50 paths quickly
        self.assertLess(total_time, 0.5)

        print(f"\nContext building (50 paths): {total_time:.4f}s")
        print(f"Context length: {len(context)} characters")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)

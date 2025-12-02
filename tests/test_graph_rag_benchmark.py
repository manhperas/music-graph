"""
Benchmark tests for GraphRAG components.

This module provides comprehensive benchmarking for performance,
accuracy, and scalability testing.
"""

import unittest
import time
import statistics
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_rag.cypher_gen import CypherQueryGenerator
from graph_rag.path_ranker import PathRanker
from graph_rag.verbalizer import TripleVerbalizer
from graph_rag.context_builder import ContextBuilder


class BenchmarkQueries:
    """Standard benchmark query set."""

    SIMPLE_QUERIES = [
        "Who is Taylor Swift?",
        "What is pop music?",
        "Who won Grammy 2020?",
        "What genre does The Beatles play?",
        "Did Michael Jackson release Thriller?"
    ]

    COMPLEX_QUERIES = [
        "Did Taylor Swift collaborate with anyone who won Grammy 2020?",
        "What awards have artists who collaborated with Ed Sheeran won?",
        "Did any member of The Beatles collaborate with Taylor Swift?",
        "What genre do artists who won Grammy 2020 typically play?",
        "Did Taylor Swift work with anyone who worked with Michael Jackson?"
    ]

    ENTITY_RICH_QUERIES = [
        'Did "Taylor Swift" collaborate with "Ed Sheeran" on "Love Story"?',
        'What awards has "Billie Eilish" won in her career?',
        'What genre does "The Beatles" play and who are the members?',
        'Did "Michael Jackson" work with "Quincy Jones" on "Thriller"?',
        'What albums has "Eminem" released and what genres do they belong to?'
    ]


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarking tests."""

    def setUp(self):
        self.cypher_gen = CypherQueryGenerator()
        self.path_ranker = PathRanker()
        self.verbalizer = TripleVerbalizer()
        self.context_builder = ContextBuilder()

    def benchmark_entity_extraction(self):
        """Benchmark entity extraction performance."""

        queries = BenchmarkQueries.SIMPLE_QUERIES + BenchmarkQueries.COMPLEX_QUERIES + BenchmarkQueries.ENTITY_RICH_QUERIES

        times = []

        for query in queries:
            start_time = time.perf_counter()
            entities = self.cypher_gen.parse_entities_from_query(query)
            end_time = time.perf_counter()

            times.append(end_time - start_time)

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile

        print("
📊 Entity Extraction Benchmark:"        print(f"  Queries tested: {len(queries)}")
        print(f"  Average time: {avg_time:.6f}s")
        print(f"  Median time: {median_time:.6f}s")
        print(f"  95th percentile: {p95_time:.6f}s")
        print(f"  Min time: {min(times):.6f}s")
        print(f"  Max time: {max(times):.6f}s")

        # Performance assertions
        self.assertLess(avg_time, 0.001)  # Should be very fast
        self.assertLess(p95_time, 0.005)  # 95% should be under 5ms

        return {
            'avg_time': avg_time,
            'median_time': median_time,
            'p95_time': p95_time,
            'min_time': min(times),
            'max_time': max(times)
        }

    def benchmark_path_ranking(self):
        """Benchmark path ranking performance."""

        # Create test paths of different sizes
        test_scenarios = [
            (10, "Small graph"),
            (100, "Medium graph"),
            (500, "Large graph")
        ]

        results = {}

        for num_paths, scenario_name in test_scenarios:
            # Generate test paths
            paths = []
            for i in range(num_paths):
                paths.append({
                    'node_names': [f'Entity_{i}', f'Entity_{i+1}', f'Entity_{i+2}'],
                    'rel_types': ['REL1', 'REL2'],
                    'path_length': 2
                })

            query = "What connects Entity_1 and Entity_50?"
            entities = ['Entity_1', 'Entity_50']

            # Benchmark ranking
            times = []
            for _ in range(5):  # Run multiple times for stable measurement
                start_time = time.perf_counter()
                ranked_paths = self.path_ranker.rank_paths(paths, query, entities)
                end_time = time.perf_counter()

                times.append(end_time - start_time)

            avg_time = statistics.mean(times)
            median_time = statistics.median(times)

            print(f"\n📊 Path Ranking - {scenario_name} ({num_paths} paths):")
            print(f"  Average time: {avg_time:.6f}s")
            print(f"  Median time: {median_time:.6f}s")
            print(f"  Paths/second: {num_paths/avg_time:.0f}")

            # Performance assertions
            if num_paths == 10:
                self.assertLess(avg_time, 0.001)
            elif num_paths == 100:
                self.assertLess(avg_time, 0.01)
            elif num_paths == 500:
                self.assertLess(avg_time, 0.05)

            results[scenario_name] = {
                'num_paths': num_paths,
                'avg_time': avg_time,
                'median_time': median_time,
                'throughput': num_paths/avg_time
            }

        return results

    def benchmark_context_building(self):
        """Benchmark context building performance."""

        # Create test scenarios with different numbers of triples
        test_scenarios = [
            (5, "Small context"),
            (50, "Medium context"),
            (200, "Large context")
        ]

        results = {}

        for num_triples, scenario_name in test_scenarios:
            # Generate test triples
            triples = []
            for i in range(num_triples):
                triples.append((f'Subject_{i}', 'RELATION', f'Object_{i}'))

            ranked_paths = [{
                'triples': triples,
                'score': 0.8
            }]

            # Benchmark context building
            times = []
            for _ in range(5):
                start_time = time.perf_counter()
                context = self.context_builder.build_context(ranked_paths)
                end_time = time.perf_counter()

                times.append(end_time - start_time)

            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            context_length = len(context)

            print(f"\n📊 Context Building - {scenario_name} ({num_triples} triples):")
            print(f"  Average time: {avg_time:.6f}s")
            print(f"  Median time: {median_time:.6f}s")
            print(f"  Context length: {context_length} chars")
            print(f"  Triples/second: {num_triples/avg_time:.0f}")

            # Performance assertions
            self.assertLess(avg_time, 0.1)  # Should be reasonably fast
            self.assertGreater(context_length, num_triples * 10)  # Should produce substantial context

            results[scenario_name] = {
                'num_triples': num_triples,
                'avg_time': avg_time,
                'median_time': median_time,
                'context_length': context_length,
                'throughput': num_triples/avg_time
            }

        return results

    def test_end_to_end_performance(self):
        """Test end-to-end performance of the full pipeline."""

        # Simulate a complete query processing pipeline
        queries = BenchmarkQueries.COMPLEX_QUERIES[:3]  # Test 3 complex queries

        total_times = []

        for query in queries:
            start_time = time.perf_counter()

            # Step 1: Entity extraction
            entities = self.cypher_gen.parse_entities_from_query(query)

            # Step 2: Simulate path finding (mock data)
            mock_paths = [
                {
                    'node_names': entities[:2] if len(entities) >= 2 else ['Entity1', 'Entity2'],
                    'rel_types': ['RELATION'],
                    'path_length': 1
                }
            ] * 10  # 10 mock paths

            # Step 3: Path ranking
            ranked_paths = self.path_ranker.rank_paths(mock_paths, query, entities)

            # Step 4: Context building
            context = self.context_builder.build_context(ranked_paths[:3])

            end_time = time.perf_counter()
            total_times.append(end_time - start_time)

        avg_time = statistics.mean(total_times)

        print("
📊 End-to-End Pipeline Performance:"        print(f"  Queries tested: {len(queries)}")
        print(f"  Average total time: {avg_time:.6f}s")
        print(f"  Queries/second: {1/avg_time:.2f}")

        # Should handle complex queries in reasonable time
        self.assertLess(avg_time, 0.1)  # Under 100ms per query


class TestAccuracyBenchmarks(unittest.TestCase):
    """Accuracy and correctness benchmarking."""

    def setUp(self):
        self.cypher_gen = CypherQueryGenerator()
        self.path_ranker = PathRanker()
        self.verbalizer = TripleVerbalizer()
        self.context_builder = ContextBuilder()

    def test_entity_extraction_accuracy(self):
        """Test accuracy of entity extraction."""

        test_cases = [
            # (query, expected_entities)
            ('Did "Taylor Swift" collaborate with "Ed Sheeran"?', ['Taylor Swift', 'Ed Sheeran']),
            ('What awards has Billie Eilish won?', ['Billie Eilish']),
            ('What genre does The Beatles play?', ['The Beatles']),
            ('Did Michael Jackson release Thriller?', ['Michael Jackson', 'Thriller']),
            ('Who won Grammy 2020?', ['Grammy 2020']),
            ('What is pop music?', []),  # No entities
            ('Did "Artist A" and "Artist B" work together?', ['Artist A', 'Artist B']),
        ]

        correct_extractions = 0
        total_cases = len(test_cases)

        for query, expected_entities in test_cases:
            extracted = self.cypher_gen.parse_entities_from_query(query)

            # Check if all expected entities are found
            if set(expected_entities).issubset(set(extracted)):
                correct_extractions += 1
            else:
                print(f"  Mismatch in: '{query}'")
                print(f"    Expected: {expected_entities}")
                print(f"    Got: {extracted}")

        accuracy = correct_extractions / total_cases

        print("
📊 Entity Extraction Accuracy:"        print(f"  Test cases: {total_cases}")
        print(f"  Correct extractions: {correct_extractions}")
        print(f"  Accuracy: {accuracy:.2%}")

        # Should have high accuracy
        self.assertGreaterEqual(accuracy, 0.8)

    def test_path_ranking_correctness(self):
        """Test correctness of path ranking algorithm."""

        # Test case: Direct connection should rank higher than indirect
        paths = [
            {
                'node_names': ['A', 'B'],  # Direct connection
                'rel_types': ['DIRECT_REL'],
                'path_length': 1
            },
            {
                'node_names': ['A', 'C', 'B'],  # 2-hop connection
                'rel_types': ['REL1', 'REL2'],
                'path_length': 2
            },
            {
                'node_names': ['A', 'D', 'E', 'B'],  # 3-hop connection
                'rel_types': ['REL1', 'REL2', 'REL3'],
                'path_length': 3
            }
        ]

        query = "Is A connected to B?"
        entities = ['A', 'B']

        ranked = self.path_ranker.rank_paths(paths, query, entities)

        # Direct connection should be highest ranked
        self.assertEqual(ranked[0]['path'], paths[0])
        self.assertEqual(ranked[0]['path']['path_length'], 1)

        # Scores should decrease with path length
        self.assertGreater(ranked[0]['score'], ranked[1]['score'])
        self.assertGreater(ranked[1]['score'], ranked[2]['score'])

    def test_context_quality(self):
        """Test quality of generated context."""

        triples = [
            ('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran'),
            ('Ed Sheeran', 'WON_AWARD', 'Grammy'),
            ('Taylor Swift', 'HAS_GENRE', 'Pop')
        ]

        ranked_paths = [{
            'triples': triples,
            'score': 0.9
        }]

        context = self.context_builder.build_context(ranked_paths)

        # Context should contain all key information
        self.assertIn('Taylor Swift', context)
        self.assertIn('Ed Sheeran', context)
        self.assertIn('Grammy', context)
        self.assertIn('Pop', context)

        # Context should be coherent and grammatical
        self.assertTrue(context.endswith('.'))
        self.assertNotIn('undefined', context.lower())
        self.assertNotIn('null', context.lower())

        # Check context statistics
        stats = self.context_builder.get_context_stats(context)
        self.assertGreater(stats['sentences'], 0)
        self.assertGreater(stats['words'], 10)

    def test_relation_verbalization_completeness(self):
        """Test that all supported relations can be verbalized."""

        supported_relations = [
            'COLLABORATES_WITH',
            'PERFORMS_ON',
            'HAS_GENRE',
            'WON_AWARD',
            'MEMBER_OF',
            'RELEASED',
            'BELONGS_TO'
        ]

        for relation in supported_relations:
            triple = ('Subject', relation, 'Object')
            verbalization = self.verbalizer.verbalize_triple(triple)

            # Should produce valid text
            self.assertIsInstance(verbalization, str)
            self.assertGreater(len(verbalization), 5)
            self.assertIn('Subject', verbalization)
            self.assertIn('Object', verbalization)


class TestScalabilityBenchmarks(unittest.TestCase):
    """Scalability testing for GraphRAG components."""

    def setUp(self):
        self.path_ranker = PathRanker()
        self.context_builder = ContextBuilder()

    def test_path_ranking_scalability(self):
        """Test how path ranking scales with increasing path count."""

        path_counts = [10, 50, 100, 200, 500]

        scalability_results = {}

        for count in path_counts:
            # Generate paths
            paths = []
            for i in range(count):
                paths.append({
                    'node_names': [f'Node_{i}', f'Node_{i+1}'],
                    'rel_types': ['RELATION'],
                    'path_length': 1
                })

            query = "Find connections"
            entities = ['Node_1', 'Node_50']

            # Measure time
            start_time = time.perf_counter()
            ranked = self.path_ranker.rank_paths(paths, query, entities)
            end_time = time.perf_counter()

            processing_time = end_time - start_time

            scalability_results[count] = {
                'time': processing_time,
                'time_per_path': processing_time / count
            }

            print(f"  {count} paths: {processing_time:.6f}s ({processing_time/count*1000:.2f}ms per path)")

        # Check that time scales reasonably (should be roughly linear)
        time_per_path_10 = scalability_results[10]['time_per_path']
        time_per_path_500 = scalability_results[500]['time_per_path']

        # Should not degrade too much with scale
        degradation_ratio = time_per_path_500 / time_per_path_10
        self.assertLess(degradation_ratio, 2.0)  # Should not be more than 2x slower

    def test_memory_usage_estimate(self):
        """Estimate memory usage for large datasets."""

        # Create large path dataset
        large_paths = []
        for i in range(1000):
            large_paths.append({
                'node_names': [f'Entity_{j}' for j in range(10)],  # 10 nodes per path
                'rel_types': [f'Relation_{j}' for j in range(9)],  # 9 relations
                'path_length': 9
            })

        # Measure memory usage indirectly through processing time
        start_time = time.perf_counter()
        ranked = self.path_ranker.rank_paths(large_paths, "Test query", ['Entity_1'])
        end_time = time.perf_counter()

        processing_time = end_time - start_time

        print("
📊 Large Dataset Test (1000 complex paths):"        print(f"  Processing time: {processing_time:.6f}s")
        print(f"  Paths/second: {1000/processing_time:.0f}")

        # Should handle large datasets reasonably
        self.assertLess(processing_time, 1.0)  # Under 1 second for 1000 paths


def run_full_benchmark():
    """Run complete benchmark suite."""

    print("🚀 GraphRAG Comprehensive Benchmark Suite")
    print("=" * 60)

    # Performance benchmarks
    perf_test = TestPerformanceBenchmarks()
    perf_test.setUp()

    print("\n🔥 Performance Benchmarks:")
    entity_results = perf_test.benchmark_entity_extraction()
    path_results = perf_test.benchmark_path_ranking()
    context_results = perf_test.benchmark_context_building()
    perf_test.test_end_to_end_performance()

    # Accuracy benchmarks
    accuracy_test = TestAccuracyBenchmarks()
    accuracy_test.setUp()

    print("\n🎯 Accuracy Benchmarks:")
    accuracy_test.test_entity_extraction_accuracy()
    accuracy_test.test_path_ranking_correctness()
    accuracy_test.test_context_quality()
    accuracy_test.test_relation_verbalization_completeness()

    # Scalability benchmarks
    scale_test = TestScalabilityBenchmarks()
    scale_test.setUp()

    print("\n📈 Scalability Benchmarks:")
    scale_test.test_path_ranking_scalability()
    scale_test.test_memory_usage_estimate()

    print("\n✅ Benchmark Suite Complete!")
    print("\n📊 Summary:")
    print(f"  Entity extraction: {entity_results['avg_time']*1000:.2f}ms avg")
    print(f"  Path ranking (100 paths): {path_results['Medium graph']['avg_time']*1000:.2f}ms")
    print(f"  Context building (50 triples): {context_results['Medium context']['avg_time']*1000:.2f}ms")


if __name__ == '__main__':
    # Run benchmarks
    run_full_benchmark()

    # Also run unit tests
    unittest.main(verbosity=2)

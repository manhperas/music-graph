#!/usr/bin/env python3
"""
Validation Framework for Neo4j Database

This module provides comprehensive validation for Neo4j graph database:
- Node validation (orphans, duplicates, missing fields)
- Relationship validation (broken links, invalid types)
- Data completeness checks
- Quality metrics calculation

Usage:
    from scripts.validation_framework import ValidationFramework
    
    validator = ValidationFramework()
    results = validator.validate_all()
    validator.print_report(results)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from dotenv import load_dotenv
from src.data_collection.utils import logger


class ValidationFramework:
    """Comprehensive validation framework for Neo4j database"""
    
    def __init__(self, config_path: str = "config/neo4j_config.json",
                 output_dir: str = "data/validation"):
        """
        Initialize validation framework
        
        Args:
            config_path: Path to Neo4j configuration file
            output_dir: Directory to store validation reports
        """
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load Neo4j config
        self.config = self._load_config()
        
        # Load password from environment
        load_dotenv()
        self.password = os.getenv('NEO4J_PASS', 'password')
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(
            self.config['uri'],
            auth=(self.config['user'], self.password)
        )
        
        logger.info(f"Validation framework initialized")
        logger.info(f"  - Output directory: {self.output_dir}")
    
    def _load_config(self) -> Dict:
        """Load Neo4j configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading Neo4j config: {e}")
            return {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "database": "neo4j"
            }
    
    def validate_all(self) -> Dict:
        """
        Run all validation checks
        
        Returns:
            Dictionary containing all validation results
        """
        logger.info("Starting comprehensive validation...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "node_validation": self.validate_nodes(),
            "relationship_validation": self.validate_relationships(),
            "data_completeness": self.check_data_completeness(),
            "quality_metrics": self.calculate_quality_metrics()
        }
        
        # Save results
        report_file = self.output_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Validation completed. Report saved to: {report_file}")
        
        return results
    
    def validate_nodes(self) -> Dict:
        """
        Validate nodes: check for orphans, duplicates, and missing fields
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Validating nodes...")
        
        results = {
            "orphaned_nodes": {},
            "duplicate_ids": {},
            "missing_fields": {},
            "invalid_data": {},
            "summary": {}
        }
        
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Check for orphaned nodes (nodes without relationships)
            orphaned_query = """
                MATCH (n)
                WHERE NOT (n)--()
                RETURN labels(n)[0] AS label, count(n) AS count
            """
            result = session.run(orphaned_query)
            orphaned_counts = {record["label"]: record["count"] for record in result}
            
            # Get detailed orphaned nodes
            orphaned_details_query = """
                MATCH (n)
                WHERE NOT (n)--()
                RETURN labels(n)[0] AS label, n.id AS id, n.name AS name
                LIMIT 100
            """
            result = session.run(orphaned_details_query)
            orphaned_details = {}
            for record in result:
                label = record["label"]
                if label not in orphaned_details:
                    orphaned_details[label] = []
                orphaned_details[label].append({
                    "id": record["id"],
                    "name": record.get("name", "N/A")
                })
            
            results["orphaned_nodes"] = {
                "counts": orphaned_counts,
                "total": sum(orphaned_counts.values()),
                "details": orphaned_details
            }
            
            # Check for duplicate IDs (should be prevented by constraints, but verify)
            duplicate_query = """
                MATCH (n)
                WITH labels(n)[0] AS label, n.id AS id, count(*) AS count
                WHERE count > 1
                RETURN label, id, count
            """
            result = session.run(duplicate_query)
            duplicates = {}
            for record in result:
                label = record["label"]
                if label not in duplicates:
                    duplicates[label] = []
                duplicates[label].append({
                    "id": record["id"],
                    "count": record["count"]
                })
            
            results["duplicate_ids"] = {
                "found": len(duplicates) > 0,
                "details": duplicates
            }
            
            # Check for missing required fields
            missing_fields = {}
            
            # Check Artist nodes
            artist_missing_query = """
                MATCH (a:Artist)
                WHERE a.id IS NULL OR a.name IS NULL OR a.id = '' OR a.name = ''
                RETURN a.id AS id, a.name AS name,
                       CASE WHEN a.id IS NULL OR a.id = '' THEN 'missing_id' ELSE '' END +
                       CASE WHEN a.name IS NULL OR a.name = '' THEN 'missing_name' ELSE '' END AS missing
                LIMIT 100
            """
            result = session.run(artist_missing_query)
            artist_missing = []
            for record in result:
                artist_missing.append({
                    "id": record["id"],
                    "name": record["name"],
                    "missing_fields": record["missing"]
                })
            
            if artist_missing:
                missing_fields["Artist"] = artist_missing
            
            # Check Album nodes
            album_missing_query = """
                MATCH (a:Album)
                WHERE a.id IS NULL OR a.title IS NULL OR a.id = '' OR a.title = ''
                RETURN a.id AS id, a.title AS title,
                       CASE WHEN a.id IS NULL OR a.id = '' THEN 'missing_id' ELSE '' END +
                       CASE WHEN a.title IS NULL OR a.title = '' THEN 'missing_title' ELSE '' END AS missing
                LIMIT 100
            """
            result = session.run(album_missing_query)
            album_missing = []
            for record in result:
                album_missing.append({
                    "id": record["id"],
                    "title": record["title"],
                    "missing_fields": record["missing"]
                })
            
            if album_missing:
                missing_fields["Album"] = album_missing
            
            results["missing_fields"] = missing_fields
            
            # Check for invalid data patterns
            invalid_data = {}
            
            # Check for empty genres in Artists (not necessarily invalid, but worth noting)
            empty_genres_query = """
                MATCH (a:Artist)
                WHERE a.genres IS NULL OR a.genres = ''
                RETURN count(a) AS count
            """
            result = session.run(empty_genres_query)
            empty_genres_count = result.single()["count"]
            
            if empty_genres_count > 0:
                invalid_data["artists_without_genres"] = {
                    "count": empty_genres_count,
                    "severity": "low"
                }
            
            # Summary
            total_nodes_query = """
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
            """
            result = session.run(total_nodes_query)
            node_counts = {record["label"]: record["count"] for record in result}
            
            results["summary"] = {
                "total_nodes": sum(node_counts.values()),
                "node_counts": node_counts,
                "orphaned_count": sum(orphaned_counts.values()),
                "duplicates_found": len(duplicates) > 0,
                "missing_fields_count": sum(len(v) for v in missing_fields.values())
            }
        
        logger.info(f"  ✓ Node validation completed")
        logger.info(f"    - Total nodes: {results['summary']['total_nodes']}")
        logger.info(f"    - Orphaned nodes: {results['summary']['orphaned_count']}")
        logger.info(f"    - Duplicates found: {results['summary']['duplicates_found']}")
        
        return results
    
    def validate_relationships(self) -> Dict:
        """
        Validate relationships: check for broken links, invalid types, duplicates
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Validating relationships...")
        
        results = {
            "broken_relationships": {},
            "invalid_types": {},
            "duplicate_relationships": {},
            "self_loops": {},
            "summary": {}
        }
        
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Check for broken relationships (relationships pointing to non-existent nodes)
            # This shouldn't happen in Neo4j, but we can check for relationships with null endpoints
            broken_query = """
                MATCH (a)-[r]->(b)
                WHERE a.id IS NULL OR b.id IS NULL
                RETURN type(r) AS rel_type, count(*) AS count
            """
            result = session.run(broken_query)
            broken_counts = {record["rel_type"]: record["count"] for record in result}
            
            results["broken_relationships"] = {
                "counts": broken_counts,
                "total": sum(broken_counts.values())
            }
            
            # Check for invalid relationship types
            valid_types = {"PERFORMS_ON", "COLLABORATES_WITH", "SIMILAR_GENRE"}
            
            invalid_types_query = """
                MATCH ()-[r]->()
                WITH type(r) AS rel_type, count(*) AS count
                RETURN rel_type, count
            """
            result = session.run(invalid_types_query)
            found_types = {}
            invalid_types = []
            
            for record in result:
                rel_type = record["rel_type"]
                count = record["count"]
                found_types[rel_type] = count
                
                if rel_type not in valid_types:
                    invalid_types.append({
                        "type": rel_type,
                        "count": count
                    })
            
            results["invalid_types"] = {
                "found": len(invalid_types) > 0,
                "valid_types": list(valid_types),
                "found_types": found_types,
                "invalid": invalid_types
            }
            
            # Check for duplicate relationships (same relationship between same nodes)
            duplicate_rel_query = """
                MATCH (a)-[r]->(b)
                WITH a, b, type(r) AS rel_type, count(*) AS count
                WHERE count > 1
                RETURN labels(a)[0] AS from_label, a.id AS from_id,
                       labels(b)[0] AS to_label, b.id AS to_id,
                       rel_type, count
                LIMIT 100
            """
            result = session.run(duplicate_rel_query)
            duplicates = []
            for record in result:
                duplicates.append({
                    "from": f"{record['from_label']}:{record['from_id']}",
                    "to": f"{record['to_label']}:{record['to_id']}",
                    "type": record["rel_type"],
                    "count": record["count"]
                })
            
            results["duplicate_relationships"] = {
                "found": len(duplicates) > 0,
                "count": len(duplicates),
                "details": duplicates
            }
            
            # Check for self-loops (if not allowed)
            self_loop_query = """
                MATCH (a)-[r]->(a)
                RETURN type(r) AS rel_type, count(*) AS count
            """
            result = session.run(self_loop_query)
            self_loops = {record["rel_type"]: record["count"] for record in result}
            
            results["self_loops"] = {
                "counts": self_loops,
                "total": sum(self_loops.values())
            }
            
            # Validate relationship constraints
            # PERFORMS_ON should be Artist -> Album
            performs_on_violation_query = """
                MATCH (a)-[r:PERFORMS_ON]->(b)
                WHERE NOT (a:Artist AND b:Album)
                RETURN count(*) AS count
            """
            result = session.run(performs_on_violation_query)
            performs_on_violations = result.single()["count"]
            
            # COLLABORATES_WITH should be Artist <-> Artist
            collaborates_violation_query = """
                MATCH (a)-[r:COLLABORATES_WITH]->(b)
                WHERE NOT (a:Artist AND b:Artist)
                RETURN count(*) AS count
            """
            result = session.run(collaborates_violation_query)
            collaborates_violations = result.single()["count"]
            
            # SIMILAR_GENRE should be Artist <-> Artist
            similar_genre_violation_query = """
                MATCH (a)-[r:SIMILAR_GENRE]->(b)
                WHERE NOT (a:Artist AND b:Artist)
                RETURN count(*) AS count
            """
            result = session.run(similar_genre_violation_query)
            similar_genre_violations = result.single()["count"]
            
            constraint_violations = {
                "PERFORMS_ON": performs_on_violations,
                "COLLABORATES_WITH": collaborates_violations,
                "SIMILAR_GENRE": similar_genre_violations
            }
            
            results["constraint_violations"] = constraint_violations
            
            # Summary
            total_rel_query = """
                MATCH ()-[r]->()
                RETURN type(r) AS rel_type, count(*) AS count
            """
            result = session.run(total_rel_query)
            rel_counts = {record["rel_type"]: record["count"] for record in result}
            
            results["summary"] = {
                "total_relationships": sum(rel_counts.values()),
                "relationship_counts": rel_counts,
                "broken_count": sum(broken_counts.values()),
                "invalid_types_count": len(invalid_types),
                "duplicate_count": len(duplicates),
                "self_loops_count": sum(self_loops.values()),
                "constraint_violations": sum(constraint_violations.values())
            }
        
        logger.info(f"  ✓ Relationship validation completed")
        logger.info(f"    - Total relationships: {results['summary']['total_relationships']}")
        logger.info(f"    - Broken relationships: {results['summary']['broken_count']}")
        logger.info(f"    - Constraint violations: {results['summary']['constraint_violations']}")
        
        return results
    
    def check_data_completeness(self) -> Dict:
        """
        Check data completeness: missing fields, empty values, etc.
        
        Returns:
            Dictionary with completeness results
        """
        logger.info("Checking data completeness...")
        
        results = {
            "artist_completeness": {},
            "album_completeness": {},
            "relationship_completeness": {},
            "overall_completeness": {}
        }
        
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Artist completeness
            artist_total_query = "MATCH (a:Artist) RETURN count(a) AS total"
            total_artists = session.run(artist_total_query).single()["total"]
            
            artist_completeness_query = """
                MATCH (a:Artist)
                WITH a,
                     CASE WHEN a.id IS NOT NULL AND a.id <> '' THEN 1 ELSE 0 END AS has_id,
                     CASE WHEN a.name IS NOT NULL AND a.name <> '' THEN 1 ELSE 0 END AS has_name,
                     CASE WHEN a.genres IS NOT NULL AND a.genres <> '' THEN 1 ELSE 0 END AS has_genres,
                     CASE WHEN a.instruments IS NOT NULL AND a.instruments <> '' THEN 1 ELSE 0 END AS has_instruments,
                     CASE WHEN a.active_years IS NOT NULL AND a.active_years <> '' THEN 1 ELSE 0 END AS has_active_years,
                     CASE WHEN a.url IS NOT NULL AND a.url <> '' THEN 1 ELSE 0 END AS has_url
                RETURN 
                    sum(has_id) AS with_id,
                    sum(has_name) AS with_name,
                    sum(has_genres) AS with_genres,
                    sum(has_instruments) AS with_instruments,
                    sum(has_active_years) AS with_active_years,
                    sum(has_url) AS with_url
            """
            result = session.run(artist_completeness_query).single()
            
            artist_completeness = {
                "total": total_artists,
                "fields": {
                    "id": {"present": result["with_id"], "percentage": (result["with_id"] / total_artists * 100) if total_artists > 0 else 0},
                    "name": {"present": result["with_name"], "percentage": (result["with_name"] / total_artists * 100) if total_artists > 0 else 0},
                    "genres": {"present": result["with_genres"], "percentage": (result["with_genres"] / total_artists * 100) if total_artists > 0 else 0},
                    "instruments": {"present": result["with_instruments"], "percentage": (result["with_instruments"] / total_artists * 100) if total_artists > 0 else 0},
                    "active_years": {"present": result["with_active_years"], "percentage": (result["with_active_years"] / total_artists * 100) if total_artists > 0 else 0},
                    "url": {"present": result["with_url"], "percentage": (result["with_url"] / total_artists * 100) if total_artists > 0 else 0}
                }
            }
            
            # Calculate overall artist completeness
            artist_field_count = sum(1 for v in artist_completeness["fields"].values() if v["present"] > 0)
            artist_completeness["overall_percentage"] = (
                sum(v["percentage"] for v in artist_completeness["fields"].values()) / 
                len(artist_completeness["fields"])
            )
            
            results["artist_completeness"] = artist_completeness
            
            # Album completeness
            album_total_query = "MATCH (a:Album) RETURN count(a) AS total"
            total_albums = session.run(album_total_query).single()["total"]
            
            album_completeness_query = """
                MATCH (a:Album)
                WITH a,
                     CASE WHEN a.id IS NOT NULL AND a.id <> '' THEN 1 ELSE 0 END AS has_id,
                     CASE WHEN a.title IS NOT NULL AND a.title <> '' THEN 1 ELSE 0 END AS has_title
                RETURN 
                    sum(has_id) AS with_id,
                    sum(has_title) AS with_title
            """
            result = session.run(album_completeness_query).single()
            
            album_completeness = {
                "total": total_albums,
                "fields": {
                    "id": {"present": result["with_id"], "percentage": (result["with_id"] / total_albums * 100) if total_albums > 0 else 0},
                    "title": {"present": result["with_title"], "percentage": (result["with_title"] / total_albums * 100) if total_albums > 0 else 0}
                }
            }
            
            album_completeness["overall_percentage"] = (
                sum(v["percentage"] for v in album_completeness["fields"].values()) / 
                len(album_completeness["fields"])
            )
            
            results["album_completeness"] = album_completeness
            
            # Relationship completeness (check for missing properties)
            rel_completeness_query = """
                MATCH ()-[r]->()
                WITH type(r) AS rel_type,
                     CASE WHEN r.shared_albums IS NOT NULL THEN 1 ELSE 0 END AS has_shared_albums,
                     CASE WHEN r.similarity IS NOT NULL THEN 1 ELSE 0 END AS has_similarity
                RETURN rel_type,
                       count(*) AS total,
                       sum(has_shared_albums) AS with_shared_albums,
                       sum(has_similarity) AS with_similarity
            """
            result = session.run(rel_completeness_query)
            
            rel_completeness = {}
            for record in result:
                rel_type = record["rel_type"]
                total = record["total"]
                
                rel_completeness[rel_type] = {
                    "total": total,
                    "properties": {}
                }
                
                if rel_type == "COLLABORATES_WITH":
                    rel_completeness[rel_type]["properties"]["shared_albums"] = {
                        "present": record["with_shared_albums"],
                        "percentage": (record["with_shared_albums"] / total * 100) if total > 0 else 0
                    }
                elif rel_type == "SIMILAR_GENRE":
                    rel_completeness[rel_type]["properties"]["similarity"] = {
                        "present": record["with_similarity"],
                        "percentage": (record["with_similarity"] / total * 100) if total > 0 else 0
                    }
            
            results["relationship_completeness"] = rel_completeness
            
            # Overall completeness
            total_nodes = total_artists + total_albums
            total_rels = sum(v["total"] for v in rel_completeness.values())
            
            results["overall_completeness"] = {
                "node_completeness": (
                    (artist_completeness["overall_percentage"] * total_artists + 
                     album_completeness["overall_percentage"] * total_albums) / total_nodes
                    if total_nodes > 0 else 0
                ),
                "total_nodes": total_nodes,
                "total_relationships": total_rels
            }
        
        logger.info(f"  ✓ Data completeness check completed")
        logger.info(f"    - Artist completeness: {results['artist_completeness']['overall_percentage']:.1f}%")
        logger.info(f"    - Album completeness: {results['album_completeness']['overall_percentage']:.1f}%")
        
        return results
    
    def calculate_quality_metrics(self) -> Dict:
        """
        Calculate quality metrics: coverage, consistency, connectivity
        
        Returns:
            Dictionary with quality metrics
        """
        logger.info("Calculating quality metrics...")
        
        results = {
            "coverage": {},
            "connectivity": {},
            "consistency": {},
            "health_score": 0.0
        }
        
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Coverage: percentage of nodes with relationships
            coverage_query = """
                MATCH (n)
                WITH n, 
                     CASE WHEN (n)--() THEN 1 ELSE 0 END AS has_relationships
                RETURN labels(n)[0] AS label,
                       count(*) AS total,
                       sum(has_relationships) AS with_relationships
            """
            result = session.run(coverage_query)
            
            coverage = {}
            total_nodes = 0
            total_with_rels = 0
            
            for record in result:
                label = record["label"]
                total = record["total"]
                with_rels = record["with_relationships"]
                
                coverage[label] = {
                    "total": total,
                    "with_relationships": with_rels,
                    "percentage": (with_rels / total * 100) if total > 0 else 0
                }
                
                total_nodes += total
                total_with_rels += with_rels
            
            coverage["overall"] = {
                "total": total_nodes,
                "with_relationships": total_with_rels,
                "percentage": (total_with_rels / total_nodes * 100) if total_nodes > 0 else 0
            }
            
            results["coverage"] = coverage
            
            # Connectivity: average degree, isolated nodes, etc.
            connectivity_query = """
                MATCH (a:Artist)
                OPTIONAL MATCH (a)-[r]->()
                WITH a, count(r) AS degree
                RETURN 
                    count(*) AS total,
                    avg(degree) AS avg_degree,
                    min(degree) AS min_degree,
                    max(degree) AS max_degree,
                    sum(CASE WHEN degree = 0 THEN 1 ELSE 0 END) AS isolated_count
            """
            result = session.run(connectivity_query).single()
            
            artist_connectivity = {
                "total": result["total"],
                "average_degree": result["avg_degree"] or 0,
                "min_degree": result["min_degree"] or 0,
                "max_degree": result["max_degree"] or 0,
                "isolated_count": result["isolated_count"] or 0,
                "isolated_percentage": (
                    (result["isolated_count"] or 0) / result["total"] * 100 
                    if result["total"] > 0 else 0
                )
            }
            
            # Network density
            total_rels_query = "MATCH ()-[r]->() RETURN count(r) AS total"
            total_rels = session.run(total_rels_query).single()["total"]
            
            # Density = 2 * edges / (nodes * (nodes - 1)) for undirected graph
            # For directed graph: edges / (nodes * (nodes - 1))
            if total_nodes > 1:
                max_possible_edges = total_nodes * (total_nodes - 1)
                density = (total_rels / max_possible_edges * 100) if max_possible_edges > 0 else 0
            else:
                density = 0
            
            results["connectivity"] = {
                "artist_connectivity": artist_connectivity,
                "total_relationships": total_rels,
                "density_percentage": density
            }
            
            # Consistency: check data format consistency
            consistency_issues = []
            
            # Check if all IDs follow expected format
            id_format_query = """
                MATCH (a:Artist)
                WHERE a.id IS NOT NULL AND NOT a.id STARTS WITH 'artist_'
                RETURN count(*) AS count
            """
            result = session.run(id_format_query)
            inconsistent_ids = result.single()["count"]
            
            if inconsistent_ids > 0:
                consistency_issues.append({
                    "issue": "Artist IDs not following expected format",
                    "count": inconsistent_ids,
                    "severity": "medium"
                })
            
            # Check genre format consistency (should be semicolon-separated)
            genre_format_query = """
                MATCH (a:Artist)
                WHERE a.genres IS NOT NULL AND a.genres <> ''
                  AND NOT a.genres CONTAINS ';'
                RETURN count(*) AS count
            """
            result = session.run(genre_format_query)
            single_genre_count = result.single()["count"]
            
            # This is not necessarily an issue, just a note
            if single_genre_count > 0:
                consistency_issues.append({
                    "issue": "Artists with single genre (no semicolon separator)",
                    "count": single_genre_count,
                    "severity": "low"
                })
            
            results["consistency"] = {
                "issues": consistency_issues,
                "issues_count": len(consistency_issues)
            }
            
            # Calculate completeness for health score
            # Get artist completeness
            artist_comp_query = """
                MATCH (a:Artist)
                WITH a,
                     CASE WHEN a.id IS NOT NULL AND a.id <> '' THEN 1 ELSE 0 END AS has_id,
                     CASE WHEN a.name IS NOT NULL AND a.name <> '' THEN 1 ELSE 0 END AS has_name,
                     CASE WHEN a.genres IS NOT NULL AND a.genres <> '' THEN 1 ELSE 0 END AS has_genres,
                     CASE WHEN a.instruments IS NOT NULL AND a.instruments <> '' THEN 1 ELSE 0 END AS has_instruments,
                     CASE WHEN a.active_years IS NOT NULL AND a.active_years <> '' THEN 1 ELSE 0 END AS has_active_years,
                     CASE WHEN a.url IS NOT NULL AND a.url <> '' THEN 1 ELSE 0 END AS has_url
                WITH count(*) AS total,
                     sum(has_id + has_name + has_genres + has_instruments + has_active_years + has_url) AS total_fields
                RETURN total, 
                       CASE WHEN total > 0 THEN (total_fields / (total * 6.0) * 100) ELSE 0 END AS completeness
            """
            result = session.run(artist_comp_query).single()
            artist_completeness_pct = result["completeness"] if result else 0
            
            # Get album completeness
            album_comp_query = """
                MATCH (a:Album)
                WITH a,
                     CASE WHEN a.id IS NOT NULL AND a.id <> '' THEN 1 ELSE 0 END AS has_id,
                     CASE WHEN a.title IS NOT NULL AND a.title <> '' THEN 1 ELSE 0 END AS has_title
                WITH count(*) AS total,
                     sum(has_id + has_title) AS total_fields
                RETURN total,
                       CASE WHEN total > 0 THEN (total_fields / (total * 2.0) * 100) ELSE 0 END AS completeness
            """
            result = session.run(album_comp_query).single()
            album_completeness_pct = result["completeness"] if result else 0
            
            # Weighted average completeness
            artist_count = session.run("MATCH (a:Artist) RETURN count(a) AS total").single()["total"] or 0
            album_count = session.run("MATCH (a:Album) RETURN count(a) AS total").single()["total"] or 0
            total_nodes_for_comp = artist_count + album_count
            
            if total_nodes_for_comp > 0:
                overall_completeness = (
                    (artist_completeness_pct * artist_count + album_completeness_pct * album_count) / 
                    total_nodes_for_comp
                )
            else:
                overall_completeness = 0
            
            # Health score: overall quality metric (0-100)
            health_factors = []
            
            # Coverage factor (0-40 points)
            coverage_score = coverage["overall"]["percentage"] * 0.4
            health_factors.append(("coverage", coverage_score))
            
            # Completeness factor (0-30 points)
            completeness_score = overall_completeness * 0.3
            health_factors.append(("completeness", completeness_score))
            
            # Consistency factor (0-20 points)
            consistency_score = max(0, 20 - len(consistency_issues) * 5) * 0.2
            health_factors.append(("consistency", consistency_score))
            
            # Connectivity factor (0-10 points)
            # Higher connectivity is better, but not too high (avoid over-connected graphs)
            connectivity_score = min(10, artist_connectivity["average_degree"] * 2) * 0.1
            health_factors.append(("connectivity", connectivity_score))
            
            health_score = sum(score for _, score in health_factors)
            results["health_score"] = round(health_score, 2)
            results["health_factors"] = {name: round(score, 2) for name, score in health_factors}
            results["completeness_for_health"] = round(overall_completeness, 2)
        
        logger.info(f"  ✓ Quality metrics calculated")
        logger.info(f"    - Coverage: {results['coverage']['overall']['percentage']:.1f}%")
        logger.info(f"    - Average degree: {results['connectivity']['artist_connectivity']['average_degree']:.2f}")
        logger.info(f"    - Health score: {results['health_score']:.1f}/100")
        
        return results
    
    def print_report(self, results: Dict):
        """
        Print a formatted validation report
        
        Args:
            results: Validation results dictionary
        """
        print("\n" + "="*80)
        print("VALIDATION REPORT")
        print("="*80)
        print(f"Timestamp: {results['timestamp']}\n")
        
        # Node validation
        print("📊 NODE VALIDATION")
        print("-"*80)
        node_summary = results['node_validation']['summary']
        print(f"Total nodes: {node_summary['total_nodes']}")
        print(f"  - Artists: {node_summary['node_counts'].get('Artist', 0)}")
        print(f"  - Albums: {node_summary['node_counts'].get('Album', 0)}")
        print(f"Orphaned nodes: {node_summary['orphaned_count']}")
        print(f"Duplicates found: {'Yes' if node_summary['duplicates_found'] else 'No'}")
        print(f"Missing fields: {node_summary['missing_fields_count']}")
        print()
        
        # Relationship validation
        print("🔗 RELATIONSHIP VALIDATION")
        print("-"*80)
        rel_summary = results['relationship_validation']['summary']
        print(f"Total relationships: {rel_summary['total_relationships']}")
        for rel_type, count in rel_summary['relationship_counts'].items():
            print(f"  - {rel_type}: {count}")
        print(f"Broken relationships: {rel_summary['broken_count']}")
        print(f"Constraint violations: {rel_summary['constraint_violations']}")
        print(f"Self-loops: {rel_summary['self_loops_count']}")
        print()
        
        # Data completeness
        print("✅ DATA COMPLETENESS")
        print("-"*80)
        artist_comp = results['data_completeness']['artist_completeness']
        print(f"Artist completeness: {artist_comp['overall_percentage']:.1f}%")
        for field, data in artist_comp['fields'].items():
            print(f"  - {field}: {data['percentage']:.1f}% ({data['present']}/{artist_comp['total']})")
        
        album_comp = results['data_completeness']['album_completeness']
        print(f"\nAlbum completeness: {album_comp['overall_percentage']:.1f}%")
        for field, data in album_comp['fields'].items():
            print(f"  - {field}: {data['percentage']:.1f}% ({data['present']}/{album_comp['total']})")
        print()
        
        # Quality metrics
        print("📈 QUALITY METRICS")
        print("-"*80)
        coverage = results['quality_metrics']['coverage']['overall']
        print(f"Coverage: {coverage['percentage']:.1f}% ({coverage['with_relationships']}/{coverage['total']} nodes have relationships)")
        
        connectivity = results['quality_metrics']['connectivity']
        print(f"Average degree: {connectivity['artist_connectivity']['average_degree']:.2f}")
        print(f"Isolated artists: {connectivity['artist_connectivity']['isolated_count']} ({connectivity['artist_connectivity']['isolated_percentage']:.1f}%)")
        print(f"Network density: {connectivity['density_percentage']:.4f}%")
        
        health = results['quality_metrics']['health_score']
        health_bar = "█" * int(health / 2) + "░" * (50 - int(health / 2))
        print(f"\nHealth Score: {health}/100")
        print(f"[{health_bar}]")
        
        if 'health_factors' in results['quality_metrics']:
            print("\nHealth factors:")
            for factor, score in results['quality_metrics']['health_factors'].items():
                print(f"  - {factor}: {score:.1f}")
        
        print("\n" + "="*80)
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Validation framework connection closed")


def main():
    """CLI interface for validation framework"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neo4j Validation Framework")
    parser.add_argument("--check", choices=["all", "nodes", "relationships", "completeness", "metrics"],
                       default="all", help="Type of validation to run")
    parser.add_argument("--output", "-o", help="Output directory for reports")
    
    args = parser.parse_args()
    
    output_dir = args.output or "data/validation"
    validator = ValidationFramework(output_dir=output_dir)
    
    try:
        if args.check == "all":
            results = validator.validate_all()
            validator.print_report(results)
        elif args.check == "nodes":
            results = validator.validate_nodes()
            print(json.dumps(results, indent=2))
        elif args.check == "relationships":
            results = validator.validate_relationships()
            print(json.dumps(results, indent=2))
        elif args.check == "completeness":
            results = validator.check_data_completeness()
            print(json.dumps(results, indent=2))
        elif args.check == "metrics":
            results = validator.calculate_quality_metrics()
            print(json.dumps(results, indent=2))
    
    finally:
        validator.close()


if __name__ == "__main__":
    main()


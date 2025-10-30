#!/usr/bin/env python3
"""
Migration Framework for Neo4j Database

This module provides a comprehensive migration framework with:
- Backup capability before migration
- Progress tracking
- Rollback functionality
- Detailed logging
- Error handling

Usage:
    from scripts.migration_framework import MigrationFramework
    
    framework = MigrationFramework()
    migration_id = framework.create_backup("backup_description")
    
    try:
        # Perform migration operations
        framework.execute_migration(migration_id, migration_function)
    except Exception as e:
        framework.rollback(migration_id)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Callable, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
from src.data_collection.utils import logger


class MigrationFramework:
    """Migration framework with backup, rollback, and progress tracking"""
    
    def __init__(self, config_path: str = "config/neo4j_config.json", 
                 backup_dir: str = "data/migrations/backups",
                 log_dir: str = "data/migrations/logs"):
        """
        Initialize migration framework
        
        Args:
            config_path: Path to Neo4j configuration file
            backup_dir: Directory to store backups
            log_dir: Directory to store migration logs
        """
        self.config_path = config_path
        self.backup_dir = Path(backup_dir)
        self.log_dir = Path(log_dir)
        self.migrations_dir = Path("data/migrations")
        
        # Create directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        # Migration state tracking
        self.state_file = self.migrations_dir / "migration_state.json"
        self.current_migration = None
        
        logger.info(f"Migration framework initialized")
        logger.info(f"  - Backup directory: {self.backup_dir}")
        logger.info(f"  - Log directory: {self.log_dir}")
    
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
    
    def _get_migration_state(self) -> Dict:
        """Load migration state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading migration state: {e}")
                return {"migrations": []}
        return {"migrations": []}
    
    def _save_migration_state(self, state: Dict):
        """Save migration state to file"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving migration state: {e}")
            raise
    
    def _create_backup_metadata(self, migration_id: str, description: str) -> Dict:
        """Create metadata for backup"""
        return {
            "migration_id": migration_id,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "backup_path": None,
            "rollback_path": None,
            "progress": {
                "current_step": 0,
                "total_steps": 0,
                "steps_completed": [],
                "steps_failed": []
            },
            "error": None,
            "neo4j_config": self.config.copy()
        }
    
    def create_backup(self, description: str = "Manual backup") -> str:
        """
        Create a backup of the Neo4j database
        
        Args:
            description: Description of the backup/migration
            
        Returns:
            migration_id: Unique identifier for this migration
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_id = f"migration_{timestamp}"
        
        logger.info(f"Creating backup: {migration_id}")
        logger.info(f"  Description: {description}")
        
        # Create backup directory for this migration
        backup_path = self.backup_dir / migration_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create metadata
        metadata = self._create_backup_metadata(migration_id, description)
        metadata["backup_path"] = str(backup_path)
        
        try:
            # Export nodes and relationships
            self._export_nodes(backup_path)
            self._export_relationships(backup_path)
            self._export_statistics(backup_path)
            
            # Save metadata
            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Update migration state
            state = self._get_migration_state()
            state["migrations"].append(metadata)
            state["last_backup"] = migration_id
            self._save_migration_state(state)
            
            metadata["status"] = "backed_up"
            self.current_migration = migration_id
            
            logger.info(f"✓ Backup created successfully: {migration_id}")
            logger.info(f"  Backup location: {backup_path}")
            
            return migration_id
            
        except Exception as e:
            logger.error(f"✗ Error creating backup: {e}")
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            
            # Save failed metadata
            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            raise
    
    def _export_nodes(self, backup_path: Path):
        """Export all nodes to CSV files"""
        logger.info("  Exporting nodes...")
        
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Export Artist nodes
            artist_query = """
                MATCH (a:Artist)
                RETURN a.id as id, a.name as name, 
                       a.genres as genres, a.instruments as instruments,
                       a.active_years as active_years, a.url as url
            """
            result = session.run(artist_query)
            artists = [dict(record) for record in result]
            
            if artists:
                artists_file = backup_path / "artists_backup.csv"
                df = pd.DataFrame(artists)
                df.to_csv(artists_file, index=False, encoding='utf-8')
                logger.info(f"    ✓ Exported {len(artists)} Artist nodes")
            
            # Export Album nodes
            album_query = """
                MATCH (a:Album)
                RETURN a.id as id, a.title as title
            """
            result = session.run(album_query)
            albums = [dict(record) for record in result]
            
            if albums:
                albums_file = backup_path / "albums_backup.csv"
                df = pd.DataFrame(albums)
                df.to_csv(albums_file, index=False, encoding='utf-8')
                logger.info(f"    ✓ Exported {len(albums)} Album nodes")
    
    def _export_relationships(self, backup_path: Path):
        """Export all relationships to CSV files"""
        logger.info("  Exporting relationships...")
        
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Export all relationships
            rel_query = """
                MATCH (a)-[r]->(b)
                RETURN labels(a)[0] as from_label, a.id as from_id,
                       type(r) as rel_type,
                       labels(b)[0] as to_label, b.id as to_id,
                       properties(r) as properties
            """
            result = session.run(rel_query)
            relationships = []
            
            for record in result:
                rel_data = {
                    "from_label": record["from_label"],
                    "from_id": record["from_id"],
                    "rel_type": record["rel_type"],
                    "to_label": record["to_label"],
                    "to_id": record["to_id"],
                    "properties": dict(record["properties"])
                }
                relationships.append(rel_data)
            
            if relationships:
                rels_file = backup_path / "relationships_backup.json"
                with open(rels_file, 'w', encoding='utf-8') as f:
                    json.dump(relationships, f, indent=2, ensure_ascii=False)
                logger.info(f"    ✓ Exported {len(relationships)} relationships")
    
    def _export_statistics(self, backup_path: Path):
        """Export database statistics"""
        logger.info("  Exporting statistics...")
        
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Node counts by label
            node_query = """
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
            """
            result = session.run(node_query)
            node_stats = {record["label"]: record["count"] for record in result}
            
            # Relationship counts by type
            rel_query = """
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
            """
            result = session.run(rel_query)
            rel_stats = {record["type"]: record["count"] for record in result}
            
            stats = {
                "nodes": node_stats,
                "relationships": rel_stats,
                "timestamp": datetime.now().isoformat()
            }
            
            stats_file = backup_path / "statistics.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            logger.info(f"    ✓ Exported statistics")
            logger.info(f"      Nodes: {sum(node_stats.values())}")
            logger.info(f"      Relationships: {sum(rel_stats.values())}")
    
    def execute_migration(self, migration_id: str, migration_func: Callable, 
                         steps: Optional[List[str]] = None):
        """
        Execute a migration with progress tracking
        
        Args:
            migration_id: ID of the migration to execute
            migration_func: Function to execute for migration
            steps: Optional list of step names for progress tracking
        """
        logger.info(f"Executing migration: {migration_id}")
        
        # Load migration state
        state = self._get_migration_state()
        migration = None
        
        for mig in state["migrations"]:
            if mig["migration_id"] == migration_id:
                migration = mig
                break
        
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")
        
        migration["status"] = "running"
        migration["progress"]["total_steps"] = len(steps) if steps else 1
        
        # Create log file
        log_file = self.log_dir / f"{migration_id}.log"
        migration["log_file"] = str(log_file)
        
        # Update state
        self._save_migration_state(state)
        self.current_migration = migration_id
        
        try:
            with open(log_file, 'w', encoding='utf-8') as log:
                log.write(f"Migration Execution Log: {migration_id}\n")
                log.write(f"Description: {migration['description']}\n")
                log.write(f"Started: {datetime.now().isoformat()}\n\n")
                
                # Execute migration function
                if steps:
                    for i, step in enumerate(steps, 1):
                        logger.info(f"  Step {i}/{len(steps)}: {step}")
                        log.write(f"Step {i}/{len(steps)}: {step}\n")
                        log.write(f"  Started: {datetime.now().isoformat()}\n")
                        
                        migration["progress"]["current_step"] = i
                        self._save_migration_state(state)
                        
                        # Execute step (assume migration_func handles step execution)
                        migration_func(self, step)
                        
                        migration["progress"]["steps_completed"].append(step)
                        log.write(f"  Completed: {datetime.now().isoformat()}\n\n")
                else:
                    migration_func(self)
                
                log.write(f"\nMigration completed: {datetime.now().isoformat()}\n")
            
            migration["status"] = "completed"
            migration["progress"]["current_step"] = migration["progress"]["total_steps"]
            
            logger.info(f"✓ Migration completed successfully: {migration_id}")
            
        except Exception as e:
            migration["status"] = "failed"
            migration["error"] = str(e)
            if steps and migration["progress"]["current_step"] > 0:
                failed_step = steps[migration["progress"]["current_step"] - 1]
                migration["progress"]["steps_failed"].append(failed_step)
            
            logger.error(f"✗ Migration failed: {e}")
            raise
        
        finally:
            self._save_migration_state(state)
    
    def rollback(self, migration_id: str) -> bool:
        """
        Rollback a migration by restoring from backup
        
        Args:
            migration_id: ID of the migration to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        logger.info(f"Rolling back migration: {migration_id}")
        
        # Load migration state
        state = self._get_migration_state()
        migration = None
        
        for mig in state["migrations"]:
            if mig["migration_id"] == migration_id:
                migration = mig
                break
        
        if not migration:
            logger.error(f"Migration {migration_id} not found")
            return False
        
        backup_path = Path(migration["backup_path"])
        
        if not backup_path.exists():
            logger.error(f"Backup path does not exist: {backup_path}")
            return False
        
        # Create rollback log
        rollback_log = self.log_dir / f"{migration_id}_rollback.log"
        
        try:
            with open(rollback_log, 'w', encoding='utf-8') as log:
                log.write(f"Rollback Log: {migration_id}\n")
                log.write(f"Started: {datetime.now().isoformat()}\n\n")
                
                # Clear current database
                logger.info("  Clearing current database...")
                log.write("Step 1: Clearing current database\n")
                with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                    session.run("MATCH (n) DETACH DELETE n")
                log.write("  ✓ Database cleared\n\n")
                
                # Restore nodes
                logger.info("  Restoring nodes...")
                log.write("Step 2: Restoring nodes\n")
                self._restore_nodes(backup_path, log)
                
                # Restore relationships
                logger.info("  Restoring relationships...")
                log.write("Step 3: Restoring relationships\n")
                self._restore_relationships(backup_path, log)
                
                log.write(f"\nRollback completed: {datetime.now().isoformat()}\n")
            
            migration["status"] = "rolled_back"
            migration["rollback_path"] = str(rollback_log)
            self._save_migration_state(state)
            
            logger.info(f"✓ Rollback completed successfully: {migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Rollback failed: {e}")
            migration["status"] = "rollback_failed"
            migration["error"] = str(e)
            self._save_migration_state(state)
            return False
    
    def _restore_nodes(self, backup_path: Path, log_file):
        """Restore nodes from backup"""
        # Restore Artists
        artists_file = backup_path / "artists_backup.csv"
        if artists_file.exists():
            df = pd.read_csv(artists_file, encoding='utf-8')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                batch_size = 500
                for i in range(0, len(df), batch_size):
                    batch_df = df.iloc[i:i+batch_size]
                    # Convert to dict and handle NaN values
                    batch = []
                    for _, row in batch_df.iterrows():
                        artist_dict = {
                            'id': row.get('id', ''),
                            'name': row.get('name', ''),
                            'genres': row.get('genres') if pd.notna(row.get('genres')) else '',
                            'instruments': row.get('instruments') if pd.notna(row.get('instruments')) else '',
                            'active_years': row.get('active_years') if pd.notna(row.get('active_years')) else '',
                            'url': row.get('url') if pd.notna(row.get('url')) else ''
                        }
                        batch.append(artist_dict)
                    
                    session.run("""
                        UNWIND $artists AS artist
                        CREATE (a:Artist {
                            id: artist.id,
                            name: artist.name,
                            genres: artist.genres,
                            instruments: artist.instruments,
                            active_years: artist.active_years,
                            url: artist.url
                        })
                    """, artists=batch)
                
                log_file.write(f"  ✓ Restored {len(df)} Artist nodes\n")
                logger.info(f"    ✓ Restored {len(df)} Artist nodes")
        
        # Restore Albums
        albums_file = backup_path / "albums_backup.csv"
        if albums_file.exists():
            df = pd.read_csv(albums_file, encoding='utf-8')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                batch_size = 500
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size].to_dict('records')
                    
                    session.run("""
                        UNWIND $albums AS album
                        CREATE (a:Album {
                            id: album.id,
                            title: album.title
                        })
                    """, albums=batch)
                
                log_file.write(f"  ✓ Restored {len(df)} Album nodes\n")
                logger.info(f"    ✓ Restored {len(df)} Album nodes")
    
    def _restore_relationships(self, backup_path: Path, log_file):
        """Restore relationships from backup"""
        rels_file = backup_path / "relationships_backup.json"
        
        if not rels_file.exists():
            log_file.write("  ⚠ No relationships file found\n")
            return
        
        with open(rels_file, 'r', encoding='utf-8') as f:
            relationships = json.load(f)
        
        # Group by relationship type
        by_type = {}
        for rel in relationships:
            rel_type = rel["rel_type"]
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel)
        
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            for rel_type, rels in by_type.items():
                batch_size = 1000
                for i in range(0, len(rels), batch_size):
                    batch = rels[i:i+batch_size]
                    
                    for rel in batch:
                        from_label = rel["from_label"]
                        to_label = rel["to_label"]
                        properties = rel.get("properties", {})
                        
                        # Build properties string
                        props_str = ""
                        if properties:
                            props_list = [f"{k}: ${k}" for k in properties.keys()]
                            props_str = " {" + ", ".join(props_list) + "}"
                        
                        query = f"""
                            MATCH (from:{from_label} {{id: $from_id}})
                            MATCH (to:{to_label} {{id: $to_id}})
                            CREATE (from)-[:{rel_type}{props_str}]->(to)
                        """
                        
                        params = {
                            "from_id": rel["from_id"],
                            "to_id": rel["to_id"],
                            **properties
                        }
                        
                        session.run(query, params)
                
                log_file.write(f"  ✓ Restored {len(rels)} {rel_type} relationships\n")
                logger.info(f"    ✓ Restored {len(rels)} {rel_type} relationships")
    
    def list_migrations(self) -> List[Dict]:
        """List all migrations"""
        state = self._get_migration_state()
        return state.get("migrations", [])
    
    def get_migration_status(self, migration_id: str) -> Optional[Dict]:
        """Get status of a specific migration"""
        migrations = self.list_migrations()
        for mig in migrations:
            if mig["migration_id"] == migration_id:
                return mig
        return None
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Migration framework connection closed")


def main():
    """CLI interface for migration framework"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neo4j Migration Framework")
    parser.add_argument("action", choices=["backup", "rollback", "list", "status"],
                       help="Action to perform")
    parser.add_argument("--migration-id", "-m", help="Migration ID")
    parser.add_argument("--description", "-d", help="Backup description")
    
    args = parser.parse_args()
    
    framework = MigrationFramework()
    
    try:
        if args.action == "backup":
            description = args.description or "Manual backup"
            migration_id = framework.create_backup(description)
            print(f"✓ Backup created: {migration_id}")
            
        elif args.action == "rollback":
            if not args.migration_id:
                print("Error: --migration-id required for rollback")
                return
            success = framework.rollback(args.migration_id)
            if success:
                print(f"✓ Rollback completed: {args.migration_id}")
            else:
                print(f"✗ Rollback failed: {args.migration_id}")
                
        elif args.action == "list":
            migrations = framework.list_migrations()
            print(f"\nFound {len(migrations)} migrations:\n")
            for mig in migrations:
                print(f"  {mig['migration_id']}")
                print(f"    Status: {mig['status']}")
                print(f"    Description: {mig['description']}")
                print(f"    Timestamp: {mig['timestamp']}")
                print()
                
        elif args.action == "status":
            if not args.migration_id:
                print("Error: --migration-id required for status")
                return
            status = framework.get_migration_status(args.migration_id)
            if status:
                print(json.dumps(status, indent=2))
            else:
                print(f"Migration {args.migration_id} not found")
    
    finally:
        framework.close()


if __name__ == "__main__":
    main()


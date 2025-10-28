"""Neo4j importer module"""

import json
import os
from typing import Dict
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
from data_collection.utils import logger


class Neo4jImporter:
    """Import graph data into Neo4j database"""
    
    def __init__(self, config_path: str = "config/neo4j_config.json"):
        """Initialize Neo4j connection"""
        self.config = self._load_config(config_path)
        
        # Load password from environment
        load_dotenv()
        password = os.getenv('NEO4J_PASS', 'password')
        
        # Create driver
        self.driver = GraphDatabase.driver(
            self.config['uri'],
            auth=(self.config['user'], password)
        )
        
        logger.info(f"Connected to Neo4j at {self.config['uri']}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load Neo4j configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading Neo4j config: {e}")
            return {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "database": "neo4j"
            }
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")
    
    def clear_database(self):
        """Clear all nodes and relationships"""
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared Neo4j database")
    
    def create_constraints(self):
        """Create constraints and indexes"""
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Create constraints for Artist
            try:
                session.run("""
                    CREATE CONSTRAINT artist_id IF NOT EXISTS
                    FOR (a:Artist) REQUIRE a.id IS UNIQUE
                """)
                logger.info("Created constraint for Artist.id")
            except Exception as e:
                logger.warning(f"Could not create Artist constraint: {e}")
            
            # Create constraints for Album
            try:
                session.run("""
                    CREATE CONSTRAINT album_id IF NOT EXISTS
                    FOR (a:Album) REQUIRE a.id IS UNIQUE
                """)
                logger.info("Created constraint for Album.id")
            except Exception as e:
                logger.warning(f"Could not create Album constraint: {e}")
    
    def import_artists(self, csv_path: str):
        """Import artist nodes from CSV"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            artists = df.to_dict('records')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Batch import
                batch_size = 500
                for i in range(0, len(artists), batch_size):
                    batch = artists[i:i + batch_size]
                    
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
                    
                    logger.info(f"Imported artists batch {i//batch_size + 1}: {len(batch)} nodes")
            
            logger.info(f"Successfully imported {len(artists)} artists")
            
        except Exception as e:
            logger.error(f"Error importing artists: {e}")
            raise
    
    def import_albums(self, csv_path: str):
        """Import album nodes from CSV"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            albums = df.to_dict('records')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Batch import
                batch_size = 500
                for i in range(0, len(albums), batch_size):
                    batch = albums[i:i + batch_size]
                    
                    session.run("""
                        UNWIND $albums AS album
                        CREATE (a:Album {
                            id: album.id,
                            title: album.title
                        })
                    """, albums=batch)
                    
                    logger.info(f"Imported albums batch {i//batch_size + 1}: {len(batch)} nodes")
            
            logger.info(f"Successfully imported {len(albums)} albums")
            
        except Exception as e:
            logger.error(f"Error importing albums: {e}")
            raise
    
    def import_relationships(self, csv_path: str):
        """Import relationships from CSV with dynamic relationship types"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            edges = df.to_dict('records')
            
            # Separate edges by type for better import
            performs_on_edges = [e for e in edges if e.get('type') == 'PERFORMS_ON']
            collaborates_edges = [e for e in edges if e.get('type') == 'COLLABORATES_WITH']
            similar_genre_edges = [e for e in edges if e.get('type') == 'SIMILAR_GENRE']
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Import PERFORMS_ON relationships (Artist -> Album)
                if performs_on_edges:
                    batch_size = 1000
                    for i in range(0, len(performs_on_edges), batch_size):
                        batch = performs_on_edges[i:i + batch_size]
                        
                        session.run("""
                            UNWIND $edges AS edge
                            MATCH (from {id: edge.from})
                            MATCH (to {id: edge.to})
                            CREATE (from)-[:PERFORMS_ON]->(to)
                        """, edges=batch)
                        
                        logger.info(f"Imported PERFORMS_ON batch {i//batch_size + 1}: {len(batch)} edges")
                    
                    logger.info(f"✓ Imported {len(performs_on_edges)} PERFORMS_ON relationships")
                
                # Import COLLABORATES_WITH relationships (Artist <-> Artist)
                if collaborates_edges:
                    batch_size = 1000
                    for i in range(0, len(collaborates_edges), batch_size):
                        batch = collaborates_edges[i:i + batch_size]
                        
                        session.run("""
                            UNWIND $edges AS edge
                            MATCH (from:Artist {id: edge.from})
                            MATCH (to:Artist {id: edge.to})
                            CREATE (from)-[:COLLABORATES_WITH {shared_albums: edge.weight}]->(to)
                        """, edges=batch)
                        
                        logger.info(f"Imported COLLABORATES_WITH batch {i//batch_size + 1}: {len(batch)} edges")
                    
                    logger.info(f"✓ Imported {len(collaborates_edges)} COLLABORATES_WITH relationships")
                
                # Import SIMILAR_GENRE relationships (Artist <-> Artist)
                if similar_genre_edges:
                    batch_size = 1000
                    for i in range(0, len(similar_genre_edges), batch_size):
                        batch = similar_genre_edges[i:i + batch_size]
                        
                        session.run("""
                            UNWIND $edges AS edge
                            MATCH (from:Artist {id: edge.from})
                            MATCH (to:Artist {id: edge.to})
                            CREATE (from)-[:SIMILAR_GENRE {similarity: edge.weight}]->(to)
                        """, edges=batch)
                        
                        logger.info(f"Imported SIMILAR_GENRE batch {i//batch_size + 1}: {len(batch)} edges")
                    
                    logger.info(f"✓ Imported {len(similar_genre_edges)} SIMILAR_GENRE relationships")
            
            logger.info(f"✓ Successfully imported {len(edges)} total relationships")
            
        except Exception as e:
            logger.error(f"Error importing relationships: {e}")
            raise
    
    def verify_import(self):
        """Verify the import by counting nodes and relationships"""
        with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
            # Count nodes
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
            """)
            
            logger.info("Node counts:")
            for record in result:
                logger.info(f"  - {record['label']}: {record['count']}")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(r) AS count
            """)
            
            logger.info("Relationship counts:")
            for record in result:
                logger.info(f"  - {record['type']}: {record['count']}")


def import_to_neo4j(data_dir: str = "data/processed",
                    config_path: str = "config/neo4j_config.json",
                    clear_first: bool = True):
    """Main function to import data to Neo4j"""
    importer = Neo4jImporter(config_path)
    
    try:
        # Clear database if requested
        if clear_first:
            importer.clear_database()
        
        # Create constraints
        importer.create_constraints()
        
        # Import nodes
        artists_path = os.path.join(data_dir, "artists.csv")
        albums_path = os.path.join(data_dir, "albums.csv")
        edges_path = os.path.join(data_dir, "edges.csv")
        
        if os.path.exists(artists_path):
            importer.import_artists(artists_path)
        else:
            logger.warning(f"Artists file not found: {artists_path}")
        
        if os.path.exists(albums_path):
            importer.import_albums(albums_path)
        else:
            logger.warning(f"Albums file not found: {albums_path}")
        
        # Import relationships
        if os.path.exists(edges_path):
            importer.import_relationships(edges_path)
        else:
            logger.warning(f"Edges file not found: {edges_path}")
        
        # Verify
        importer.verify_import()
        
        logger.info("Neo4j import completed successfully")
        
    except Exception as e:
        logger.error(f"Error during Neo4j import: {e}")
        raise
    finally:
        importer.close()


if __name__ == "__main__":
    import_to_neo4j()


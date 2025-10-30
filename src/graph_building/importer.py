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
            
            # Create constraints for Genre
            try:
                session.run("""
                    CREATE CONSTRAINT genre_id IF NOT EXISTS
                    FOR (g:Genre) REQUIRE g.id IS UNIQUE
                """)
                logger.info("Created constraint for Genre.id")
            except Exception as e:
                logger.warning(f"Could not create Genre constraint: {e}")
            
            # Create constraints for Band
            try:
                session.run("""
                    CREATE CONSTRAINT band_id IF NOT EXISTS
                    FOR (b:Band) REQUIRE b.id IS UNIQUE
                """)
                logger.info("Created constraint for Band.id")
            except Exception as e:
                logger.warning(f"Could not create Band constraint: {e}")
            
            # Create constraints for RecordLabel
            try:
                session.run("""
                    CREATE CONSTRAINT recordlabel_id IF NOT EXISTS
                    FOR (r:RecordLabel) REQUIRE r.id IS UNIQUE
                """)
                logger.info("Created constraint for RecordLabel.id")
            except Exception as e:
                logger.warning(f"Could not create RecordLabel constraint: {e}")
            
            # Create constraints for Song
            try:
                session.run("""
                    CREATE CONSTRAINT song_id IF NOT EXISTS
                    FOR (s:Song) REQUIRE s.id IS UNIQUE
                """)
                logger.info("Created constraint for Song.id")
            except Exception as e:
                logger.warning(f"Could not create Song constraint: {e}")
            
            # Create constraints for Award
            try:
                session.run("""
                    CREATE CONSTRAINT award_id IF NOT EXISTS
                    FOR (a:Award) REQUIRE a.id IS UNIQUE
                """)
                logger.info("Created constraint for Award.id")
            except Exception as e:
                logger.warning(f"Could not create Award constraint: {e}")
    
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
    
    def import_genres(self, csv_path: str):
        """Import genre nodes from CSV"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            genres = df.to_dict('records')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Batch import
                batch_size = 500
                for i in range(0, len(genres), batch_size):
                    batch = genres[i:i + batch_size]
                    
                    session.run("""
                        UNWIND $genres AS genre
                        CREATE (g:Genre {
                            id: genre.id,
                            name: genre.name,
                            normalized_name: genre.normalized_name,
                            count: COALESCE(toInteger(genre.count), 0)
                        })
                    """, genres=batch)
                    
                    logger.info(f"Imported genres batch {i//batch_size + 1}: {len(batch)} nodes")
            
            logger.info(f"Successfully imported {len(genres)} genres")
            
        except Exception as e:
            logger.error(f"Error importing genres: {e}")
            raise
    
    def import_bands(self, csv_path: str):
        """Import band nodes from CSV"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            bands = df.to_dict('records')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Batch import
                batch_size = 500
                for i in range(0, len(bands), batch_size):
                    batch = bands[i:i + batch_size]
                    
                    session.run("""
                        UNWIND $bands AS band
                        CREATE (b:Band {
                            id: band.id,
                            name: band.name,
                            url: band.url,
                            classification_confidence: COALESCE(toFloat(band.classification_confidence), 0.0)
                        })
                    """, bands=batch)
                    
                    logger.info(f"Imported bands batch {i//batch_size + 1}: {len(batch)} nodes")
            
            logger.info(f"Successfully imported {len(bands)} bands")
            
        except Exception as e:
            logger.error(f"Error importing bands: {e}")
            raise
    
    def import_record_labels(self, csv_path: str):
        """Import record label nodes from CSV"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            labels = df.to_dict('records')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Batch import
                batch_size = 500
                for i in range(0, len(labels), batch_size):
                    batch = labels[i:i + batch_size]
                    
                    session.run("""
                        UNWIND $labels AS label
                        CREATE (r:RecordLabel {
                            id: label.id,
                            name: label.name
                        })
                    """, labels=batch)
                    
                    logger.info(f"Imported record labels batch {i//batch_size + 1}: {len(batch)} nodes")
            
            logger.info(f"Successfully imported {len(labels)} record labels")
            
        except Exception as e:
            logger.error(f"Error importing record labels: {e}")
            raise
    
    def import_songs(self, csv_path: str):
        """Import song nodes from CSV"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            songs = df.to_dict('records')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Batch import
                batch_size = 500
                for i in range(0, len(songs), batch_size):
                    batch = songs[i:i + batch_size]
                    
                    session.run("""
                        UNWIND $songs AS song
                        CREATE (s:Song {
                            id: song.id,
                            title: song.title,
                            duration: COALESCE(song.duration, ''),
                            track_number: COALESCE(song.track_number, ''),
                            album_id: COALESCE(song.album_id, ''),
                            featured_artists: COALESCE(song.featured_artists, '')
                        })
                    """, songs=batch)
                    
                    logger.info(f"Imported songs batch {i//batch_size + 1}: {len(batch)} nodes")
            
            logger.info(f"Successfully imported {len(songs)} songs")
            
        except Exception as e:
            logger.error(f"Error importing songs: {e}")
            raise
    
    def import_awards(self, csv_path: str):
        """Import award nodes from CSV"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            awards = df.to_dict('records')
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Batch import
                batch_size = 500
                for i in range(0, len(awards), batch_size):
                    batch = awards[i:i + batch_size]
                    
                    session.run("""
                        UNWIND $awards AS award
                        CREATE (a:Award {
                            id: award.id,
                            name: COALESCE(award.name, ''),
                            ceremony: COALESCE(award.ceremony, ''),
                            category: COALESCE(award.category, ''),
                            year: COALESCE(award.year, '')
                        })
                    """, awards=batch)
                    
                    logger.info(f"Imported awards batch {i//batch_size + 1}: {len(batch)} nodes")
            
            logger.info(f"Successfully imported {len(awards)} awards")
            
        except Exception as e:
            logger.error(f"Error importing awards: {e}")
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
            has_genre_edges = [e for e in edges if e.get('type') == 'HAS_GENRE']
            member_of_edges = [e for e in edges if e.get('type') == 'MEMBER_OF']
            signed_with_edges = [e for e in edges if e.get('type') == 'SIGNED_WITH']
            part_of_edges = [e for e in edges if e.get('type') == 'PART_OF']
            award_nomination_edges = [e for e in edges if e.get('type') == 'AWARD_NOMINATION']
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # Import PERFORMS_ON relationships (Artist -> Album or Artist -> Song)
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
                
                # Import HAS_GENRE relationships (Artist/Album -> Genre)
                if has_genre_edges:
                    batch_size = 1000
                    for i in range(0, len(has_genre_edges), batch_size):
                        batch = has_genre_edges[i:i + batch_size]
                        
                        session.run("""
                            UNWIND $edges AS edge
                            MATCH (from {id: edge.from})
                            MATCH (to:Genre {id: edge.to})
                            CREATE (from)-[:HAS_GENRE]->(to)
                        """, edges=batch)
                        
                        logger.info(f"Imported HAS_GENRE batch {i//batch_size + 1}: {len(batch)} edges")
                    
                    logger.info(f"✓ Imported {len(has_genre_edges)} HAS_GENRE relationships")
                
                # Import MEMBER_OF relationships (Artist -> Band)
                if member_of_edges:
                    batch_size = 1000
                    for i in range(0, len(member_of_edges), batch_size):
                        batch = member_of_edges[i:i + batch_size]
                        
                        session.run("""
                            UNWIND $edges AS edge
                            MATCH (from:Artist {id: edge.from})
                            MATCH (to:Band {id: edge.to})
                            CREATE (from)-[:MEMBER_OF]->(to)
                        """, edges=batch)
                        
                        logger.info(f"Imported MEMBER_OF batch {i//batch_size + 1}: {len(batch)} edges")
                    
                    logger.info(f"✓ Imported {len(member_of_edges)} MEMBER_OF relationships")
                
                # Import SIGNED_WITH relationships (Artist -> RecordLabel)
                if signed_with_edges:
                    batch_size = 1000
                    for i in range(0, len(signed_with_edges), batch_size):
                        batch = signed_with_edges[i:i + batch_size]
                        
                        session.run("""
                            UNWIND $edges AS edge
                            MATCH (from:Artist {id: edge.from})
                            MATCH (to:RecordLabel {id: edge.to})
                            CREATE (from)-[:SIGNED_WITH]->(to)
                        """, edges=batch)
                        
                        logger.info(f"Imported SIGNED_WITH batch {i//batch_size + 1}: {len(batch)} edges")
                    
                    logger.info(f"✓ Imported {len(signed_with_edges)} SIGNED_WITH relationships")
                
                # Import PART_OF relationships (Song -> Album)
                if part_of_edges:
                    batch_size = 1000
                    for i in range(0, len(part_of_edges), batch_size):
                        batch = part_of_edges[i:i + batch_size]
                        
                        # Separate edges with and without track_number for batch processing
                        edges_with_track = []
                        edges_without_track = []
                        
                        for edge in batch:
                            track_number = edge.get('track_number')
                            if track_number and str(track_number).strip() and str(track_number) != 'nan':
                                edges_with_track.append({
                                    'from': edge['from'],
                                    'to': edge['to'],
                                    'track_number': str(track_number).strip()
                                })
                            else:
                                edges_without_track.append({
                                    'from': edge['from'],
                                    'to': edge['to']
                                })
                        
                        # Import edges with track_number
                        if edges_with_track:
                            session.run("""
                                UNWIND $edges AS edge
                                MATCH (from:Song {id: edge.from})
                                MATCH (to:Album {id: edge.to})
                                CREATE (from)-[:PART_OF {track_number: edge.track_number}]->(to)
                            """, edges=edges_with_track)
                        
                        # Import edges without track_number
                        if edges_without_track:
                            session.run("""
                                UNWIND $edges AS edge
                                MATCH (from:Song {id: edge.from})
                                MATCH (to:Album {id: edge.to})
                                CREATE (from)-[:PART_OF]->(to)
                            """, edges=edges_without_track)
                        
                        logger.info(f"Imported PART_OF batch {i//batch_size + 1}: {len(batch)} edges")
                    
                    logger.info(f"✓ Imported {len(part_of_edges)} PART_OF relationships")
                
                # Import AWARD_NOMINATION relationships (Artist/Band -> Award)
                if award_nomination_edges:
                    batch_size = 1000
                    for i in range(0, len(award_nomination_edges), batch_size):
                        batch = award_nomination_edges[i:i + batch_size]
                        
                        # Separate edges by whether they have optional properties
                        edges_with_props = []
                        edges_without_props = []
                        
                        for edge in batch:
                            status = edge.get('status')
                            year = edge.get('year')
                            
                            # Check if edge has optional properties
                            has_status = status and str(status).strip() and str(status).lower() != 'nan'
                            has_year = year and str(year).strip() and str(year).lower() != 'nan'
                            
                            if has_status or has_year:
                                edge_props = {
                                    'from': edge['from'],
                                    'to': edge['to']
                                }
                                if has_status:
                                    edge_props['status'] = str(status).strip()
                                if has_year:
                                    edge_props['year'] = str(year).strip()
                                edges_with_props.append(edge_props)
                            else:
                                edges_without_props.append({
                                    'from': edge['from'],
                                    'to': edge['to']
                                })
                        
                        # Import edges with optional properties
                        if edges_with_props:
                            # Properties are already filtered - only include if they exist
                            # Neo4j will not store properties with NULL values
                            session.run("""
                                UNWIND $edges AS edge
                                MATCH (from {id: edge.from})
                                WHERE from:Artist OR from:Band
                                MATCH (to:Award {id: edge.to})
                                CREATE (from)-[:AWARD_NOMINATION {
                                    status: edge.status,
                                    year: edge.year
                                }]->(to)
                            """, edges=edges_with_props)
                        
                        # Import edges without optional properties
                        if edges_without_props:
                            session.run("""
                                UNWIND $edges AS edge
                                MATCH (from {id: edge.from})
                                WHERE from:Artist OR from:Band
                                MATCH (to:Award {id: edge.to})
                                CREATE (from)-[:AWARD_NOMINATION]->(to)
                            """, edges=edges_without_props)
                        
                        logger.info(f"Imported AWARD_NOMINATION batch {i//batch_size + 1}: {len(batch)} edges")
                    
                    logger.info(f"✓ Imported {len(award_nomination_edges)} AWARD_NOMINATION relationships")
            
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
        genres_path = os.path.join(data_dir, "genres.csv")
        bands_path = os.path.join(data_dir, "bands.csv")
        record_labels_path = os.path.join(data_dir, "record_labels.csv")
        songs_path = os.path.join(data_dir, "songs.csv")
        awards_path = os.path.join(data_dir, "awards.csv")
        edges_path = os.path.join(data_dir, "edges.csv")
        has_genre_path = os.path.join(data_dir, "has_genre_edges.csv")
        
        if os.path.exists(artists_path):
            importer.import_artists(artists_path)
        else:
            logger.warning(f"Artists file not found: {artists_path}")
        
        if os.path.exists(albums_path):
            importer.import_albums(albums_path)
        else:
            logger.warning(f"Albums file not found: {albums_path}")
        
        if os.path.exists(genres_path):
            importer.import_genres(genres_path)
        else:
            logger.warning(f"Genres file not found: {genres_path}")
        
        if os.path.exists(bands_path):
            importer.import_bands(bands_path)
        else:
            logger.warning(f"Bands file not found: {bands_path}")
        
        if os.path.exists(record_labels_path):
            importer.import_record_labels(record_labels_path)
        else:
            logger.warning(f"Record labels file not found: {record_labels_path}")
        
        if os.path.exists(songs_path):
            importer.import_songs(songs_path)
        else:
            logger.warning(f"Songs file not found: {songs_path}")
        
        if os.path.exists(awards_path):
            importer.import_awards(awards_path)
        else:
            logger.warning(f"Awards file not found: {awards_path}")
        
        # Import relationships
        if os.path.exists(edges_path):
            importer.import_relationships(edges_path)
        else:
            logger.warning(f"Edges file not found: {edges_path}")
        
        # Import HAS_GENRE relationships if separate file exists
        if os.path.exists(has_genre_path):
            # Read HAS_GENRE edges and add to edges
            import pandas as pd
            has_genre_df = pd.read_csv(has_genre_path, encoding='utf-8')
            edges_df = pd.read_csv(edges_path, encoding='utf-8') if os.path.exists(edges_path) else pd.DataFrame()
            
            # Combine HAS_GENRE with existing edges
            combined_edges = pd.concat([edges_df, has_genre_df], ignore_index=True)
            temp_edges_path = os.path.join(data_dir, "edges_with_genres.csv")
            combined_edges.to_csv(temp_edges_path, index=False, encoding='utf-8')
            
            importer.import_relationships(temp_edges_path)
            
            # Clean up temp file
            if os.path.exists(temp_edges_path):
                os.remove(temp_edges_path)
        elif os.path.exists(edges_path):
            # Check if HAS_GENRE is already in edges.csv
            import pandas as pd
            edges_df = pd.read_csv(edges_path, encoding='utf-8')
            if 'HAS_GENRE' in edges_df['type'].values:
                logger.info("HAS_GENRE relationships found in edges.csv, importing...")
                importer.import_relationships(edges_path)
        
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


"""Graph building module using NetworkX"""

import json
import os
from typing import Dict, List, Tuple
import pandas as pd
import networkx as nx
from data_collection.utils import logger


class GraphBuilder:
    """Build graph network from processed data"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.artist_nodes = {}
        self.album_nodes = {}
    
    def load_nodes(self, nodes_path: str) -> pd.DataFrame:
        """Load artist nodes from CSV"""
        try:
            df = pd.read_csv(nodes_path, encoding='utf-8')
            logger.info(f"Loaded {len(df)} artist nodes from {nodes_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading nodes: {e}")
            return pd.DataFrame()
    
    def load_albums(self, albums_path: str) -> Dict:
        """Load album mapping from JSON"""
        try:
            with open(albums_path, 'r', encoding='utf-8') as f:
                albums = json.load(f)
            logger.info(f"Loaded {len(albums)} albums from {albums_path}")
            return albums
        except Exception as e:
            logger.error(f"Error loading albums: {e}")
            return {}
    
    def add_artist_nodes(self, df: pd.DataFrame):
        """Add artist nodes to graph"""
        for idx, row in df.iterrows():
            node_id = f"artist_{row['id']}"
            self.artist_nodes[row['id']] = node_id
            
            self.graph.add_node(
                node_id,
                node_type='Artist',
                name=row['name'],
                genres=row.get('genres', ''),
                instruments=row.get('instruments', ''),
                active_years=row.get('active_years', ''),
                url=row.get('url', '')
            )
        
        logger.info(f"Added {len(self.artist_nodes)} artist nodes to graph")
    
    def add_album_nodes_and_edges(self, album_map: Dict):
        """Add album nodes and create artist-album edges"""
        edges_added = 0
        collaboration_edges = 0
        
        for album_idx, (album_title, artist_ids) in enumerate(album_map.items()):
            # Only create album nodes if multiple artists are associated
            if len(artist_ids) < 2:
                continue
            
            album_id = f"album_{album_idx}"
            self.album_nodes[album_title] = album_id
            
            # Add album node
            self.graph.add_node(
                album_id,
                node_type='Album',
                title=album_title
            )
            
            # Add edges from artists to album
            valid_artist_nodes = []
            for artist_id in artist_ids:
                artist_node_id = self.artist_nodes.get(artist_id)
                if artist_node_id:
                    self.graph.add_edge(
                        artist_node_id,
                        album_id,
                        relationship='PERFORMS_ON'
                    )
                    edges_added += 1
                    valid_artist_nodes.append(artist_node_id)
            
            # Create collaboration edges between artists on the same album
            for i, artist1 in enumerate(valid_artist_nodes):
                for artist2 in valid_artist_nodes[i+1:]:
                    # Check if collaboration edge already exists
                    if not self.graph.has_edge(artist1, artist2):
                        self.graph.add_edge(
                            artist1,
                            artist2,
                            relationship='COLLABORATES_WITH',
                            shared_albums=1
                        )
                        collaboration_edges += 1
                    else:
                        # Increment shared albums count
                        edge_data = self.graph[artist1][artist2]
                        if edge_data.get('relationship') == 'COLLABORATES_WITH':
                            edge_data['shared_albums'] = edge_data.get('shared_albums', 0) + 1
        
        logger.info(f"Added {len(self.album_nodes)} album nodes")
        logger.info(f"Added {edges_added} artist-album edges")
        logger.info(f"Added {collaboration_edges} artist-artist collaboration edges")
    
    def create_similar_genre_edges(self, similarity_threshold: float = 0.3):
        """Create SIMILAR_GENRE edges between artists with similar genres"""
        logger.info("Creating SIMILAR_GENRE edges...")
        
        edges_added = 0
        
        # Get all artist nodes
        artist_nodes_list = list(self.artist_nodes.values())
        
        for i, artist1_id in enumerate(artist_nodes_list):
            artist1 = self.graph.nodes[artist1_id]
            genres1_str = artist1.get('genres', '')
            
            if not genres1_str:
                continue
            
            # Parse genres
            genres1 = set(g.lower().strip() for g in genres1_str.split(';') if g.strip())
            
            if not genres1:
                continue
            
            # Compare with other artists
            for artist2_id in artist_nodes_list[i+1:]:
                artist2 = self.graph.nodes[artist2_id]
                genres2_str = artist2.get('genres', '')
                
                if not genres2_str:
                    continue
                
                genres2 = set(g.lower().strip() for g in genres2_str.split(';') if g.strip())
                
                if not genres2:
                    continue
                
                # Calculate similarity
                common_genres = genres1.intersection(genres2)
                all_genres = genres1.union(genres2)
                
                if len(common_genres) > 0 and len(all_genres) > 0:
                    similarity = len(common_genres) / len(all_genres)
                    
                    # Create edge if similarity exceeds threshold
                    if similarity >= similarity_threshold:
                        # Check if edge already exists
                        if not self.graph.has_edge(artist1_id, artist2_id):
                            self.graph.add_edge(
                                artist1_id,
                                artist2_id,
                                relationship='SIMILAR_GENRE',
                                similarity=round(similarity, 3)
                            )
                            edges_added += 1
        
        logger.info(f"Added {edges_added} SIMILAR_GENRE edges")
        return edges_added
    
    def build_graph(self, nodes_path: str, albums_path: str) -> nx.Graph:
        """Build complete graph from processed data"""
        logger.info("Building graph network...")
        
        # Load data
        df = self.load_nodes(nodes_path)
        album_map = self.load_albums(albums_path)
        
        if df.empty:
            logger.error("No nodes to build graph")
            return self.graph
        
        # Build graph
        self.add_artist_nodes(df)
        self.add_album_nodes_and_edges(album_map)
        
        # Create similar genre edges
        self.create_similar_genre_edges(similarity_threshold=0.3)
        
        # Log statistics
        logger.info(f"Graph built successfully:")
        logger.info(f"  - Nodes: {self.graph.number_of_nodes()}")
        logger.info(f"  - Edges: {self.graph.number_of_edges()}")
        
        return self.graph
    
    def export_edges_csv(self, output_path: str):
        """Export edges to CSV for Neo4j import"""
        edges_data = []
        
        for u, v, data in self.graph.edges(data=True):
            edge_record = {
                'from': u,
                'to': v,
                'type': data.get('relationship', 'PERFORMS_ON')
            }
            
            # Add weight based on relationship type
            relationship = data.get('relationship', 'PERFORMS_ON')
            
            if relationship == 'COLLABORATES_WITH':
                edge_record['weight'] = data.get('shared_albums', 1)
            elif relationship == 'SIMILAR_GENRE':
                edge_record['weight'] = data.get('similarity', 0.5)
            else:
                edge_record['weight'] = 1
                
            edges_data.append(edge_record)
        
        df = pd.DataFrame(edges_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Log breakdown by type
        type_counts = df['type'].value_counts().to_dict()
        logger.info(f"Exported {len(edges_data)} edges to {output_path}")
        for edge_type, count in type_counts.items():
            logger.info(f"  - {edge_type}: {count}")
    
    def export_nodes_for_neo4j(self, output_dir: str):
        """Export nodes in Neo4j-friendly format"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export artist nodes
        artist_data = []
        for node_id in self.artist_nodes.values():
            node_attrs = self.graph.nodes[node_id]
            artist_data.append({
                'id': node_id,
                'name': node_attrs.get('name', ''),
                'genres': node_attrs.get('genres', ''),
                'instruments': node_attrs.get('instruments', ''),
                'active_years': node_attrs.get('active_years', ''),
                'url': node_attrs.get('url', '')
            })
        
        df_artists = pd.DataFrame(artist_data)
        df_artists.to_csv(f"{output_dir}/artists.csv", index=False, encoding='utf-8')
        logger.info(f"Exported {len(artist_data)} artists to {output_dir}/artists.csv")
        
        # Export album nodes
        album_data = []
        for node_id in self.album_nodes.values():
            node_attrs = self.graph.nodes[node_id]
            album_data.append({
                'id': node_id,
                'title': node_attrs.get('title', '')
            })
        
        df_albums = pd.DataFrame(album_data)
        df_albums.to_csv(f"{output_dir}/albums.csv", index=False, encoding='utf-8')
        logger.info(f"Exported {len(album_data)} albums to {output_dir}/albums.csv")
    
    def save_graph(self, output_path: str):
        """Save graph in GraphML format"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        nx.write_graphml(self.graph, output_path)
        logger.info(f"Saved graph to {output_path}")


def build_graph(nodes_path: str = "data/processed/nodes.csv",
                albums_path: str = "data/processed/albums.json",
                output_dir: str = "data/processed") -> int:
    """Main function to build graph"""
    builder = GraphBuilder()
    graph = builder.build_graph(nodes_path, albums_path)
    
    # Export for Neo4j
    builder.export_nodes_for_neo4j(output_dir)
    builder.export_edges_csv(f"{output_dir}/edges.csv")
    
    # Save graph file
    builder.save_graph(f"{output_dir}/network.graphml")
    
    return graph.number_of_nodes()


if __name__ == "__main__":
    build_graph()


"""Run community detection and clustering analysis on the music network"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analysis.communities import analyze_communities
from analysis.viz import create_community_visualizations


def main():
    """Run community analysis and create visualizations"""
    print("=" * 60)
    print("Community Detection and Clustering Analysis")
    print("=" * 60)
    
    # Run community analysis
    print("\n1. Running community detection algorithms...")
    community_analysis = analyze_communities(
        graph_path="data/processed/network.graphml",
        output_path="data/processed/community_analysis.json"
    )
    
    # Print summary
    if community_analysis:
        print("\n" + "=" * 60)
        print("Community Analysis Summary")
        print("=" * 60)
        
        if 'louvain' in community_analysis:
            louvain = community_analysis['louvain']
            print(f"\n📊 Louvain Algorithm:")
            print(f"   - Number of communities: {louvain['num_communities']}")
            print(f"   - Modularity score: {louvain['modularity']:.4f}")
            print(f"   - Average community size: {louvain['size_analysis']['avg_size']:.1f}")
            print(f"   - Largest community size: {louvain['size_analysis']['max_size']}")
            print(f"   - Small communities (<5): {louvain['size_analysis']['small_communities']}")
            print(f"   - Medium communities (5-19): {louvain['size_analysis']['medium_communities']}")
            print(f"   - Large communities (>=20): {louvain['size_analysis']['large_communities']}")
        
        if 'greedy_modularity' in community_analysis:
            greedy = community_analysis['greedy_modularity']
            print(f"\n📊 Greedy Modularity Algorithm:")
            print(f"   - Number of communities: {greedy['num_communities']}")
            print(f"   - Modularity score: {greedy['modularity']:.4f}")
        
        if 'clustering' in community_analysis:
            clustering = community_analysis['clustering']
            print(f"\n🔗 Clustering Analysis:")
            print(f"   - Average clustering coefficient: {clustering['average_clustering']:.4f}")
            print(f"   - Transitivity: {clustering['transitivity']:.4f}")
            print(f"   - Max clustering: {clustering['max_clustering']:.4f}")
            print(f"   - Median clustering: {clustering['median_clustering']:.4f}")
        
        if 'small_world' in community_analysis:
            sw = community_analysis['small_world']
            print(f"\n🌐 Small-World Properties:")
            print(f"   - Number of connected components: {sw['num_connected_components']}")
            print(f"   - Largest component size: {sw['largest_component_size']}")
            if sw.get('avg_path_length'):
                print(f"   - Average path length: {sw['avg_path_length']:.2f}")
            if sw.get('diameter'):
                print(f"   - Diameter: {sw['diameter']}")
        
        if 'density' in community_analysis:
            density = community_analysis['density']
            print(f"\n📈 Network Density:")
            print(f"   - Overall density: {density['overall_density']:.6f}")
            print(f"   - Largest component density: {density['largest_component_density']:.6f}")
        
        # Show largest communities
        if 'louvain' in community_analysis:
            print(f"\n🏆 Top 5 Largest Communities:")
            for i, comm in enumerate(community_analysis['louvain']['largest_communities']):
                print(f"\n   Community {comm['community_id']} (Size: {comm['size']}):")
                print(f"   Members: {', '.join(comm['members'][:10])}")
                if i < len(community_analysis['louvain']['genre_analysis']):
                    genre_info = community_analysis['louvain']['genre_analysis'][i]
                    if genre_info['top_genres']:
                        top_genres = ', '.join([f"{g} ({c})" for g, c in genre_info['top_genres'].items()])
                        print(f"   Top genres: {top_genres}")
    
    # Create visualizations
    print("\n" + "=" * 60)
    print("2. Creating community visualizations...")
    print("=" * 60)
    
    create_community_visualizations(
        graph_path="data/processed/network.graphml",
        community_analysis_path="data/processed/community_analysis.json",
        output_dir="data/processed/figures"
    )
    
    print("\n✅ Community analysis completed!")
    print("\nOutput files:")
    print("  - data/processed/community_analysis.json")
    print("  - data/processed/figures/louvain_communities.png")
    print("  - data/processed/figures/louvain_community_sizes.png")
    print("  - data/processed/figures/clustering_coefficient_distribution.png")


if __name__ == "__main__":
    main()


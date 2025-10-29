#!/usr/bin/env python3
"""Analyze degree statistics from edges"""

import csv
from collections import defaultdict

def analyze_degrees(edges_file):
    """Analyze degree statistics"""
    print(f"Analyzing degrees from {edges_file}...")
    
    # Count degrees for each node
    degrees = defaultdict(int)
    
    with open(edges_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_node = row['from']
            to_node = row['to']
            
            # Count degree for both nodes
            degrees[from_node] += 1
            degrees[to_node] += 1
    
    # Calculate statistics
    if not degrees:
        print("No degrees found!")
        return
    
    degree_values = list(degrees.values())
    degree_values.sort(reverse=True)
    
    avg_degree = sum(degree_values) / len(degree_values)
    max_degree = max(degree_values)
    min_degree = min(degree_values)
    median_degree = degree_values[len(degree_values) // 2]
    
    print(f"\n=== Degree Statistics ===")
    print(f"Total nodes: {len(degrees)}")
    print(f"Average degree: {avg_degree:.2f}")
    print(f"Max degree: {max_degree}")
    print(f"Min degree: {min_degree}")
    print(f"Median degree: {median_degree}")
    
    # Show top 10 nodes by degree
    sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n=== Top 10 Nodes by Degree ===")
    for i, (node, degree) in enumerate(sorted_nodes[:10], 1):
        print(f"{i}. {node}: degree {degree}")
    
    # Count nodes with very high degree
    high_degree_count = sum(1 for d in degree_values if d >= 50)
    print(f"\nNodes with degree >= 50: {high_degree_count}")

if __name__ == "__main__":
    analyze_degrees("data/processed/filtered/edges.csv")


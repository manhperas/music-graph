#!/usr/bin/env python3
"""
Quick validation script cho Phase 2 - không cần dependencies
Chỉ kiểm tra files CSV đã được tạo đúng chưa
"""

import os
import pandas as pd
import sys

def check_files():
    """Check if required files exist and have correct data"""
    print("=" * 60)
    print("PHASE 2 QUICK VALIDATION")
    print("=" * 60)
    
    results = {}
    
    # Check 1: nodes.csv has labels column
    print("\n[1] Checking nodes.csv...")
    nodes_path = "data/processed/nodes.csv"
    if os.path.exists(nodes_path):
        try:
            df = pd.read_csv(nodes_path)
            has_labels = 'labels' in df.columns
            if has_labels:
                labels_count = df['labels'].notna().sum()
                all_labels = set()
                for labels_str in df['labels'].dropna():
                    if labels_str:
                        labels = [l.strip() for l in str(labels_str).split(';') if l.strip()]
                        all_labels.update(labels)
                print(f"  ✓ nodes.csv exists")
                print(f"  ✓ Has 'labels' column")
                print(f"  ✓ {labels_count} artists have labels")
                print(f"  ✓ {len(all_labels)} unique record labels found")
                if len(all_labels) > 0:
                    print(f"  ✓ Sample labels: {list(all_labels)[:5]}")
                results['nodes_csv'] = True
            else:
                print(f"  ✗ Missing 'labels' column")
                results['nodes_csv'] = False
        except Exception as e:
            print(f"  ✗ Error reading nodes.csv: {e}")
            results['nodes_csv'] = False
    else:
        print(f"  ✗ nodes.csv not found")
        results['nodes_csv'] = False
    
    # Check 2: record_labels.csv exists
    print("\n[2] Checking record_labels.csv...")
    labels_path = "data/processed/record_labels.csv"
    if os.path.exists(labels_path):
        try:
            df = pd.read_csv(labels_path)
            print(f"  ✓ record_labels.csv exists")
            print(f"  ✓ Contains {len(df)} record labels")
            if len(df) > 0:
                print(f"  ✓ Sample labels: {df.head(5)['name'].tolist()}")
            results['record_labels_csv'] = True
        except Exception as e:
            print(f"  ✗ Error reading record_labels.csv: {e}")
            results['record_labels_csv'] = False
    else:
        print(f"  ✗ record_labels.csv not found")
        results['record_labels_csv'] = False
    
    # Check 3: edges.csv has SIGNED_WITH edges
    print("\n[3] Checking edges.csv for SIGNED_WITH...")
    edges_path = "data/processed/edges.csv"
    if os.path.exists(edges_path):
        try:
            df = pd.read_csv(edges_path)
            if 'type' in df.columns:
                signed_with_count = len(df[df['type'] == 'SIGNED_WITH'])
                print(f"  ✓ edges.csv exists")
                print(f"  ✓ Contains {signed_with_count} SIGNED_WITH edges")
                if signed_with_count > 0:
                    sample = df[df['type'] == 'SIGNED_WITH'].head(3)
                    print(f"  ✓ Sample edges:")
                    for idx, row in sample.iterrows():
                        print(f"      {row['from']} -> {row['to']}")
                results['signed_with_edges'] = signed_with_count > 0
            else:
                print(f"  ✗ Missing 'type' column")
                results['signed_with_edges'] = False
        except Exception as e:
            print(f"  ✗ Error reading edges.csv: {e}")
            results['signed_with_edges'] = False
    else:
        print(f"  ✗ edges.csv not found")
        results['signed_with_edges'] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")
    
    if all_passed:
        print("\n✓ All file checks passed!")
        print("Next steps:")
        print("  1. Start Neo4j: docker-compose up -d")
        print("  2. Import to Neo4j: uv run python src/main.py import")
        print("  3. Verify with Cypher: python3 cypher_validation_queries.py")
    else:
        print("\n✗ Some checks failed!")
        print("Next steps:")
        print("  1. Re-process data: uv run python src/main.py process")
        print("  2. Re-build graph: uv run python src/main.py build")
    
    return all_passed

if __name__ == "__main__":
    success = check_files()
    sys.exit(0 if success else 1)


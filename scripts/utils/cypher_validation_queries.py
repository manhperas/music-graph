#!/usr/bin/env python3
"""
Cypher Queries để Verify Phase 2: Record Label Nodes + SIGNED_WITH Relationships
"""

# Copy các queries này vào Neo4j Browser để verify data

CYPHER_QUERIES = """
// ============================================================
// PHASE 2 VALIDATION QUERIES
// ============================================================

// Query 1: Count RecordLabel nodes
MATCH (r:RecordLabel)
RETURN count(r) AS record_label_count

// Query 2: Count SIGNED_WITH relationships
MATCH ()-[r:SIGNED_WITH]->()
RETURN count(r) AS signed_with_count

// Query 3: Sample RecordLabel nodes
MATCH (r:RecordLabel)
RETURN r.id AS id, r.name AS name
LIMIT 10

// Query 4: Artists signed with record labels (sample)
MATCH (a:Artist)-[:SIGNED_WITH]->(r:RecordLabel)
RETURN a.name AS artist, r.name AS label
LIMIT 10

// Query 5: Top 10 record labels by number of artists
MATCH (a:Artist)-[:SIGNED_WITH]->(r:RecordLabel)
RETURN r.name AS label, count(a) AS artist_count
ORDER BY artist_count DESC
LIMIT 10

// Query 6: Artists signed with multiple labels
MATCH (a:Artist)-[:SIGNED_WITH]->(r:RecordLabel)
WITH a, collect(r.name) AS labels
WHERE size(labels) > 1
RETURN a.name AS artist, labels
LIMIT 10

// Query 7: Record labels network connections
MATCH (r:RecordLabel)
OPTIONAL MATCH (a:Artist)-[:SIGNED_WITH]->(r)
OPTIONAL MATCH (a)-[:COLLABORATES_WITH]-(other:Artist)
RETURN r.name AS label, 
       count(DISTINCT a) AS artists,
       count(DISTINCT other) AS collaborators
ORDER BY artists DESC
LIMIT 10

// Query 8: Full network overview
MATCH (n)
RETURN labels(n)[0] AS node_type, count(n) AS count
ORDER BY count DESC

// Query 9: Relationship types overview
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS count
ORDER BY count DESC

// Query 10: Verify RecordLabel constraint exists
CALL db.constraints()
YIELD name, description
WHERE name CONTAINS 'recordlabel'
RETURN name, description
"""

if __name__ == "__main__":
    print("=" * 60)
    print("CYPHER QUERIES FOR PHASE 2 VALIDATION")
    print("=" * 60)
    print("\nCopy these queries to Neo4j Browser (http://localhost:7474)")
    print("Run each query to verify Phase 2 implementation\n")
    print(CYPHER_QUERIES)
    print("\n" + "=" * 60)
    print("Instructions:")
    print("1. Open Neo4j Browser: http://localhost:7474")
    print("2. Copy each query above and run it")
    print("3. Verify the results match expected values")
    print("=" * 60)


# Cypher Queries for Phase 4 Validation

These queries can be run in Neo4j Browser or Cypher Shell to validate Award nodes and AWARD_NOMINATION relationships.

## Basic Counts

```cypher
// Count all Award nodes
MATCH (a:Award)
RETURN count(a) AS award_count;

// Count all AWARD_NOMINATION relationships
MATCH ()-[r:AWARD_NOMINATION]->()
RETURN count(r) AS relationship_count;

// Count Award nodes by ceremony
MATCH (a:Award)
RETURN a.ceremony AS ceremony, count(a) AS count
ORDER BY count DESC;

// Count Award nodes by category
MATCH (a:Award)
RETURN a.category AS category, count(a) AS count
ORDER BY count DESC
LIMIT 20;
```

## Artists and Awards

```cypher
// Top 10 artists with most awards
MATCH (a:Artist)-[:AWARD_NOMINATION]->(aw:Award)
RETURN a.name AS artist, count(aw) AS award_count
ORDER BY award_count DESC
LIMIT 10;

// Artists with awards, showing status (won/nominated)
MATCH (a:Artist)-[r:AWARD_NOMINATION]->(aw:Award)
RETURN a.name AS artist, aw.ceremony AS ceremony, aw.category AS category, 
       aw.year AS year, COALESCE(r.status, 'nominated') AS status
ORDER BY a.name, aw.year DESC
LIMIT 20;

// Artists with won awards
MATCH (a:Artist)-[r:AWARD_NOMINATION {status: 'won'}]->(aw:Award)
RETURN a.name AS artist, aw.ceremony AS ceremony, aw.category AS category, aw.year AS year
ORDER BY aw.year DESC
LIMIT 20;
```

## Awards Analysis

```cypher
// Awards by year
MATCH (a:Award)
WHERE a.year IS NOT NULL AND a.year <> ''
RETURN a.year AS year, count(a) AS count
ORDER BY year DESC;

// Most awarded ceremonies
MATCH (a:Award)
RETURN a.ceremony AS ceremony, count(a) AS award_count
ORDER BY award_count DESC;

// Most common award categories
MATCH (a:Award)
RETURN a.category AS category, count(a) AS count
ORDER BY count DESC
LIMIT 15;
```

## Relationship Properties

```cypher
// AWARD_NOMINATION relationships with status property
MATCH ()-[r:AWARD_NOMINATION]->()
RETURN 
    count(r) AS total_relationships,
    count(r.status) AS with_status,
    count(r.year) AS with_year;

// Breakdown of status values
MATCH ()-[r:AWARD_NOMINATION]->()
RETURN 
    COALESCE(r.status, 'unspecified') AS status,
    count(r) AS count
ORDER BY count DESC;
```

## Validation Queries

```cypher
// Check for Award nodes without relationships (orphan nodes)
MATCH (a:Award)
WHERE NOT ()-[:AWARD_NOMINATION]->(a)
RETURN count(a) AS orphan_awards;

// Check for AWARD_NOMINATION relationships without proper node types
MATCH (from)-[r:AWARD_NOMINATION]->(to)
WHERE NOT (from:Artist OR from:Band) OR NOT (to:Award)
RETURN count(r) AS invalid_relationships;

// Summary statistics
MATCH (a:Award)
WITH count(a) AS award_count
MATCH ()-[r:AWARD_NOMINATION]->()
WITH award_count, count(r) AS relationship_count
MATCH (artist:Artist)-[:AWARD_NOMINATION]->()
WITH award_count, relationship_count, count(DISTINCT artist) AS artists_with_awards
RETURN 
    award_count AS total_awards,
    relationship_count AS total_nominations,
    artists_with_awards AS artists_with_awards,
    toFloat(relationship_count) / award_count AS avg_nominations_per_award;
```

## Seed Artists Validation

```cypher
// Percentage of artists with awards
MATCH (total:Artist)
WITH count(total) AS total_artists
MATCH (awarded:Artist)-[:AWARD_NOMINATION]->()
WITH total_artists, count(DISTINCT awarded) AS awarded_artists
RETURN 
    total_artists AS total_artists,
    awarded_artists AS artists_with_awards,
    toFloat(awarded_artists) / total_artists * 100 AS percentage_with_awards;
```


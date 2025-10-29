# CÁC QUERIES ĐỂ XEM DATA TRONG NEO4J

## 📊 1. XEM TỔNG QUAN

### Đếm số nodes và relationships:
```cypher
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Count
ORDER BY Count DESC
```

### Đếm số relationships theo loại:
```cypher
MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC
```

---

## 🎵 2. XEM ARTISTS

### Xem 10 artists đầu tiên:
```cypher
MATCH (a:Artist)
RETURN a.name AS Name, a.genres AS Genres
LIMIT 10
```

### Tìm artists theo tên:
```cypher
MATCH (a:Artist)
WHERE a.name CONTAINS 'Taylor'
RETURN a.name, a.genres, a.url
```

### Artists có nhiều collaborations nhất:
```cypher
MATCH (a:Artist)-[:COLLABORATES_WITH]->()
RETURN a.name AS Artist, count(*) AS Collaborations
ORDER BY Collaborations DESC
LIMIT 10
```

---

## 🎤 3. XEM COLLABORATIONS

### Xem collaboration giữa 2 artists:
```cypher
MATCH (a1:Artist)-[r:COLLABORATES_WITH]->(a2:Artist)
RETURN a1.name AS Artist1, a2.name AS Artist2, r.shared_albums AS SharedAlbums
LIMIT 20
```

### Top collaborations mạnh nhất (nhiều shared albums):
```cypher
MATCH (a1:Artist)-[r:COLLABORATES_WITH]->(a2:Artist)
WHERE r.shared_albums > 0
RETURN a1.name AS Artist1, a2.name AS Artist2, r.shared_albums AS SharedAlbums
ORDER BY r.shared_albums DESC
LIMIT 10
```

---

## 🎶 4. XEM ALBUMS

### Xem albums và artists:
```cypher
MATCH (a:Artist)-[:PERFORMS_ON]->(alb:Album)
RETURN a.name AS Artist, alb.title AS Album
LIMIT 20
```

### Albums có nhiều artists nhất:
```cypher
MATCH (a:Artist)-[:PERFORMS_ON]->(alb:Album)
RETURN alb.title AS Album, count(a) AS NumberOfArtists
ORDER BY NumberOfArtists DESC
LIMIT 10
```

---

## 🎼 5. XEM SIMILAR GENRES

### Artists có genre tương tự:
```cypher
MATCH (a1:Artist)-[r:SIMILAR_GENRE]->(a2:Artist)
RETURN a1.name AS Artist1, a2.name AS Artist2, r.similarity AS Similarity
ORDER BY r.similarity DESC
LIMIT 20
```

### Tìm artists tương tự với một artist cụ thể:
```cypher
MATCH (a1:Artist {name: 'Taylor Swift'})-[r:SIMILAR_GENRE]->(a2:Artist)
RETURN a2.name AS SimilarArtist, r.similarity AS Similarity
ORDER BY r.similarity DESC
LIMIT 10
```

---

## 🎯 6. VISUALIZE NETWORK

### Xem network của một artist:
```cypher
MATCH (a:Artist {name: 'Taylor Swift'})-[r]-(connected)
RETURN a, r, connected
LIMIT 50
```

### Xem full network sample (nhiều nodes):
```cypher
MATCH (a:Artist)-[r:COLLABORATES_WITH]->(a2:Artist)
RETURN a, r, a2
LIMIT 100
```

### Network theo albums:
```cypher
MATCH (a:Artist)-[:PERFORMS_ON]->(alb:Album)<-[:PERFORMS_ON]-(a2:Artist)
RETURN a, alb, a2
LIMIT 50
```

---

## 🔍 7. TÌM KIẾM NÂNG CAO

### Tìm artists connected qua nhiều albums:
```cypher
MATCH path = (a1:Artist)-[:PERFORMS_ON]->(:Album)<-[:PERFORMS_ON]-(a2:Artist)
WHERE a1 <> a2
RETURN a1.name AS Artist1, a2.name AS Artist2, count(path) AS ConnectedAlbums
ORDER BY ConnectedAlbums DESC
LIMIT 20
```

### Shortest path giữa 2 artists:
```cypher
MATCH path = shortestPath(
  (a1:Artist {name: 'Taylor Swift'})-[*]-(a2:Artist {name: 'Ed Sheeran'})
)
RETURN path
```

### Artists có degree cao nhất (nhiều connections):
```cypher
MATCH (a:Artist)
WITH a, size((a)-[]-()) AS degree
RETURN a.name AS Artist, degree
ORDER BY degree DESC
LIMIT 20
```

---

## 📈 8. STATISTICS

### Genres phổ biến nhất:
```cypher
MATCH (a:Artist)
WHERE a.genres IS NOT NULL AND a.genres <> ''
UNWIND split(a.genres, ';') AS genre
RETURN trim(genre) AS Genre, count(*) AS Count
ORDER BY Count DESC
LIMIT 20
```

### Average collaborations per artist:
```cypher
MATCH (a:Artist)
OPTIONAL MATCH (a)-[:COLLABORATES_WITH]->()
WITH a, count(*) AS collabs
RETURN avg(collabs) AS AvgCollaborations, 
       max(collabs) AS MaxCollaborations,
       min(collabs) AS MinCollaborations
```

---

## 🎨 9. GRAPH EXAMPLES

### Xem một cluster nhỏ:
```cypher
MATCH (a:Artist)-[r:COLLABORATES_WITH]->(a2:Artist)
WHERE a.name IN ['Taylor Swift', 'Ed Sheeran', 'Adele']
RETURN a, r, a2
```

### Tìm island nodes (không có connections):
```cypher
MATCH (a:Artist)
WHERE NOT (a)-[]-()
RETURN a.name AS IsolatedArtist
LIMIT 20
```

---

## 🚀 QUICK QUERIES

### Tất cả trong một:
```cypher
// Đếm tổng
MATCH (n)
RETURN count(n) AS TotalNodes;

MATCH ()-[r]->()
RETURN count(r) AS TotalRelationships;

// Top artists
MATCH (a:Artist)
OPTIONAL MATCH (a)-[:COLLABORATES_WITH]->()
RETURN a.name AS Artist, count(*) AS Collaborations
ORDER BY Collaborations DESC
LIMIT 10
```


# VAI TRÒ CỦA NEO4J TRONG DỰ ÁN

## 🎯 TỔNG QUAN

Neo4j là **Graph Database** được sử dụng làm **persistent storage** và **query engine** cho mạng lưới collaboration của nghệ sĩ trong dự án này.

---

## 📊 VAI TRÒ CỦA NEO4J

### **1. Graph Database (Cơ sở dữ liệu đồ thị)**

**Khác với SQL Database**:
- SQL: Tables với rows và columns
- Neo4j: Nodes và Relationships
- Lưu trữ cấu trúc graph một cách tự nhiên

**Phù hợp với dự án**:
- ✅ Collaboration network là graph structure
- ✅ Nodes = Artists, Albums
- ✅ Relationships = PERFORMS_ON, COLLABORATES_WITH, SIMILAR_GENRE
- ✅ Query theo mẫu relationships dễ dàng

---

### **2. Persistent Storage (Lưu trữ bền vững)**

**NetworkX chỉ lưu trong memory**:
```python
# NetworkX graph chỉ tồn tại khi code chạy
graph = nx.Graph()
# Tắt program → mất data
```

**Neo4j lưu trên disk**:
```
Neo4j database persist trên disk
→ Có thể query lại sau khi restart
→ Không mất data
```

---

### **3. Query Engine (Công cụ truy vấn)**

**Neo4j sử dụng Cypher Query Language**:

```cypher
// Tìm nghệ sĩ hợp tác với Taylor Swift
MATCH (ts:Artist {name: "Taylor Swift"})-[:COLLABORATES_WITH]-(other:Artist)
RETURN other.name, shared_albums
ORDER BY shared_albums DESC
```

**Truy vấn phức tạp dễ dàng**:
- ✅ Shortest path giữa 2 nghệ sĩ
- ✅ Community detection
- ✅ PageRank với relationships
- ✅ Pattern matching phức tạp

---

### **4. Neo4j Browser (Giao diện trực quan)**

**Neo4j Browser** (http://localhost:7474):
- Visualize graph network
- Query và xem kết quả
- Explore relationships
- Debug và analyze

---

## 🔧 KIẾN TRÚC DỰ ÁN

### **Workflow**:

```
1. Python Scripts
   ├─ Scrape Wikipedia
   ├─ Parse và clean data
   ├─ Build graph với NetworkX
   └─ Export to CSV
   
2. Neo4j Importer
   ├─ Read CSV files
   ├─ Import nodes và relationships
   └─ Create constraints & indexes
   
3. Neo4j Database
   ├─ Store graph persistently
   ├─ Execute Cypher queries
   └─ Provide data for analysis
   
4. Python Analysis
   ├─ Query Neo4j for stats
   ├─ Compute metrics
   └─ Generate visualizations
```

---

## 🎨 CẤU TRÚC DỮ LIỆU TRONG NEO4J

### **Nodes (Điểm nút)**:

**Artist Node**:
```cypher
(:Artist {
  id: "artist_0",
  name: "Taylor Swift",
  genres: "pop; country; folk",
  instruments: "vocals; guitar; piano",
  active_years: "2006-present",
  url: "https://vi.wikipedia.org/..."
})
```

**Album Node**:
```cypher
(:Album {
  id: "album_0",
  title: "1989"
})
```

### **Relationships (Mối quan hệ)**:

**PERFORMS_ON**:
```cypher
(Artist)-[:PERFORMS_ON]->(Album)
```

**COLLABORATES_WITH**:
```cypher
(Artist)-[:COLLABORATES_WITH {shared_albums: 2}]-(Artist)
```

**SIMILAR_GENRE**:
```cypher
(Artist)-[:SIMILAR_GENRE {similarity: 0.75}]-(Artist)
```

---

## 🚀 CÁCH CHẠY NEO4J

### **Bước 1: Khởi động Neo4j**

**Dùng Docker** (đã có sẵn trong dự án):
```bash
# Start Neo4j container
docker-compose up -d

# Check status
docker-compose ps
```

**Output**:
```
neo4j running on:
- HTTP: http://localhost:7474
- Bolt: bolt://localhost:7687
```

### **Bước 2: Truy cập Neo4j Browser**

```bash
# Mở browser
http://localhost:7474
```

**Login**:
- Username: `neo4j`
- Password: `password` (hoặc password từ .env)

### **Bước 3: Import dữ liệu**

```bash
# Chạy pipeline đầy đủ
./run.sh all

# Hoặc chỉ import vào Neo4j
./run.sh import
```

**Import process**:
```
1. Clear database (nếu cần)
2. Create constraints & indexes
3. Import Artist nodes
4. Import Album nodes
5. Import Relationships:
   - PERFORMS_ON
   - COLLABORATES_WITH
   - SIMILAR_GENRE
6. Verify import
```

---

## 📝 CYPHER QUERIES MẪU

### **1. Count nodes**:

```cypher
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS count
```

**Output**:
```
label    | count
---------|-------
Artist   | 1000
Album    | 500
```

---

### **2. Tìm top collaborators**:

```cypher
MATCH (a:Artist)-[:COLLABORATES_WITH]-()
WITH a, count(*) AS collaborators
ORDER BY collaborators DESC
LIMIT 10
RETURN a.name, collaborators
```

**Output**:
```
name           | collaborators
---------------|-------------
Taylor Swift   | 15
Ed Sheeran     | 12
Bruno Mars     | 10
...
```

---

### **3. Tìm artists cùng genre**:

```cypher
MATCH (a:Artist {name: "Taylor Swift"})-[r:SIMILAR_GENRE]-(other:Artist)
RETURN other.name, r.similarity
ORDER BY r.similarity DESC
LIMIT 10
```

---

### **4. Shortest path giữa 2 artists**:

```cypher
MATCH path = shortestPath(
  (a1:Artist {name: "Taylor Swift"})-[:COLLABORATES_WITH*]-(a2:Artist {name: "Bruno Mars"})
)
RETURN path
```

---

### **5. Community detection**:

```cypher
MATCH (a:Artist)-[:COLLABORATES_WITH]-(other:Artist)
WHERE a.name = "Taylor Swift"
RETURN collect(DISTINCT other.name) AS collaborators
```

---

## 🔍 TẠI SAO DÙNG NEO4J?

### **So sánh với SQL Database**:

**SQL**:
```sql
-- Phức tạp để tìm collaborators
SELECT DISTINCT a2.name
FROM artists a1
JOIN album_artists aa1 ON a1.id = aa1.artist_id
JOIN album_artists aa2 ON aa1.album_id = aa2.album_id
JOIN artists a2 ON aa2.artist_id = a2.id
WHERE a1.name = "Taylor Swift" AND a1.id != a2.id
```

**Neo4j (Cypher)**:
```cypher
-- Đơn giản và trực quan
MATCH (a1:Artist {name: "Taylor Swift"})-[:COLLABORATES_WITH]-(a2:Artist)
RETURN a2.name
```

### **Ưu điểm**:

✅ **Query đơn giản**: Cypher tự nhiên hơn SQL cho graph  
✅ **Performance**: Tối ưu cho graph traversal  
✅ **Visualization**: Neo4j Browser visualize graph  
✅ **Scalability**: Handle large graphs tốt  
✅ **Relationships**: First-class citizen  

---

## 📊 WORKFLOW CHI TIẾT

### **Stage 1: Build Graph (NetworkX)**

```python
# Python code
graph = nx.Graph()
graph.add_node("artist_0", name="Taylor Swift", ...)
graph.add_edge("artist_0", "album_0", relationship='PERFORMS_ON')
graph.add_edge("artist_0", "artist_1", relationship='COLLABORATES_WITH')
```

### **Stage 2: Export to CSV**

```python
# Export nodes
artists.csv: id, name, genres, ...
albums.csv: id, title

# Export edges
edges.csv: from, to, type, weight
```

### **Stage 3: Import to Neo4j**

```python
# Python Neo4j driver
driver = GraphDatabase.driver("bolt://localhost:7687")
session = driver.session()

# Import nodes
session.run("CREATE (a:Artist {id: $id, name: $name, ...})", ...)

# Import relationships
session.run("MATCH (from {id: $from}) MATCH (to {id: $to}) CREATE (from)-[:PERFORMS_ON]->(to)", ...)
```

### **Stage 4: Query Neo4j**

```python
# Python query Neo4j
result = session.run("MATCH (a:Artist)-[:COLLABORATES_WITH]-() RETURN a.name, count(*) AS degree")
stats = [record.values() for record in result]
```

---

## 🎯 USE CASES TRONG DỰ ÁN

### **1. Collaboration Analysis**:

```cypher
// Nghệ sĩ có nhiều collaborations nhất
MATCH (a:Artist)-[:COLLABORATES_WITH]-()
WITH a, count(*) AS collab_count
ORDER BY collab_count DESC
LIMIT 10
RETURN a.name, collab_count
```

### **2. Genre Communities**:

```cypher
// Nhóm nghệ sĩ cùng genre
MATCH (a:Artist)-[:SIMILAR_GENRE]-(b:Artist)
WHERE a.genres CONTAINS 'pop'
RETURN collect(DISTINCT a.name) AS pop_artists
```

### **3. PageRank Analysis**:

```cypher
// Influence trong network
CALL gds.pageRank.stream({
  nodeProjection: 'Artist',
  relationshipProjection: {
    COLLABORATES_WITH: {type: 'COLLABORATES_WITH', orientation: 'UNDIRECTED'}
  }
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS artist, score
ORDER BY score DESC
LIMIT 10
```

### **4. Path Finding**:

```cypher
// Tìm đường ngắn nhất giữa 2 nghệ sĩ
MATCH path = shortestPath(
  (a1:Artist {name: "Taylor Swift"})-[:COLLABORATES_WITH*]-(a2:Artist {name: "Bruno Mars"})
)
RETURN path
```

---

## 🔧 TECHNICAL DETAILS

### **Connection**:

```python
# config/neo4j_config.json
{
  "uri": "bolt://localhost:7687",
  "user": "neo4j",
  "database": "neo4j"
}
```

### **Authentication**:

```bash
# .env file
NEO4J_PASS=password
```

### **Docker Setup**:

```yaml
# docker-compose.yml
neo4j:
  image: neo4j:5.20-community
  ports:
    - "7474:7474"  # HTTP Browser
    - "7687:7687"  # Bolt Protocol
```

---

## 📈 KẾT QUẢ

**Sau khi import**:
- ✅ ~1000 Artist nodes
- ✅ ~500 Album nodes
- ✅ ~2000 PERFORMS_ON relationships
- ✅ ~800 COLLABORATES_WITH relationships
- ✅ ~2500 SIMILAR_GENRE relationships

**Total**: ~1500 nodes, ~5300 relationships

---

## 🎓 TÓM TẮT

**Neo4j trong dự án này**:

1. **Storage**: Lưu trữ collaboration network persistently
2. **Query**: Execute Cypher queries phức tạp
3. **Visualization**: Neo4j Browser visualize graph
4. **Analysis**: Support advanced graph algorithms
5. **Integration**: Python ↔ Neo4j seamless connection

**Lợi ích**:
- ✅ Query graph relationships dễ dàng
- ✅ Performance tốt cho graph traversal
- ✅ Visualization trực quan
- ✅ Scalable cho networks lớn
- ✅ Industry-standard graph database

**So với NetworkX**:
- NetworkX: Analysis trong memory
- Neo4j: Persistent storage + production-ready
- Kết hợp: Best of both worlds!



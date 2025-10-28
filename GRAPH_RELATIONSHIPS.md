# Graph Relationships Documentation

## 📊 Cấu trúc Graph Network

Project này tạo ra **3 loại mối quan hệ chất lượng** giữa các node để phân tích mạng lưới hợp tác của nghệ sĩ:

### 1️⃣ Node Types (Loại Node)

#### Artist Nodes (Node Nghệ sĩ)
```
(:Artist {
  id: "artist_123",
  name: "Tên nghệ sĩ",
  genres: "pop; dance; r&b",
  instruments: "vocals; guitar; piano",
  active_years: "2000-2020",
  url: "wikipedia_url"
})
```

#### Album Nodes (Node Album)
```
(:Album {
  id: "album_456",
  title: "Tên album"
})
```

---

## 🔗 Relationship Types (Loại Mối Quan Hệ)

### 1. PERFORMS_ON (Nghệ sĩ biểu diễn trên Album)

**Pattern**: `(Artist)-[:PERFORMS_ON]->(Album)`

**Ý nghĩa**: Nghệ sĩ đã phát hành hoặc biểu diễn trên một album/bài hát

**Properties**: Không có

**Ví dụ**:
```cypher
// Tìm tất cả album của một nghệ sĩ
MATCH (a:Artist {name: "Taylor Swift"})-[:PERFORMS_ON]->(album:Album)
RETURN album.title

// Đếm số album của mỗi nghệ sĩ
MATCH (a:Artist)-[:PERFORMS_ON]->(album:Album)
RETURN a.name, count(album) AS album_count
ORDER BY album_count DESC
```

---

### 2. COLLABORATES_WITH (Nghệ sĩ hợp tác với nghệ sĩ) ⭐

**Pattern**: `(Artist)-[:COLLABORATES_WITH {shared_albums: n}]-(Artist)`

**Ý nghĩa**: Hai nghệ sĩ đã hợp tác với nhau (cùng xuất hiện trên ít nhất một album)

**Properties**:
- `shared_albums`: Số lượng album mà 2 nghệ sĩ cùng tham gia

**Đặc điểm**:
- Mối quan hệ **vô hướng** (undirected)
- Có **trọng số** (weighted) - số album chung
- Tự động được tạo khi 2 nghệ sĩ cùng có PERFORMS_ON một album

**Ví dụ**:
```cypher
// Tìm các nghệ sĩ hợp tác với một nghệ sĩ cụ thể
MATCH (a1:Artist {name: "Ed Sheeran"})-[r:COLLABORATES_WITH]-(a2:Artist)
RETURN a2.name, r.shared_albums
ORDER BY r.shared_albums DESC

// Tìm các cặp nghệ sĩ có nhiều hợp tác nhất
MATCH (a1:Artist)-[r:COLLABORATES_WITH]-(a2:Artist)
WHERE id(a1) < id(a2)
RETURN a1.name, a2.name, r.shared_albums
ORDER BY r.shared_albums DESC
LIMIT 10

// Tìm nghệ sĩ có nhiều partner hợp tác nhất
MATCH (a:Artist)-[:COLLABORATES_WITH]-()
WITH a, count(*) AS collab_count
ORDER BY collab_count DESC
LIMIT 10
RETURN a.name, collab_count
```

---

### 3. SIMILAR_GENRE (Nghệ sĩ cùng thể loại) 🎵

**Pattern**: `(Artist)-[:SIMILAR_GENRE {similarity: n}]-(Artist)`

**Ý nghĩa**: Hai nghệ sĩ có thể loại âm nhạc tương tự nhau

**Properties**:
- `similarity`: Điểm số tương đồng giữa genres (0.0 - 1.0)

**Đặc điểm**:
- Mối quan hệ **vô hướng** (undirected)
- Có **trọng số** (weighted) - similarity score
- Tự động được tạo khi 2 nghệ sĩ có genres chung

**Tính toán similarity**:
```
similarity = số genres chung / tổng số genres duy nhất của cả 2 nghệ sĩ
```

**Threshold**: Chỉ tạo edge nếu similarity ≥ 0.3

**Ví dụ**:
```cypher
// Tìm nghệ sĩ cùng genre với một nghệ sĩ
MATCH (a1:Artist {name: "Taylor Swift"})-[r:SIMILAR_GENRE]-(a2:Artist)
RETURN a2.name, r.similarity
ORDER BY r.similarity DESC

// Tìm genre communities
MATCH (a:Artist)-[:SIMILAR_GENRE]-(other:Artist)
WHERE a.name = "Ed Sheeran"
RETURN collect(DISTINCT other.name) AS similar_artists

// Top similarity connections
MATCH (a1:Artist)-[r:SIMILAR_GENRE]-(a2:Artist)
WHERE id(a1) < id(a2)
RETURN a1.name, a2.name, r.similarity
ORDER BY r.similarity DESC
LIMIT 10
```

---

## 🎯 Cách Mối Quan Hệ Được Tạo Ra

### Quy Trình Tự Động:

1. **Thu thập dữ liệu**: Scrape Wikipedia để lấy thông tin nghệ sĩ và album
2. **Phân tích infobox**: Parse dữ liệu album từ infobox của mỗi nghệ sĩ
3. **Tạo album map**: Nhóm các nghệ sĩ theo album chung
4. **Tạo quan hệ**:
   ```
   Nếu Album X có [Artist A, Artist B, Artist C]:
   
   → Tạo: (Artist A)-[:PERFORMS_ON]->(Album X)
   → Tạo: (Artist B)-[:PERFORMS_ON]->(Album X)
   → Tạo: (Artist C)-[:PERFORMS_ON]->(Album X)
   
   → Tạo: (Artist A)-[:COLLABORATES_WITH {shared_albums: 1}]-(Artist B)
   → Tạo: (Artist A)-[:COLLABORATES_WITH {shared_albums: 1}]-(Artist C)
   → Tạo: (Artist B)-[:COLLABORATES_WITH {shared_albums: 1}]-(Artist C)
   ```

5. **Cập nhật trọng số**: Nếu 2 nghệ sĩ xuất hiện trên nhiều album, tăng `shared_albums`

6. **Tạo SIMILAR_GENRE edges**:
   ```
   Với mỗi cặp nghệ sĩ:
   - Parse genres của từng nghệ sĩ
   - Tính similarity = số genres chung / tổng genres
   - Nếu similarity ≥ 0.3: Tạo SIMILAR_GENRE edge
   ```

---

## 📈 Use Cases cho Network Analysis

### 1. Phân tích Collaboration Network

```cypher
// Tìm cộng đồng nghệ sĩ hợp tác chặt chẽ
CALL gds.louvain.stream('music-network')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name AS artist, communityId
```

### 2. Tìm Influencers (PageRank)

```cypher
// Dựa trên COLLABORATES_WITH relationships
CALL gds.pageRank.stream({
  nodeProjection: 'Artist',
  relationshipProjection: {
    COLLABORATES_WITH: {
      type: 'COLLABORATES_WITH',
      properties: 'shared_albums',
      orientation: 'UNDIRECTED'
    }
  },
  relationshipWeightProperty: 'shared_albums'
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS artist, score
ORDER BY score DESC
LIMIT 10
```

### 3. Shortest Path giữa 2 nghệ sĩ

```cypher
// Tìm chuỗi hợp tác ngắn nhất
MATCH path = shortestPath(
  (a1:Artist {name: "Artist 1"})-[:COLLABORATES_WITH*]-(a2:Artist {name: "Artist 2"})
)
RETURN path
```

### 4. Degree Centrality

```cypher
// Nghệ sĩ có nhiều kết nối nhất
MATCH (a:Artist)-[:COLLABORATES_WITH]-()
WITH a, count(*) AS degree
ORDER BY degree DESC
LIMIT 10
RETURN a.name, degree
```

---

## 🔍 Ví dụ Queries Thực Tế

### Tìm "cầu nối" giữa các nghệ sĩ

```cypher
// Artists acting as bridges between communities
MATCH (a:Artist)-[:COLLABORATES_WITH]-(other:Artist)
WITH a, collect(DISTINCT other) AS collaborators
WHERE size(collaborators) >= 5
RETURN a.name, size(collaborators) AS bridge_score
ORDER BY bridge_score DESC
```

### Phân tích Genre Collaboration

```cypher
// Xem nghệ sĩ nào hợp tác xuyên genre
MATCH (a1:Artist)-[:COLLABORATES_WITH]-(a2:Artist)
WHERE a1.genres <> a2.genres
RETURN a1.name, a1.genres, a2.name, a2.genres
LIMIT 20
```

### Tìm "Supergroups" (nhóm nghệ sĩ hợp tác chặt chẽ)

```cypher
// Tìm cliques (nhóm nghệ sĩ mà tất cả đều hợp tác với nhau)
MATCH (a:Artist)-[:COLLABORATES_WITH]-(b:Artist)-[:COLLABORATES_WITH]-(c:Artist)
WHERE (a)-[:COLLABORATES_WITH]-(c)
  AND id(a) < id(b) AND id(b) < id(c)
RETURN a.name, b.name, c.name
LIMIT 10
```

---

## 📊 Statistics Được Tính Toán

Từ các mối quan hệ này, project tính toán:

### Basic Network Stats
- ✅ Tổng số nodes (Artist + Album)
- ✅ Tổng số relationships (PERFORMS_ON + COLLABORATES_WITH)
- ✅ Degree trung bình, max, min, median

### Collaboration Stats  
- ✅ Top 10 nghệ sĩ có nhiều collaborations nhất
- ✅ Top 10 cặp nghệ sĩ có nhiều shared albums nhất
- ✅ Tổng số collaboration relationships

### Centrality Metrics
- ✅ PageRank scores (influence trong network)
- ✅ Degree centrality (số lượng connections)

### Genre Analysis
- ✅ Genre distribution
- ✅ Cross-genre collaborations

---

## ✅ Quality Assurance

### Đảm bảo chất lượng mối quan hệ:

1. **Filtering**: Chỉ tạo Album nodes nếu có ≥2 nghệ sĩ (loại bỏ single artist albums)
2. **Deduplication**: Tránh tạo duplicate edges giữa cùng 2 nghệ sĩ
3. **Weight accumulation**: Cộng dồn `shared_albums` nếu 2 nghệ sĩ xuất hiện trên nhiều album
4. **Bidirectional check**: Đảm bảo COLLABORATES_WITH không bị tạo 2 chiều

### Code Implementation:

```python
# In builder.py - tạo collaboration edges
for i, artist1 in enumerate(valid_artist_nodes):
    for artist2 in valid_artist_nodes[i+1:]:
        if not self.graph.has_edge(artist1, artist2):
            # Tạo edge mới
            self.graph.add_edge(
                artist1, artist2,
                relationship='COLLABORATES_WITH',
                shared_albums=1
            )
        else:
            # Tăng weight nếu đã tồn tại
            edge_data = self.graph[artist1][artist2]
            if edge_data.get('relationship') == 'COLLABORATES_WITH':
                edge_data['shared_albums'] += 1
```

---

## 🎨 Visualization

Relationships được visualize trong:

1. **Network Graph**: Shows COLLABORATES_WITH connections
2. **Degree Distribution**: Histogram of collaboration counts
3. **Top Collaborators Chart**: Bar chart of most connected artists

---

## 📝 Summary

**Trước khi cải thiện**:
- ❌ Chỉ có Artist -> Album relationships
- ❌ Phải query phức tạp để tìm collaborations
- ❌ Không có trọng số cho mối quan hệ

**Sau khi cải thiện**:
- ✅ Artist -> Album (PERFORMS_ON)
- ✅ Artist <-> Artist (COLLABORATES_WITH) với trọng số
- ✅ Queries đơn giản và nhanh hơn
- ✅ Phân tích collaboration network chính xác
- ✅ Metrics về collaboration quality

**Kết quả**: Graph network có **chất lượng cao** và **dễ phân tích** hơn! 🎉



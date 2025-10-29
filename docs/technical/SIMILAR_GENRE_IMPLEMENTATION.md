# TRIỂN KHAI SIMILAR_GENRE EDGES

## ✅ ĐÃ HOÀN THÀNH

Dự án đã triển khai thành công loại cạnh **SIMILAR_GENRE** để kết nối các nghệ sĩ có thể loại âm nhạc tương tự nhau.

---

## 📋 CHI TIẾT TRIỂN KHAI

### **File được cập nhật**:

1. ✅ `src/graph_building/builder.py` - Thêm method `create_similar_genre_edges()`
2. ✅ `src/graph_building/builder.py` - Update `export_edges_csv()` 
3. ✅ `src/graph_building/importer.py` - Update `import_relationships()`
4. ✅ `GRAPH_RELATIONSHIPS.md` - Thêm documentation

---

## 🔧 THUẬT TOÁN

### **Method**: `create_similar_genre_edges(similarity_threshold=0.3)`

**Logic**:

```python
1. Lấy tất cả artist nodes
2. Với mỗi cặp nghệ sĩ (i, j):
   a. Parse genres của nghệ sĩ i và j
   b. Tính genres chung = intersection
   c. Tính tổng genres = union
   d. Tính similarity = len(common) / len(all)
   e. Nếu similarity >= threshold:
      - Tạo SIMILAR_GENRE edge với weight = similarity
3. Log số edges đã tạo
```

**Similarity formula**:
```
similarity = số genres chung / tổng số genres duy nhất
```

**Ví dụ**:
- Artist A: `["pop", "dance", "r&b"]`
- Artist B: `["pop", "dance"]`
- Common: `["pop", "dance"]` = 2
- All: `["pop", "dance", "r&b"]` = 3
- Similarity: `2/3 = 0.667`

---

## 📊 OUTPUT EXPECTED

### **Khi build graph**:

```
Building graph network...
Added 1000 artist nodes to graph
Added 500 album nodes
Added 2000 artist-album edges
Added 800 artist-artist collaboration edges
Creating SIMILAR_GENRE edges...
Added 2500 SIMILAR_GENRE edges          ← MỚI!
Graph built successfully:
  - Nodes: 1500
  - Edges: 5300                          ← Tăng từ 2800 lên 5300
```

### **Khi export edges**:

```
Exported 5300 edges to data/processed/edges.csv
  - PERFORMS_ON: 2000
  - COLLABORATES_WITH: 800
  - SIMILAR_GENRE: 2500                  ← MỚI!
```

### **Khi import to Neo4j**:

```
✓ Imported 2000 PERFORMS_ON relationships
✓ Imported 800 COLLABORATES_WITH relationships
✓ Imported 2500 SIMILAR_GENRE relationships  ← MỚI!
✓ Successfully imported 5300 total relationships
```

---

## 🎯 USE CASES

### **1. Genre-based Recommendations**

```cypher
// Tìm nghệ sĩ cùng genre với Taylor Swift
MATCH (ts:Artist {name: "Taylor Swift"})-[r:SIMILAR_GENRE]-(other:Artist)
RETURN other.name, r.similarity
ORDER BY r.similarity DESC
LIMIT 10
```

### **2. Genre Communities**

```cypher
// Tìm nhóm nghệ sĩ pop
MATCH (a:Artist)-[:SIMILAR_GENRE]-(b:Artist)
WHERE a.genres CONTAINS 'pop'
RETURN collect(DISTINCT a.name) AS pop_artists
```

### **3. Similarity Analysis**

```cypher
// Nghệ sĩ có nhiều connections về genre nhất
MATCH (a:Artist)-[:SIMILAR_GENRE]-()
WITH a, count(*) AS genre_connections
ORDER BY genre_connections DESC
LIMIT 10
RETURN a.name, genre_connections
```

### **4. Cross-Genre Exploration**

```cypher
// Tìm nghệ sĩ bridge giữa 2 genres
MATCH (a:Artist)-[:SIMILAR_GENRE]-(bridge)-[:SIMILAR_GENRE]-(b:Artist)
WHERE a.genres CONTAINS 'pop' AND b.genres CONTAINS 'rock'
RETURN DISTINCT bridge.name AS genre_bridge
```

---

## ✅ ĐẢM BẢO CHẤT LƯỢNG

### **Filters**:

1. **Threshold**: Chỉ tạo edge nếu similarity ≥ 0.3
2. **Avoid duplicates**: Kiểm tra edge đã tồn tại
3. **Case insensitive**: Lowercase để so sánh
4. **Empty genres**: Skip artists không có genres

### **Performance**:

- O(n²) cho n artists
- Optimized: Chỉ check một nửa pairs (i, j với i < j)
- Threshold giảm số edges để tránh quá nhiều connections

---

## 📝 TỔNG KẾT

**Trước khi thêm SIMILAR_GENRE**:
- 2 loại edges: PERFORMS_ON, COLLABORATES_WITH
- Focus vào collaborations qua albums

**Sau khi thêm SIMILAR_GENRE**:
- 3 loại edges: PERFORMS_ON, COLLABORATES_WITH, SIMILAR_GENRE
- Network đa dạng hơn với genre-based connections
- Hữu ích cho recommendation và community detection

**Lợi ích**:
- ✅ Network phong phú hơn
- ✅ Genre analysis dễ dàng
- ✅ Recommendation system tốt hơn
- ✅ Community detection chính xác hơn

---

## 🚀 SỬ DỤNG

Chạy pipeline như bình thường:

```bash
./run.sh build
./run.sh import
```

SIMILAR_GENRE edges sẽ được tạo tự động!


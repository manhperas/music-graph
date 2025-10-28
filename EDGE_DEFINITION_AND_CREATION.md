# MÔ TẢ ĐỊNH NGHĨA VÀ TẠO CẠNH (EDGES/RELATIONSHIPS)

## ✅ ĐÃ CÓ ĐẦY ĐỦ

Dự án đã có đầy đủ định nghĩa và code để tạo các cạnh (edges/relationships) trong graph network.

---

## 📋 CÁC LOẠI CẠNH ĐÃ ĐỊNH NGHĨA

### **1. PERFORMS_ON - Nghệ sĩ biểu diễn trên Album**

**Pattern**: `(Artist)-[:PERFORMS_ON]->(Album)`

**Ý nghĩa**: Nghệ sĩ đã phát hành hoặc biểu diễn trên một album

**Đặc điểm**:
- Có hướng (directed): Artist → Album
- Không có trọng số
- Mỗi nghệ sĩ trên album tạo một cạnh đến album đó

**Ví dụ**:
- Taylor Swift → Album "1989"
- Ed Sheeran → Album "÷"

---

### **2. COLLABORATES_WITH - Nghệ sĩ hợp tác với nghệ sĩ**

**Pattern**: `(Artist)-[:COLLABORATES_WITH {shared_albums: n}]-(Artist)`

**Ý nghĩa**: Hai nghệ sĩ đã hợp tác với nhau (cùng xuất hiện trên ít nhất một album)

**Đặc điểm**:
- Vô hướng (undirected): Artist ↔ Artist
- Có trọng số (weighted): `shared_albums` - số lượng album chung
- Tự động được tạo khi 2 nghệ sĩ cùng có PERFORMS_ON một album
- Trọng số được tăng khi nghệ sĩ xuất hiện trên nhiều album chung

**Ví dụ**:
- Taylor Swift -[:COLLABORATES_WITH {shared_albums: 2}]- Kendrick Lamar
- Ed Sheeran -[:COLLABORATES_WITH {shared_albums: 1}]- Bruno Mars

---

## 🔧 CODE TẠO CẠNH

### **File**: `src/graph_building/builder.py`

### **1. Tạo cạnh PERFORMS_ON**

```python
# Trong method add_album_nodes_and_edges()
for artist_id in artist_ids:
    artist_node_id = self.artist_nodes.get(artist_id)
    if artist_node_id:
        self.graph.add_edge(
            artist_node_id,
            album_id,
            relationship='PERFORMS_ON'
        )
        edges_added += 1
```

**Logic**:
- Với mỗi album trong album_map
- Nếu album có ≥2 nghệ sĩ: tạo album node
- Với mỗi nghệ sĩ trong album: tạo cạnh Artist → Album
- Đếm số cạnh đã tạo

---

### **2. Tạo cạnh COLLABORATES_WITH**

```python
# Trong method add_album_nodes_and_edges()
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
```

**Logic**:
- Với mỗi album có nhiều nghệ sĩ
- Tạo cạnh giữa tất cả các cặp nghệ sĩ
- Nếu cạnh đã tồn tại: tăng trọng số `shared_albums`
- Nếu cạnh chưa tồn tại: tạo mới với `shared_albums=1`

---

## 📊 QUY TRÌNH TẠO CẠNH

### **Quy trình tổng thể**:

```
1. Load Data
   ├─ Load nodes.csv (artist nodes)
   └─ Load albums.json (album mapping)

2. Add Artist Nodes
   └─ Create artist nodes với attributes

3. Add Album Nodes và Edges
   ├─ Filter: Chỉ tạo album node nếu ≥2 artists
   ├─ Create Album Node
   ├─ Create PERFORMS_ON edges (Artist → Album)
   └─ Create COLLABORATES_WITH edges (Artist ↔ Artist)

4. Export Edges CSV
   └─ Format: from, to, type, weight

5. Import to Neo4j
   ├─ Import PERFORMS_ON
   └─ Import COLLABORATES_WITH
```

---

## 📝 CHI TIẾT TẠO CẠNH

### **Ví dụ cụ thể**:

**Input**: Album "1989" có nghệ sĩ [Taylor Swift, Kendrick Lamar, Imogen Heap]

**Bước 1**: Tạo album node
```python
graph.add_node(
    "album_0",
    node_type='Album',
    title="1989"
)
```

**Bước 2**: Tạo PERFORMS_ON edges
```python
graph.add_edge("artist_0", "album_0", relationship='PERFORMS_ON')  # Taylor Swift
graph.add_edge("artist_1", "album_0", relationship='PERFORMS_ON')  # Kendrick Lamar
graph.add_edge("artist_2", "album_0", relationship='PERFORMS_ON')  # Imogen Heap
```

**Bước 3**: Tạo COLLABORATES_WITH edges
```python
graph.add_edge("artist_0", "artist_1", relationship='COLLABORATES_WITH', shared_albums=1)  # Taylor ↔ Kendrick
graph.add_edge("artist_0", "artist_2", relationship='COLLABORATES_WITH', shared_albums=1)  # Taylor ↔ Imogen
graph.add_edge("artist_1", "artist_2", relationship='COLLABORATES_WITH', shared_albums=1)  # Kendrick ↔ Imogen
```

**Nếu 2 nghệ sĩ xuất hiện trên nhiều album**: Trọng số tự động tăng
```python
# Album thứ 2 có Taylor + Kendrick
# Edge đã tồn tại → Tăng shared_albums
edge_data['shared_albums'] = 1 + 1 = 2
```

---

## 📤 EXPORT EDGES

### **File**: `src/graph_building/builder.py` - Method `export_edges_csv()`

```python
for u, v, data in self.graph.edges(data=True):
    edge_record = {
        'from': u,
        'to': v,
        'type': data.get('relationship', 'PERFORMS_ON')
    }
    
    # Add shared_albums count for collaboration edges
    if data.get('relationship') == 'COLLABORATES_WITH':
        edge_record['weight'] = data.get('shared_albums', 1)
    else:
        edge_record['weight'] = 1
        
    edges_data.append(edge_record)
```

**Output**: File `data/processed/edges.csv`
```csv
from,to,type,weight
artist_0,album_0,PERFORMS_ON,1
artist_1,album_0,PERFORMS_ON,1
artist_0,artist_1,COLLABORATES_WITH,2
```

---

## 🔗 IMPORT VÀO NEO4J

### **File**: `src/graph_building/importer.py` - Method `import_relationships()`

**Bước 1**: Tách edges theo type
```python
performs_on_edges = [e for e in edges if e.get('type') == 'PERFORMS_ON']
collaborates_edges = [e for e in edges if e.get('type') == 'COLLABORATES_WITH']
```

**Bước 2**: Import PERFORMS_ON
```cypher
UNWIND $edges AS edge
MATCH (from {id: edge.from})
MATCH (to {id: edge.to})
CREATE (from)-[:PERFORMS_ON]->(to)
```

**Bước 3**: Import COLLABORATES_WITH
```cypher
UNWIND $edges AS edge
MATCH (from:Artist {id: edge.from})
MATCH (to:Artist {id: edge.to})
CREATE (from)-[:COLLABORATES_WITH {shared_albums: edge.weight}]->(to)
```

---

## ✅ ĐẢM BẢO CHẤT LƯỢNG

### **Kiểm tra và filter**:

1. **Filter albums**: Chỉ tạo album node nếu ≥2 artists
   ```python
   if len(artist_ids) < 2:
       continue
   ```

2. **Avoid duplicates**: Kiểm tra edge đã tồn tại
   ```python
   if not self.graph.has_edge(artist1, artist2):
       # Create new edge
   ```

3. **Accumulate weights**: Tăng shared_albums khi cần
   ```python
   edge_data['shared_albums'] = edge_data.get('shared_albums', 0) + 1
   ```

4. **Bidirectional**: COLLABORATES_WITH là undirected
   ```python
   # Query từ cả 2 hướng đều hợp lệ
   (a1)-[:COLLABORATES_WITH]-(a2)
   ```

---

## 📊 THỐNG KÊ CẠNH

### **Log output khi build graph**:

```
Building graph network...
Added 1000 artist nodes to graph
Added 500 album nodes
Added 2000 artist-album edges
Added 800 artist-artist collaboration edges

Graph built successfully:
  - Nodes: 1500
  - Edges: 2800
```

### **Log output khi export**:

```
Exported 2800 edges to data/processed/edges.csv
  - PERFORMS_ON: 2000
  - COLLABORATES_WITH: 800
```

---

## 📖 MÔ TẢ CHO BÀI TẬP

### **Định nghĩa và tạo cạnh**:

Dự án đã định nghĩa hai loại cạnh (edges/relationships) chính để mô hình hóa mạng lưới hợp tác giữa các nghệ sĩ:

**Loại 1 - PERFORMS_ON**: Đây là cạnh có hướng từ nghệ sĩ đến album, biểu thị việc nghệ sĩ đã phát hành hoặc biểu diễn trên album đó. Cạnh này không có trọng số và được tạo tự động khi hệ thống parse thông tin album từ infobox của nghệ sĩ.

**Loại 2 - COLLABORATES_WITH**: Đây là cạnh vô hướng giữa hai nghệ sĩ, biểu thị mối quan hệ hợp tác giữa họ. Cạnh này có trọng số `shared_albums` thể hiện số lượng album mà hai nghệ sĩ cùng tham gia. Cạnh này được tạo tự động khi hai nghệ sĩ cùng xuất hiện trên ít nhất một album.

Thuật toán tạo cạnh hoạt động như sau: Khi một album có nhiều nghệ sĩ (≥2), hệ thống sẽ tạo các cạnh PERFORMS_ON từ mỗi nghệ sĩ đến album đó. Sau đó, hệ thống tạo các cạnh COLLABORATES_WITH giữa tất cả các cặp nghệ sĩ trong album. Nếu hai nghệ sĩ đã có cạnh collaboration trước đó, hệ thống sẽ tăng trọng số `shared_albums` thay vì tạo cạnh trùng lặp.

Các cạnh được export ra file CSV với format chuẩn gồm các trường: from, to, type, và weight. File này sau đó được import vào Neo4j graph database với hai câu lệnh CREATE riêng biệt cho từng loại cạnh, đảm bảo các properties và types được thiết lập đúng.

---

## ✅ KẾT LUẬN

**Đã có**: Định nghĩa đầy đủ 2 loại cạnh và code tạo cạnh  
**Code**: Trong builder.py và importer.py  
**Logic**: Tự động tạo từ album data  
**Quality**: Có kiểm tra và filter để đảm bảo chất lượng  

**Kết quả**: Graph network hoàn chỉnh với PERFORMS_ON và COLLABORATES_WITH relationships!


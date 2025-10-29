# Enhanced Duplicate Filtering and Shortest Path Analysis

## 📋 Tổng Quan

Dự án đã được cải thiện với hai tính năng quan trọng:
1. **Enhanced Duplicate Filtering**: Lọc và normalize dữ liệu để tránh duplicate artists tốt hơn
2. **Shortest Path Analysis**: Phân tích đường đi ngắn nhất giữa các nghệ sĩ trong mạng

---

## 1. ✨ Enhanced Duplicate Filtering

### Vấn Đề Trước Đây

- Chỉ dựa vào exact match (`drop_duplicates(subset=['name'])`)
- Không xử lý được các trường hợp:
  - "Artist Name" vs "ArtistName" (whitespace khác nhau)
  - "Artist" vs "Artist (band)" (suffix khác nhau)
  - "Ártist" vs "Artist" (accents khác nhau)
  - Case variations

### Giải Pháp Mới

Đã thêm phương thức `create_similarity_key()` trong `src/data_processing/cleaner.py`:

```python
def create_similarity_key(self, name: str) -> str:
    """Create a normalized key for duplicate detection"""
    # Remove accents and special characters
    normalized = unidecode(name.lower())
    
    # Remove common suffixes that don't affect uniqueness
    suffixes = [
        r'\s*\(band\)', r'\s*\(singer\)', r'\s*\(artist\)',
        r'\s*\(musician\)', r'\s*\(group\)', r'\s*\(solo\)',
        r'\s*\(vocalist\)', r'\s*\(vocal\)'
    ]
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized)
    
    # Remove special characters except spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Normalize whitespace
    normalized = " ".join(normalized.split())
    
    return normalized
```

### Quy Trình Lọc Mới

1. **Normalize names**: Clean whitespace và formatting
2. **Create similarity keys**: Tạo key để phát hiện duplicates thông minh
3. **Remove exact duplicates**: Loại bỏ exact matches
4. **Remove similarity duplicates**: Loại bỏ các trường hợp tương tự
5. **Log statistics**: Hiển thị số lượng duplicates đã loại bỏ

### Ví Dụ

```
Original data:
- "Michael Jackson"
- "Michael Jackson (singer)"
- "michael jackson"
- "Michael  Jackson" (extra space)

After filtering:
- "Michael Jackson" (kept first occurrence)
```

### Kết Quả

- Loại bỏ được nhiều duplicates hơn (exact + similarity-based)
- Giữ lại data chất lượng cao
- Log chi tiết về quá trình filtering

---

## 2. 🔍 Shortest Path Analysis

### Module Mới: `src/analysis/paths.py`

Đã tạo module mới để phân tích shortest paths giữa các nghệ sĩ trong mạng.

### Các Tính Năng

#### 1. `find_shortest_path(graph, artist1, artist2)`
Tìm đường đi ngắn nhất giữa hai nghệ sĩ.

**Returns:**
```json
{
  "artist1": "Artist A",
  "artist2": "Artist B",
  "path_exists": true,
  "path_length": 3,
  "path": [
    {"name": "Artist A", "node_id": "artist_1"},
    {"name": "Album X", "node_id": "album_5", "type": "Album"},
    {"name": "Artist B", "node_id": "artist_2"}
  ],
  "path_size": 3
}
```

#### 2. `find_all_shortest_paths(graph, artist1, artist2)`
Tìm tất cả các đường đi ngắn nhất giữa hai nghệ sĩ.

#### 3. `get_artist_shortest_paths_summary(graph, limit=20)`
Phân tích mẫu các cặp nghệ sĩ để tính toán thống kê về path lengths.

**Returns:**
```json
{
  "num_pairs_analyzed": 20,
  "num_paths_found": 18,
  "avg_path_length": 2.5,
  "min_path_length": 1,
  "max_path_length": 4,
  "median_path_length": 2.0,
  "examples": [...]
}
```

#### 4. `compute_average_path_length(graph)`
Tính toán average shortest path length cho toàn bộ network.

#### 5. `compute_diameter_and_radius(graph)`
Tính toán diameter và radius của network.

**Returns:**
```json
{
  "diameter": 6,
  "radius": 3,
  "component_size": 1500
}
```

### Usage

```python
from analysis.paths import PathAnalyzer, analyze_paths

# Option 1: Run full analysis
results = analyze_paths()

# Option 2: Use class directly
analyzer = PathAnalyzer()
graph = analyzer.load_graph_from_file("data/processed/network.graphml")

# Find shortest path between two artists
path = analyzer.find_shortest_path(graph, "Michael Jackson", "Beyoncé")

# Get average path length
avg_length = analyzer.compute_average_path_length(graph)

# Get diameter and radius
stats = analyzer.compute_diameter_and_radius(graph)
```

### Command Line

```bash
python run_path_analysis.py
```

Output:
```
============================================================
SHORTEST PATH ANALYSIS
============================================================
Average Shortest Path Length: 2.45
Network Diameter: 6
Network Radius: 3
Largest Component Size: 1500

Sample Path Analysis:
  Pairs analyzed: 20
  Paths found: 18
  Average path length: 2.5
  Min/Max path length: 1/4
============================================================
```

---

## 📊 Kết Quả Phân Tích

### Duplicate Filtering Results

- **Before**: Basic exact matching
- **After**: Advanced similarity-based filtering
- **Improvement**: Có thể detect và loại bỏ nhiều duplicates hơn

### Path Analysis Results

File `data/processed/path_analysis.json` chứa:
- Average shortest path length
- Network diameter và radius
- Sample path analysis với examples
- Statistics về path lengths

### Metrics

Các metrics mới được tính toán:
1. **Average Path Length**: Độ dài trung bình của đường đi ngắn nhất
2. **Diameter**: Đường đi dài nhất giữa hai nodes bất kỳ
3. **Radius**: Đường đi ngắn nhất từ center đến node xa nhất
4. **Path Distribution**: Phân bố độ dài đường đi

---

## 🔧 Implementation Details

### Files Modified

1. **src/data_processing/cleaner.py**
   - Added `create_similarity_key()` method
   - Enhanced `clean_dataframe()` to use similarity-based filtering
   - Added logging for duplicate removal statistics

### Files Created

1. **src/analysis/paths.py**
   - New `PathAnalyzer` class
   - Methods for path finding and analysis
   - Integration with Neo4j and NetworkX

2. **run_path_analysis.py**
   - Command-line script to run path analysis
   - Displays summary statistics

3. **src/analysis/__init__.py**
   - Updated to export `PathAnalyzer` and `analyze_paths`

---

## 📈 Use Cases

### 1. Find Connection Between Artists

```python
analyzer = PathAnalyzer()
graph = analyzer.load_graph_from_file()

# Find how Artist A connects to Artist B
path = analyzer.find_shortest_path(graph, "Ariana Grande", "Taylor Swift")
print(f"Path length: {path['path_length']}")
print(f"Path: {' -> '.join([p['name'] for p in path['path']])}")
```

### 2. Network Characteristics

```python
# Get network diameter (longest shortest path)
stats = analyzer.compute_diameter_and_radius(graph)
print(f"Network diameter: {stats['diameter']}")
print(f"Number of hops between furthest artists: {stats['diameter']}")
```

### 3. Small-World Analysis

```python
# Check if network exhibits small-world properties
avg_path = analyzer.compute_average_path_length(graph)
print(f"Average path length: {avg_path}")
print(f"Is small-world: {avg_path < 6}")  # Typically small-world if < 6
```

---

## 🎯 Kết Luận

### Achievements

✅ **Enhanced Duplicate Filtering**
- Loại bỏ duplicates tốt hơn với similarity-based matching
- Xử lý accents, whitespace, và suffixes
- Giữ lại data chất lượng cao

✅ **Shortest Path Analysis**
- Module phân tích paths hoàn chỉnh
- Tính toán network metrics quan trọng
- Hỗ trợ tìm kiếm connections giữa artists
- Command-line interface để chạy analysis

### Benefits

1. **Data Quality**: Ít duplicates hơn, data sạch hơn
2. **Network Insights**: Hiểu rõ hơn về structure của network
3. **Research**: Hỗ trợ phân tích các mối quan hệ trong network
4. **Visualization**: Có thể visualize paths và connections

### Next Steps

Có thể mở rộng thêm:
- Visualize shortest paths giữa artists
- Find most central artists (closeness centrality)
- Detect bridges và articulation points
- Analyze path diversity

---

*Documentation created: 2024*
*Project: Music Network Pop US-UK*


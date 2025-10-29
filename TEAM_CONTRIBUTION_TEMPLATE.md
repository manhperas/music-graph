# Phân công công việc trong nhóm

## 👥 Thành viên nhóm

**Dự án**: Music Network Pop US-UK Analysis

**Nhóm**: [Tên nhóm]  
**Môn học**: [Tên môn học]  
**Giảng viên**: [Tên giảng viên]

---

## 📋 Phân công công việc

| Thành viên | MSSV | Vai trò | Công việc chính | Mô tả chi tiết |
|------------|------|---------|-----------------|----------------|
| [Tên] | [MSSV] | Data Collection | Thu thập dữ liệu từ Wikipedia | Scrape Wikipedia pages, extract infobox data, implement snowball sampling |
| [Tên] | [MSSV] | Data Processing | Xử lý và làm sạch dữ liệu | Parse wikitext, clean data, filter artists, extract albums |
| [Tên] | [MSSV] | Graph Building | Xây dựng network và import Neo4j | Create nodes, edges, implement graph algorithms, import to Neo4j |
| [Tên] | [MSSV] | Analysis & Visualization | Phân tích và visualization | Network statistics, community detection, create visualizations |

---

## 📊 Chi tiết phân công

### 1. Data Collection (Thu thập dữ liệu)
**Người phụ trách**: [Tên thành viên]  
**Thời gian**: [Bắt đầu] - [Kết thúc]

**Công việc**:
- ✓ Cài đặt Wikipedia API và các thư viện cần thiết
- ✓ Implement snowball sampling algorithm
- ✓ Extract artists từ Wikipedia categories
- ✓ Extract albums từ artist infobox
- ✓ Thu thập ~1000 artists

**Files liên quan**:
- `src/data_collection/scraper.py`
- `config/wikipedia_config.json`
- `config/seed_artists.json`

---

### 2. Data Processing (Xử lý dữ liệu)
**Người phụ trách**: [Tên thành viên]  
**Thời gian**: [Bắt đầu] - [Kết thúc]

**Công việc**:
- ✓ Parse infobox wikitext
- ✓ Clean và normalize artist data
- ✓ Filter pop-related artists
- ✓ Extract và normalize albums
- ✓ Deduplication

**Files liên quan**:
- `src/data_processing/parser.py`
- `src/data_processing/cleaner.py`

---

### 3. Graph Building (Xây dựng network)
**Người phụ trách**: [Tên thành viên]  
**Thời gian**: [Bắt đầu] - [Kết thúc]

**Công việc**:
- ✓ Create Artist nodes
- ✓ Create Album nodes
- ✓ Create PERFORMS_ON edges
- ✓ Create COLLABORATES_WITH edges
- ✓ Create SIMILAR_GENRE edges
- ✓ Export CSV files cho Neo4j
- ✓ Import vào Neo4j database

**Files liên quan**:
- `src/graph_building/builder.py`
- `src/graph_building/importer.py`

---

### 4. Analysis & Visualization (Phân tích và visualization)
**Người phụ trách**: [Tên thành viên]  
**Thời gian**: [Bắt đầu] - [Kết thúc]

**Công việc**:
- ✓ Compute network statistics
- ✓ Implement community detection (Louvain)
- ✓ Calculate centrality metrics (PageRank, degree)
- ✓ Analyze collaborations
- ✓ Create visualizations (degree distribution, network sample, genre distribution)
- ✓ Write documentation

**Files liên quan**:
- `src/analysis/stats.py`
- `src/analysis/communities.py`
- `src/analysis/viz.py`

---

## 🎯 Tổng hợp công việc

### Thời gian tổng thể
- **Bắt đầu**: [Ngày]
- **Kết thúc**: [Ngày]
- **Tổng thời gian**: [X tuần/tháng]

### Công nghệ sử dụng
- Python 3.10+
- Wikipedia API
- NetworkX
- Neo4j
- Matplotlib

### Kết quả đạt được
- ✓ Thu thập 1000+ artists
- ✓ Xây dựng network với 1500+ nodes
- ✓ Tạo 5300+ edges
- ✓ Phân tích communities với Louvain
- ✓ Tạo 8+ visualizations

---

## 📝 Ghi chú

### Khó khăn gặp phải
1. Wikipedia data không đồng nhất về format
2. Parsing wikitext phức tạp
3. Xử lý collaborations từ albums

### Giải pháp
1. Implement robust parsing với error handling
2. Sử dụng mwparserfromhell
3. Tạo edges từ albums shared giữa artists

---

**Ngày hoàn thành**: [Ngày]  
**Người tổng hợp**: [Tên]


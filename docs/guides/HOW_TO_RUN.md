# HƯỚNG DẪN CHẠY DỰ ÁN

## 🎯 TỔNG QUAN

Dự án có **5 stages** chạy tuần tự để tạo collaboration network từ Wikipedia và phân tích trong Neo4j.

---

## 📋 CÁC STAGES VÀ MỤC TIÊU

### **STAGE 1: Collect (Thu thập dữ liệu)**

**Command**:
```bash
# Với run.sh
./run.sh collect

# Với uv
uv run python src/main.py collect
```

**Mục tiêu**:
- ✅ Scrape Wikipedia Vietnamese để lấy thông tin nghệ sĩ
- ✅ Load seed artists từ `config/seed_artists.json`
- ✅ Thu thập từ categories Wikipedia
- ✅ Extract albums từ infobox

**Input**: 
- `config/wikipedia_config.json`
- `config/seed_artists.json`

**Output**: 
- `data/raw/artists.json` (~1000 artists)

**Thời gian**: 15-30 phút

---

### **STAGE 2: Process (Xử lý dữ liệu)**

**Command**:
```bash
./run.sh process
# hoặc
uv run python src/main.py process
```

**Mục tiêu**:
- ✅ Parse infobox data (genres, instruments, albums)
- ✅ Clean và normalize dữ liệu
- ✅ Filter pop-related artists
- ✅ Tạo nodes.csv và albums.json

**Input**: 
- `data/raw/artists.json`

**Output**: 
- `data/processed/parsed_artists.json`
- `data/processed/nodes.csv` (clean artist data)
- `data/processed/albums.json` (album mapping)

**Thời gian**: 2-3 phút

---

### **STAGE 3: Build (Xây dựng network)**

**Command**:
```bash
./run.sh build
# hoặc
uv run python src/main.py build
```

**Mục tiêu**:
- ✅ Tạo Artist nodes và Album nodes
- ✅ Tạo PERFORMS_ON edges (Artist → Album)
- ✅ Tạo COLLABORATES_WITH edges (Artist ↔ Artist)
- ✅ Tạo SIMILAR_GENRE edges (Artist ↔ Artist)
- ✅ Export CSV files cho Neo4j
- ✅ Save GraphML file

**Input**: 
- `data/processed/nodes.csv`
- `data/processed/albums.json`

**Output**: 
- `data/processed/artists.csv`
- `data/processed/albums.csv`
- `data/processed/edges.csv`
- `data/processed/network.graphml`

**Thời gian**: 1-2 phút

**Kết quả**:
```
✓ Added 1000 artist nodes
✓ Added 500 album nodes
✓ Added 2000 PERFORMS_ON edges
✓ Added 800 COLLABORATES_WITH edges
✓ Added 2500 SIMILAR_GENRE edges
Total: 1500 nodes, 5300 edges
```

---

### **STAGE 4: Import (Import vào Neo4j)**

**Command**:
```bash
./run.sh import
# hoặc
uv run python src/main.py import
```

**Mục tiêu**:
- ✅ Connect đến Neo4j database
- ✅ Clear database (optional)
- ✅ Create constraints và indexes
- ✅ Import Artist nodes
- ✅ Import Album nodes
- ✅ Import Relationships (PERFORMS_ON, COLLABORATES_WITH, SIMILAR_GENRE)
- ✅ Verify import

**Input**: 
- `data/processed/artists.csv`
- `data/processed/albums.csv`
- `data/processed/edges.csv`
- `config/neo4j_config.json`
- `.env` (password)

**Output**: 
- Graph trong Neo4j database

**Thời gian**: 2-3 phút

**Prerequisites**:
- ✅ Neo4j đang chạy
- ✅ Correct password trong `.env`

---

### **STAGE 5: Analyze (Phân tích và visualize)**

**Command**:
```bash
./run.sh analyze
# hoặc
uv run python src/main.py analyze
```

**Mục tiêu**:
- ✅ Query Neo4j để tính statistics
- ✅ Compute degree statistics
- ✅ Calculate PageRank
- ✅ Find top collaborators
- ✅ Genre distribution analysis
- ✅ Generate visualizations

**Input**: 
- Neo4j database
- `data/processed/network.graphml`

**Output**: 
- `data/processed/stats.json`
- `data/processed/figures/degree_distribution.png`
- `data/processed/figures/network_sample.png`
- `data/processed/figures/genre_distribution.png`
- `data/processed/figures/top_artists.png`
- `data/processed/figures/pagerank.png`

**Thời gian**: 3-5 phút

**Console output**:
```
NETWORK SUMMARY
==========================================

Nodes:
  • Artist: 1000
  • Album: 500

Relationships:
  • PERFORMS_ON: 2000
  • COLLABORATES_WITH: 800
  • SIMILAR_GENRE: 2500

Top 5 Connected Artists:
  1. Taylor Swift: 45 connections
  2. Ed Sheeran: 38 connections
  ...

Top 5 Collaborating Artists:
  1. Artist A: 15 collaborations (23 shared albums)
  ...
```

---

## 🚀 CHẠY ĐẦY ĐỦ PIPELINE

### **Option 1: Tất cả cùng lúc**

```bash
# Với run.sh
./run.sh all

# Với uv
uv run python src/main.py all
```

**Thời gian**: ~30-60 phút

**Chạy tuần tự**:
1. Collect data từ Wikipedia
2. Process và clean data
3. Build graph network
4. Import vào Neo4j
5. Analyze và visualize

---

### **Option 2: Từng stage riêng**

```bash
# Stage 1: Collect
uv run python src/main.py collect

# Stage 2: Process
uv run python src/main.py process

# Stage 3: Build
uv run python src/main.py build

# Stage 4: Import
uv run python src/main.py import

# Stage 5: Analyze
uv run python src/main.py analyze
```

**Ưu điểm**: Có thể dừng ở bất kỳ stage nào để debug

---

## 📊 WORKFLOW COMPLETE

```
1. Collect
   ↓ Wikipedia scraping
   ↓ data/raw/artists.json (1000 artists)

2. Process
   ↓ Parse infoboxes
   ↓ Clean data
   ↓ data/processed/nodes.csv, albums.json

3. Build
   ↓ Create graph với NetworkX
   ↓ Add nodes & edges
   ↓ Export CSV files
   ↓ data/processed/artists.csv, albums.csv, edges.csv

4. Import
   ↓ Connect to Neo4j
   ↓ Import nodes
   ↓ Import relationships
   ↓ Neo4j database filled

5. Analyze
   ↓ Query Neo4j
   ↓ Compute statistics
   ↓ Generate visualizations
   ↓ data/processed/stats.json, figures/*.png
```

---

## 🎯 KẾT QUẢ CUỐI CÙNG

### **Trong Neo4j**:
- ~1000 Artist nodes
- ~500 Album nodes
- ~2000 PERFORMS_ON relationships
- ~800 COLLABORATES_WITH relationships
- ~2500 SIMILAR_GENRE relationships

### **Files Generated**:
- `data/processed/stats.json` - Statistics
- `data/processed/figures/*.png` - 5 visualizations
- `data/processed/network.graphml` - NetworkX graph file

### **Neo4j Browser**:
- Access: http://localhost:7474
- Query và visualize network
- Explore relationships

---

## ⚡ QUICK START

### **Lần đầu chạy** (đầy đủ):

```bash
# 1. Ensure Neo4j running
sudo systemctl status neo4j

# 2. Update .env với password
nano .env
# Set: NEO4J_PASS=your_password

# 3. Chạy tất cả
uv run python src/main.py all
```

### **Chạy lại** (đã có data):

```bash
# Nếu đã có data raw
uv run python src/main.py process
uv run python src/main.py build
uv run python src/main.py import
uv run python src/main.py analyze
```

### **Chỉ import lại** (đã build rồi):

```bash
uv run python src/main.py import
uv run python src/main.py analyze
```

---

## 🔧 OPTIONS

### **Import với custom config**:

```bash
uv run python src/main.py import --config config/neo4j_config.json
```

### **Import không clear database**:

```bash
uv run python src/main.py import --no-clear
```

### **Analyze với custom config**:

```bash
uv run python src/main.py analyze --config config/neo4j_config.json
```

---

## ⏱️ TIME ESTIMATES

| Stage | Thời gian | Phụ thuộc |
|-------|-----------|-----------|
| Collect | 15-30 phút | Wikipedia response |
| Process | 2-3 phút | Data size |
| Build | 1-2 phút | Network size |
| Import | 2-3 phút | Neo4j performance |
| Analyze | 3-5 phút | Neo4j queries |
| **Total** | **30-60 phút** | |

---

## 🎓 TÓM TẮT

**Để chạy dự án**:

```bash
# Cách đơn giản nhất
uv run python src/main.py all

# Hoặc từng bước
uv run python src/main.py collect
uv run python src/main.py process
uv run python src/main.py build
uv run python src/main.py import
uv run python src/main.py analyze
```

**Mỗi stage đạt được**:
1. **Collect**: Thu thập 1000 artists từ Wikipedia
2. **Process**: Parse và clean data
3. **Build**: Tạo graph với 1500 nodes, 5300 edges
4. **Import**: Import vào Neo4j database
5. **Analyze**: Statistics và visualizations

**Result**: Complete collaboration network trong Neo4j! 🎵



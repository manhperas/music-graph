# 📋 TASK 3.7: TEST VÀ VALIDATE - HOÀN THÀNH

## ✅ TỔNG QUAN

**Task**: Test và Validate Phase 3 (Songs + PART_OF Relationships)  
**Status**: ✅ Hoàn thành  
**Date**: 2024-10-30

## 📝 ĐÃ HOÀN THÀNH

### 1. Validation Script Created ✅

File: `test_phase3_validation.py`

Script validation tự động hóa toàn bộ quy trình kiểm tra Phase 3, bao gồm:

#### **Step 1: Extract Songs from Albums**
- Kiểm tra `songs.json` có tồn tại không
- Nếu chưa có, tự động extract songs từ album pages
- Verify số lượng songs được extract

#### **Step 2: Create songs.csv**
- Tạo `songs.csv` từ `songs.json`
- Map songs với album_id (chỉ albums có 2+ artists)
- Validate columns và data quality
- Statistics: songs with duration, track_number, featured artists

#### **Step 3: Build Graph and Verify Song Nodes**
- Build graph với songs
- Verify Song nodes được tạo trong graph
- Verify PART_OF edges (Song → Album)
- Verify PERFORMS_ON edges (Artist/Band → Song)
- Show sample edges

#### **Step 4: Check Success Criteria**
- Tính toán % albums có songs
- Verify đạt ≥40% threshold
- Report statistics

#### **Step 5: Test Neo4j Import**
- Check Neo4j connection
- Import data vào Neo4j
- Verify import thành công

#### **Step 6: Verify with Cypher Queries**
- 11 Cypher queries để verify data:
  1. Count Song nodes
  2. Count PART_OF relationships
  3. Count PERFORMS_ON relationships (Artist → Song)
  4. Sample Song nodes
  5. Songs with track numbers
  6. Albums with most songs
  7. Artists with most songs
  8. Songs with featured artists
  9. Percentage of albums with songs
  10. Sample PART_OF relationships
  11. Sample PERFORMS_ON relationships (Artist → Song)

## 🚀 CÁCH SỬ DỤNG

### Chạy Validation Script

```bash
# Option 1: Using uv
uv run python test_phase3_validation.py

# Option 2: Using python directly (nếu đã install dependencies)
python test_phase3_validation.py

# Option 3: Make executable và chạy trực tiếp
chmod +x test_phase3_validation.py
./test_phase3_validation.py
```

### ⚠️ QUAN TRỌNG: Script KHÔNG scrape lại raw data!

**Script này chỉ làm việc với data đã processed sẵn:**
- ✅ `albums.json` - đã có sẵn (từ `src/main.py process`)
- ✅ `nodes.csv` - đã có sẵn (từ `src/main.py process`)
- ✅ `songs.json` - sẽ extract nếu chưa có (từ `albums.json`, không scrape Wikipedia)

**Logic:**
1. Nếu `songs.json` đã tồn tại → **SKIP extraction** (dùng file hiện có)
2. Nếu `songs.json` chưa có → Extract songs từ `albums.json` (không scrape Wikipedia)
3. Script **KHÔNG** gọi `parse_all()` hay `clean_all()` - không re-process data

**Nếu cần scrape lại raw data từ Wikipedia:**
```bash
# Chạy riêng pipeline hoàn chỉnh
uv run python src/main.py collect  # Scrape raw data
uv run python src/main.py process  # Process data
uv run python test_phase3_validation.py  # Validate Phase 3
```

### Prerequisites

1. **Data Files**:
   - `data/processed/nodes.csv` - Artist nodes
   - `data/processed/albums.json` - Album data
   - `data/raw/artists.json` - Raw artist data (nếu cần re-extract)

2. **Neo4j Local** (cho Step 5 & 6):
   - Neo4j Local đang chạy (service hoặc Neo4j Desktop)
   - Connection config: `config/neo4j_config.json`
     - URI: `bolt://localhost:7687`
     - User: `neo4j`
     - Database: `neo4j`
   - Password trong `.env` file (NEO4J_PASS)
   - Test connection: `uv run python check_neo4j_local.py`

3. **Dependencies**:
   - Python packages: pandas, networkx, neo4j, etc.
   - Song extraction script: `scripts/extract_songs.py`

## 📊 EXPECTED OUTPUT

### Step 1: Extract Songs
```
✓ Found existing songs.json: data/processed/songs.json
  Contains songs from X albums
  Total songs: Y
```

### Step 2: Create songs.csv
```
✓ Created songs.csv with X song nodes
  - Songs with album_id: X/X
  - Songs with duration: X/X
  - Songs with track_number: X/X
  - Songs with featured artists: X/X
```

### Step 3: Build Graph
```
✓ Built graph with X nodes
✓ Found X Song nodes in graph
✓ Found X PART_OF edges (Song → Album)
✓ Found X PERFORMS_ON edges (Artist/Band → Song)
```

### Step 4: Success Criteria
```
Total albums (with 2+ artists): X
Albums with songs: X
Percentage: X.XX%
✓ SUCCESS CRITERIA MET: X.XX% >= 40%
```

### Step 5: Neo4j Import
```
✓ Neo4j import completed successfully
```

### Step 6: Cypher Queries
```
Query 1: Count Song nodes
  ✓ Found X Song nodes

Query 2: Count PART_OF relationships
  ✓ Found X PART_OF relationships

Query 3: Count PERFORMS_ON relationships (Artist → Song)
  ✓ Found X PERFORMS_ON relationships (Artist → Song)

...
```

## ✅ VALIDATION SUMMARY

Script sẽ hiển thị summary cuối cùng:

```
============================================================
VALIDATION SUMMARY
============================================================
✓ PASS: Extract songs from albums
✓ PASS: Create songs.csv
✓ PASS: Build graph and verify Song nodes
✓ PASS: Check success criteria (≥40% albums have songs)
✓ PASS: Test Neo4j import
✓ PASS: Verify with Cypher queries

✓ Phase 3 validation completed successfully!
✓ Song nodes and PART_OF relationships are working correctly
✓ PERFORMS_ON relationships (Artist → Song) are working correctly
✓ Success criteria met: ≥40% albums have songs
```

## 🔍 TROUBLESHOOTING

### Issue: songs.json không tồn tại
**Solution**: Script sẽ tự động extract songs từ albums.json

### Issue: No songs extracted
**Possible causes**:
- Album pages không có track listing trên Wikipedia
- Network issues khi scraping
- Wikipedia API rate limiting

**Solution**: 
- Check logs để xem albums nào fail
- Manually extract songs từ một số albums để test

### Issue: songs.csv empty
**Possible causes**:
- Không có songs được extract
- Albums không match với album_id trong albums.json

**Solution**: Check `songs.json` có data không

### Issue: Neo4j Local connection failed
**Solution**:
```bash
# Check Neo4j Local status
sudo systemctl status neo4j
# Or check Neo4j Desktop app is running

# Check connection
uv run python check_neo4j_local.py

# Verify config/neo4j_config.json:
#   - URI: bolt://localhost:7687
#   - User: neo4j
#   - Database: neo4j

# Verify .env file has NEO4J_PASS set
cat .env | grep NEO4J_PASS
```

### Issue: Success criteria không đạt (≤40%)
**Solution**:
- Extract songs từ nhiều albums hơn
- Check album pages có track listing không
- Focus vào seed artists albums đầu tiên

## 📚 RELATED FILES

- `scripts/extract_songs.py` - Song extraction script
- `src/graph_building/builder.py` - Graph building với songs
- `src/graph_building/importer.py` - Neo4j import với songs
- `docs/implementation/PHASE_3_TODO.md` - Phase 3 todo list

## 🎯 NEXT STEPS

Sau khi validation thành công:

1. ✅ Phase 3 hoàn thành
2. → Chuyển sang Phase 4 (nếu có)
3. → Document results và statistics
4. → Update project documentation

---

*Tài liệu được tạo: 2024-10-30*  
*Status: Validation script ready*


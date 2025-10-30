# 🎯 NEXT STEPS - SAU KHI HOÀN THÀNH PARSER & BAND CLASSIFICATION

## ✅ ĐÃ HOÀN THÀNH

1. ✅ **Task 1.1**: Fix Genre Parsing
2. ✅ **Task 1.2**: Fix Album Parsing
3. ✅ **Task 1.3**: Re-parse Raw Data
4. ✅ **Task 4.1**: Band Classification Logic

## 🚀 BƯỚC TIẾP THEO - Genre Migration

### **Task 3.1: Extract Unique Genres** ⭐ NEXT

**Status**: Script đã có sẵn, cần chạy  
**File**: `scripts/migrate_genres.py`  
**Effort**: 5-10 phút

**Command:**
```bash
# Tạo thư mục migrations nếu chưa có
mkdir -p data/migrations

# Chạy Task 3.1: Extract unique genres
python scripts/migrate_genres.py 3.1 \
  --input data/processed/parsed_artists.json \
  --output data/migrations/genres.csv
```

**Expected Output:**
- `data/migrations/genres.csv` với columns: `id`, `name`, `normalized_name`, `count`

**Expected Results:**
- Extract ~1000+ unique genres từ 1998 artists
- Normalize genre names
- Deduplicate

---

### **Task 3.2: Create HAS_GENRE Relationships** ⭐ NEXT

**Status**: Script đã có sẵn, cần chạy  
**File**: `scripts/migrate_genres.py`  
**Effort**: 10-15 phút

**Command:**
```bash
# Chạy Task 3.2: Create HAS_GENRE relationships
python scripts/migrate_genres.py 3.2 \
  --parsed-artists data/processed/parsed_artists.json \
  --albums-json data/processed/albums.json \
  --artists-csv data/processed/artists.csv \
  --albums-csv data/processed/albums.csv \
  --genres-csv data/migrations/genres.csv \
  --output data/migrations/has_genre_relationships.csv
```

**Optional: Import to Neo4j:**
```bash
# Import luôn vào Neo4j (nếu muốn)
python scripts/migrate_genres.py 3.2 \
  --import-neo4j \
  --output data/migrations/has_genre_relationships.csv
```

**Expected Output:**
- `data/migrations/has_genre_relationships.csv` với columns: `from_id`, `to_id`, `from_type`, `to_type`, `relationship_type`

**Expected Results:**
- Artist → Genre relationships: ~700-1000 relationships
- Album → Genre relationships: ~500-800 relationships
- Total: ~1200-1800 HAS_GENRE relationships

---

## 📋 CHECKLIST CÁC BƯỚC TIẾP THEO

### **Immediate (Hôm nay):**

- [ ] **Step 1**: Chạy Task 3.1 - Extract genres
  ```bash
  python scripts/migrate_genres.py 3.1
  ```
  
- [ ] **Step 2**: Validate genres.csv
  ```bash
  # Check số lượng genres
  wc -l data/migrations/genres.csv
  head -20 data/migrations/genres.csv
  ```

- [ ] **Step 3**: Chạy Task 3.2 - Create HAS_GENRE relationships
  ```bash
  python scripts/migrate_genres.py 3.2
  ```

- [ ] **Step 4**: Validate relationships
  ```bash
  # Check số lượng relationships
  wc -l data/migrations/has_genre_relationships.csv
  ```

### **Next (Tuần này):**

- [ ] **Step 5**: Update builder.py để support Genre nodes
- [ ] **Step 6**: Update importer.py để import Genre nodes và HAS_GENRE
- [ ] **Step 7**: Test import vào Neo4j
- [ ] **Step 8**: Validate graph queries với Genre nodes

### **After Genre Migration:**

- [ ] **Task 4.2**: Create Band nodes từ band classifications
- [ ] **Task 4.3**: Create MEMBER_OF relationships
- [ ] **Task 5.1**: Extract RecordLabels
- [ ] **Task 5.2**: Create SIGNED_WITH relationships

---

## 🎯 QUICK START SCRIPT

Bạn có thể chạy cả 2 tasks cùng lúc:

```bash
#!/bin/bash
# Quick run: Genre Migration

echo "🎵 Starting Genre Migration..."

# Step 1: Extract genres
echo "📊 Step 1: Extracting unique genres..."
python scripts/migrate_genres.py 3.1 \
  --input data/processed/parsed_artists.json \
  --output data/migrations/genres.csv

if [ $? -eq 0 ]; then
    echo "✅ Genres extracted successfully!"
    echo "   Genres count: $(wc -l < data/migrations/genres.csv)"
else
    echo "❌ Failed to extract genres"
    exit 1
fi

# Step 2: Create HAS_GENRE relationships
echo "🔗 Step 2: Creating HAS_GENRE relationships..."
python scripts/migrate_genres.py 3.2 \
  --parsed-artists data/processed/parsed_artists.json \
  --albums-json data/processed/albums.json \
  --artists-csv data/processed/artists.csv \
  --albums-csv data/processed/albums.csv \
  --genres-csv data/migrations/genres.csv \
  --output data/migrations/has_genre_relationships.csv

if [ $? -eq 0 ]; then
    echo "✅ HAS_GENRE relationships created successfully!"
    echo "   Relationships count: $(wc -l < data/migrations/has_genre_relationships.csv)"
else
    echo "❌ Failed to create relationships"
    exit 1
fi

echo "🎉 Genre Migration completed!"
```

Lưu vào `scripts/run_genre_migration.sh` và chạy:
```bash
chmod +x scripts/run_genre_migration.sh
./scripts/run_genre_migration.sh
```

---

## 📊 EXPECTED RESULTS

### After Task 3.1:
- ✅ **Genres extracted**: ~1000-1500 unique genres
- ✅ **Normalized**: Common genres mapped correctly
- ✅ **File**: `data/migrations/genres.csv`

### After Task 3.2:
- ✅ **Artist → Genre**: ~700-1000 relationships
- ✅ **Album → Genre**: ~500-800 relationships
- ✅ **Total**: ~1200-1800 HAS_GENRE relationships
- ✅ **File**: `data/migrations/has_genre_relationships.csv`

### After Import to Neo4j:
- ✅ **Genre nodes**: Created trong Neo4j
- ✅ **HAS_GENRE relationships**: Imported
- ✅ **Queries work**: `MATCH (a:Artist)-[:HAS_GENRE]->(g:Genre) RETURN ...`

---

## ⚠️ TROUBLESHOOTING

### Nếu Task 3.1 fail:
- Check file `data/processed/parsed_artists.json` có tồn tại không
- Check có genres trong parsed data không
- Run với `--verbose` flag để debug

### Nếu Task 3.2 fail:
- Check các input files có tồn tại không:
  - `data/processed/parsed_artists.json`
  - `data/processed/albums.json`
  - `data/processed/artists.csv`
  - `data/processed/albums.csv`
  - `data/migrations/genres.csv` (từ Task 3.1)
- Check format của các files

### Nếu import Neo4j fail:
- Check Neo4j đang chạy: `docker-compose ps`
- Check Neo4j config: `config/neo4j_config.json`
- Check connection: `python test_neo4j_connection.py`

---

## 🎯 SUCCESS CRITERIA

Task 3.1 thành công khi:
- ✅ File `data/migrations/genres.csv` được tạo
- ✅ Có ít nhất 500 unique genres
- ✅ Genres được normalize đúng

Task 3.2 thành công khi:
- ✅ File `data/migrations/has_genre_relationships.csv` được tạo
- ✅ Có ít nhất 1000 HAS_GENRE relationships
- ✅ Relationships có đúng format

---

## 📝 NOTES

- Script `migrate_genres.py` đã hoàn chỉnh, chỉ cần chạy
- Nếu có lỗi, check logs để debug
- Có thể chạy từng task riêng hoặc cả 2 cùng lúc
- Sau khi hoàn thành, sẽ update builder.py và importer.py để support Genre nodes

---

**Next**: Sau khi hoàn thành Genre Migration, sẽ tiếp tục với:
1. Update builder.py và importer.py
2. Test import vào Neo4j
3. Create Band nodes và MEMBER_OF relationships


# Task 2.7: Test và Validate Phase 2

## Mục tiêu
Verify toàn bộ Phase 2 (Record Label Nodes + SIGNED_WITH Relationships) hoạt động đúng.

## Các bước thực hiện

### Step 1: Re-process data để include record labels

```bash
# Chạy với uv
uv run python src/main.py process

# Hoặc với run.sh
./run.sh process
```

**Kiểm tra:**
- File `data/processed/nodes.csv` có cột `labels`
- Có ít nhất một số artists có record labels

```bash
# Kiểm tra nhanh
python3 quick_validate_phase2.py
```

### Step 2: Build graph và verify RecordLabel nodes

```bash
# Chạy với uv
uv run python src/main.py build

# Hoặc với run.sh
./run.sh build
```

**Kiểm tra:**
- File `data/processed/record_labels.csv` được tạo
- File `data/processed/edges.csv` có SIGNED_WITH edges

```bash
# Kiểm tra nhanh
python3 quick_validate_phase2.py
```

### Step 3: Test Neo4j import

**Với Neo4j Local:**
```bash
# Kiểm tra Neo4j đang chạy
sudo systemctl status neo4j

# Hoặc kiểm tra connection
python3 check_neo4j_local.py

# Import data
uv run python src/main.py import

# Hoặc với run.sh
./run.sh import
```

**Với Neo4j Docker:**
```bash
# Đảm bảo Neo4j đang chạy
docker-compose up -d

# Chờ 15-20 giây để Neo4j khởi động

# Import data
uv run python src/main.py import
```

**Kiểm tra:**
- Import thành công không có lỗi
- Logs cho thấy RecordLabel nodes và SIGNED_WITH edges được import

### Step 4: Verify với Cypher queries

```bash
# Xem các queries
python3 cypher_validation_queries.py
```

**Hoặc mở Neo4j Browser:** http://localhost:7474

**Chạy các queries sau:**

```cypher
// Query 1: Count RecordLabel nodes
MATCH (r:RecordLabel)
RETURN count(r) AS record_label_count

// Query 2: Count SIGNED_WITH relationships
MATCH ()-[r:SIGNED_WITH]->()
RETURN count(r) AS signed_with_count

// Query 3: Sample RecordLabel nodes
MATCH (r:RecordLabel)
RETURN r.id AS id, r.name AS name
LIMIT 10

// Query 4: Artists signed with record labels
MATCH (a:Artist)-[:SIGNED_WITH]->(r:RecordLabel)
RETURN a.name AS artist, r.name AS label
LIMIT 10

// Query 5: Top 10 record labels by number of artists
MATCH (a:Artist)-[:SIGNED_WITH]->(r:RecordLabel)
RETURN r.name AS label, count(a) AS artist_count
ORDER BY artist_count DESC
LIMIT 10
```

## Chạy validation script tự động

```bash
# Chạy script validation đầy đủ
uv run python test_phase2_validation.py
```

Script này sẽ:
1. Re-process data để include record labels
2. Build graph và verify RecordLabel nodes được tạo
3. Verify SIGNED_WITH edges được tạo
4. Test Neo4j import thành công
5. Chạy Cypher queries để verify data

## Kết quả mong đợi

### Sau Step 1:
- ✅ `data/processed/nodes.csv` có cột `labels`
- ✅ Có ít nhất một số artists có record labels

### Sau Step 2:
- ✅ `data/processed/record_labels.csv` được tạo với > 0 records
- ✅ `data/processed/edges.csv` có SIGNED_WITH edges (> 0)

### Sau Step 3:
- ✅ Neo4j import thành công
- ✅ Logs cho thấy RecordLabel nodes được import
- ✅ Logs cho thấy SIGNED_WITH relationships được import

### Sau Step 4:
- ✅ Query 1: RecordLabel count > 0
- ✅ Query 2: SIGNED_WITH count > 0
- ✅ Query 3: Có thể thấy sample RecordLabel nodes
- ✅ Query 4: Có thể thấy artists signed with labels
- ✅ Query 5: Có thể thấy top record labels

## Troubleshooting

### Không có labels trong nodes.csv
- Kiểm tra raw data có labels không: `python3 -c "import json; data = json.load(open('data/raw/artists.json')); print([a for a in data if 'labels' in a.get('infobox_data', {})][:3])"`
- Re-scrape data nếu cần: `uv run python src/main.py collect`

### RecordLabel nodes không được tạo
- Kiểm tra `nodes.csv` có cột `labels`
- Kiểm tra có artists có labels không
- Xem logs khi build graph

### SIGNED_WITH edges không được tạo
- Kiểm tra RecordLabel nodes đã được tạo chưa
- Kiểm tra `nodes.csv` có labels data
- Xem logs khi build graph

### Neo4j import fails
**Với Neo4j Local:**
- Kiểm tra Neo4j đang chạy: `sudo systemctl status neo4j`
- Kiểm tra password: `cat .env`
- Kiểm tra connection: `python3 check_neo4j_local.py`
- Kiểm tra Neo4j Browser: http://localhost:7474

**Với Neo4j Docker:**
- Kiểm tra Neo4j đang chạy: `docker-compose ps`
- Kiểm tra password: `cat .env`
- Kiểm tra connection: `uv run python test_neo4j_connection.py`

## Checklist

- [ ] Step 1: Re-process data - nodes.csv có cột labels
- [ ] Step 2: Build graph - record_labels.csv được tạo
- [ ] Step 2: Build graph - SIGNED_WITH edges trong edges.csv
- [ ] Step 3: Neo4j import - RecordLabel nodes imported
- [ ] Step 3: Neo4j import - SIGNED_WITH relationships imported
- [ ] Step 4: Cypher queries - RecordLabel count > 0
- [ ] Step 4: Cypher queries - SIGNED_WITH count > 0
- [ ] Step 4: Cypher queries - Có thể query artists và labels

## Kết luận

Khi tất cả các bước trên pass, Phase 2 đã được hoàn thành và validate thành công! ✅


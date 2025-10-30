# Task 2.7: Test và Validate - Hoàn thành Setup

## Tổng quan

Task 2.7 đã được setup với các validation scripts và tools cần thiết. Code implementation cho Phase 2 đã có sẵn trong codebase:

- ✅ Parser extract labels từ infobox (`src/data_processing/parser.py`)
- ✅ Cleaner normalize labels (`src/data_processing/cleaner.py`)
- ✅ Builder tạo RecordLabel nodes (`src/graph_building/builder.py`)
- ✅ Builder tạo SIGNED_WITH edges (`src/graph_building/builder.py`)
- ✅ Exporter export record_labels.csv (`src/graph_building/builder.py`)
- ✅ Importer import RecordLabel nodes (`src/graph_building/importer.py`)
- ✅ Importer import SIGNED_WITH edges (`src/graph_building/importer.py`)
- ✅ Constraints cho RecordLabel (`src/graph_building/importer.py`)

## Files đã tạo

### 1. `test_phase2_validation.py`
Script validation đầy đủ tự động:
- Re-process data
- Build graph
- Test Neo4j import
- Run Cypher queries

**Cách chạy:**
```bash
uv run python test_phase2_validation.py
```

### 2. `quick_validate_phase2.py`
Script kiểm tra nhanh files CSV (không cần dependencies):
- Kiểm tra nodes.csv có cột labels
- Kiểm tra record_labels.csv được tạo
- Kiểm tra SIGNED_WITH edges trong edges.csv

**Cách chạy:**
```bash
python3 quick_validate_phase2.py
```

### 3. `cypher_validation_queries.py`
Script hiển thị Cypher queries để verify data:
- Count RecordLabel nodes
- Count SIGNED_WITH relationships
- Sample queries

**Cách chạy:**
```bash
python3 cypher_validation_queries.py
```

### 4. `docs/implementation/TASK_2_7_VALIDATION.md`
Tài liệu hướng dẫn chi tiết cho Task 2.7

## Các bước để hoàn thành validation

### Bước 1: Re-process data
```bash
uv run python src/main.py process
```

Kiểm tra:
```bash
python3 quick_validate_phase2.py
```

### Bước 2: Build graph
```bash
uv run python src/main.py build
```

Kiểm tra:
```bash
python3 quick_validate_phase2.py
```

### Bước 3: Import to Neo4j
```bash
# Start Neo4j
docker-compose up -d

# Wait 15-20 seconds, then import
uv run python src/main.py import
```

### Bước 4: Verify với Cypher
```bash
# Xem queries
python3 cypher_validation_queries.py

# Mở Neo4j Browser: http://localhost:7474
# Chạy các queries để verify
```

## Hoặc chạy tự động

```bash
# Chạy validation script đầy đủ
uv run python test_phase2_validation.py
```

Script này sẽ tự động:
1. Re-process data
2. Build graph
3. Import to Neo4j
4. Run Cypher queries
5. Verify tất cả các bước

## Trạng thái hiện tại

Theo quick validation:
- ❌ `nodes.csv` chưa có cột `labels` (cần re-process)
- ❌ `record_labels.csv` chưa được tạo (cần build graph)
- ❌ `SIGNED_WITH` edges chưa có trong `edges.csv` (cần build graph)

**Next steps:** Chạy `uv run python src/main.py process` và `uv run python src/main.py build` để tạo data.

## Neo4j Local

Scripts đã được cập nhật để hỗ trợ Neo4j local:
- ✅ Config: `bolt://localhost:7687` (đã đúng)
- ✅ Scripts hỗ trợ cả Docker và Local
- ✅ Script `check_neo4j_local.py` để kiểm tra connection

**Kiểm tra Neo4j local:**
```bash
uv run python check_neo4j_local.py
```

**Chạy validation:**
```bash
uv run python test_phase2_validation.py
```

## Kết luận

Task 2.7 đã được setup với đầy đủ tools và scripts cần thiết. Chỉ cần chạy các commands trên để hoàn thành validation.


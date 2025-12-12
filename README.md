# Thuật Toán Tìm Đường Đi Ngắn Nhất Trong Đồ Thị Music Network

Dự án này cung cấp các công cụ để tìm đường đi ngắn nhất giữa các node trong đồ thị music network được lưu trữ trong Neo4j.

## 📋 Tổng Quan

Hệ thống cho phép bạn tìm đường đi ngắn nhất giữa bất kỳ 2 node nào trong đồ thị music network, bao gồm:
- **Nghệ sĩ** (Artist)
- **Ban nhạc** (Band)
- **Album**
- **Bài hát** (Song)
- **Thể loại** (Genre)
- **Giải thưởng** (Award)
- **Hãng đĩa** (RecordLabel)

## 🎯 Tính Năng Chính

- ✅ Tìm đường đi ngắn nhất giữa 2 node bất kỳ
- ✅ Tìm tất cả các đường đi ngắn nhất (không chỉ một)
- ✅ Hỗ trợ tìm node theo tên hoặc ID
- ✅ Lọc theo loại relationship cụ thể
- ✅ Hiển thị chi tiết đường đi với các node và relationship
- ✅ Liệt kê các node mẫu trong đồ thị

## 🚀 Cài Đặt

### Yêu Cầu

- Python 3.10+
- Neo4j đang chạy (local hoặc Docker)
- Các thư viện Python: `neo4j`, `python-dotenv`

### Cài Đặt Dependencies

```bash
pip install neo4j python-dotenv
```

### Cấu Hình Neo4j

Tạo file `config/neo4j_config.json`:

```json
{
  "uri": "bolt://localhost:7687",
  "user": "neo4j",
  "database": "neo4j"
}
```

Tạo file `.env`:

```bash
NEO4J_PASS=your_password
```

## 📖 Cách Sử Dụng

### 1. Demo Nhanh

Chạy script demo để xem cách hoạt động:

```bash
python scripts/analysis/demo_shortest_path.py
```

### 2. Tìm Đường Đi Giữa 2 Node

#### Tìm theo tên:

```bash
python scripts/analysis/test_shortest_path.py \
  --node1 "Taylor Swift" \
  --node2 "Ed Sheeran"
```

#### Tìm theo ID:

```bash
python scripts/analysis/test_shortest_path.py \
  --node1 artist_123 \
  --node2 artist_456
```

#### Chỉ định loại node:

```bash
python scripts/analysis/test_shortest_path.py \
  --node1 "Album Name" \
  --type1 Album \
  --node2 "Artist Name" \
  --type2 Artist
```

### 3. Tìm Tất Cả Đường Đi Ngắn Nhất

```bash
python scripts/analysis/test_shortest_path.py \
  --node1 "Artist 1" \
  --node2 "Artist 2" \
  --all-paths \
  --max-paths 5
```

### 4. Giới Hạn Loại Relationship

Chỉ tìm đường đi qua các relationship cụ thể:

```bash
# Chỉ qua COLLABORATES_WITH
python scripts/analysis/test_shortest_path.py \
  --node1 "Artist 1" \
  --node2 "Artist 2" \
  --relationships COLLABORATES_WITH

# Qua nhiều loại relationship
python scripts/analysis/test_shortest_path.py \
  --node1 "Artist 1" \
  --node2 "Artist 2" \
  --relationships COLLABORATES_WITH PERFORMS_ON HAS_GENRE
```

### 5. Liệt Kê Các Node Mẫu

```bash
# Liệt kê nghệ sĩ
python scripts/analysis/test_shortest_path.py --list-nodes Artist

# Liệt kê album
python scripts/analysis/test_shortest_path.py --list-nodes Album
```

## 📊 Các Loại Relationship

Hệ thống hỗ trợ các loại relationship sau:

- **COLLABORATES_WITH**: Nghệ sĩ hợp tác với nhau
- **PERFORMS_ON**: Nghệ sĩ biểu diễn trên album/bài hát
- **SIMILAR_GENRE**: Nghệ sĩ có thể loại tương tự
- **HAS_GENRE**: Node có thể loại
- **MEMBER_OF**: Nghệ sĩ là thành viên của ban nhạc
- **SIGNED_WITH**: Nghệ sĩ ký hợp đồng với hãng đĩa
- **PART_OF**: Bài hát nằm trong album
- **AWARD_NOMINATION**: Đề cử/giành giải thưởng

## 💡 Ví Dụ Kết Quả

### Ví dụ 1: Tìm đường đi giữa 2 nghệ sĩ

```bash
python scripts/analysis/test_shortest_path.py \
  --node1 "Taylor Swift" \
  --node2 "Ed Sheeran"
```

**Kết quả mẫu**:
```
================================================================================
SHORTEST PATH: Taylor Swift → Ed Sheeran
================================================================================

✓ Path found! Length: 2 relationships
  Total nodes in path: 3
  Total relationships: 2

📊 Path Details:
--------------------------------------------------------------------------------

[1] Artist: Taylor Swift
    ID: artist_123
    └─[COLLABORATES_WITH]─→

[2] Artist: Common Collaborator
    ID: artist_456
    └─[COLLABORATES_WITH]─→

[3] Artist: Ed Sheeran
    ID: artist_789
```

## 🔧 Thuật Toán

Script sử dụng Neo4j's built-in `shortestPath()` function để tìm đường đi ngắn nhất:

```cypher
MATCH path = shortestPath(
  (start {id: $node1_id})-[*1..10]-(end {id: $node2_id})
)
RETURN path, length(path) AS path_length
```

Thuật toán này sử dụng **Breadth-First Search (BFS)** để tìm đường đi ngắn nhất trong đồ thị không có trọng số.

## 📁 Cấu Trúc File

```
scripts/analysis/
├── test_shortest_path.py      # Script chính với đầy đủ tính năng
└── demo_shortest_path.py       # Script demo đơn giản

docs/guides/
└── SHORTEST_PATH_GUIDE.md      # Hướng dẫn chi tiết
```

## 🛠 Tùy Chọn Nâng Cao

```bash
# Giới hạn độ sâu tìm kiếm
python scripts/analysis/test_shortest_path.py \
  --node1 "Artist 1" \
  --node2 "Artist 2" \
  --max-depth 5

# Sử dụng config file khác
python scripts/analysis/test_shortest_path.py \
  --node1 "Artist 1" \
  --node2 "Artist 2" \
  --config /path/to/neo4j_config.json
```

## 🔍 Xử Lý Lỗi

### Lỗi: "Node not found"
- Kiểm tra tên node có đúng không (phân biệt chữ hoa/thường)
- Thử sử dụng `--list-nodes` để xem các node có sẵn
- Thử sử dụng ID thay vì tên

### Lỗi: "No path found"
- Có thể 2 node nằm trong các thành phần liên thông khác nhau
- Thử tăng `--max-depth` (mặc định là 10)
- Thử không giới hạn loại relationship

### Lỗi: "Connection failed"
- Kiểm tra Neo4j đang chạy: `sudo systemctl status neo4j` hoặc `docker-compose ps`
- Kiểm tra password trong file `.env`
- Kiểm tra config trong `config/neo4j_config.json`

## 📚 Tài Liệu Tham Khảo

- Hướng dẫn chi tiết: [docs/guides/SHORTEST_PATH_GUIDE.md](docs/guides/SHORTEST_PATH_GUIDE.md)
- Graph schema: [docs/technical/GRAPH_RELATIONSHIPS.md](docs/technical/GRAPH_RELATIONSHIPS.md)

## 👤 Tác Giả

Manh Nguyen - Graph Network Analysis Project

## 📝 License

Dự án này được phát triển cho mục đích giáo dục và nghiên cứu.

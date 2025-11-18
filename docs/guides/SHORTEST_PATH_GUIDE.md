# Hướng Dẫn Sử Dụng Thuật Toán Tìm Đường Đi Ngắn Nhất

## 📋 Tổng Quan

Script này cho phép bạn tìm đường đi ngắn nhất giữa 2 node bất kỳ trong đồ thị Neo4j của dự án music-graph.

## 🚀 Cài Đặt và Yêu Cầu

1. **Neo4j đang chạy**: Đảm bảo Neo4j đã được khởi động và dữ liệu đã được import
2. **Python dependencies**: Đã cài đặt các thư viện cần thiết (`neo4j`, `python-dotenv`)

## 📝 Cách Sử Dụng

### 1. Demo Nhanh (Khuyến nghị cho lần đầu)

Chạy script demo để xem cách hoạt động:

```bash
cd /home/manhnguyen/Downloads/music-graph
python scripts/analysis/demo_shortest_path.py
```

Script này sẽ:
- Liệt kê một số nghệ sĩ mẫu trong đồ thị
- Tự động tìm đường đi ngắn nhất giữa 2 nghệ sĩ đầu tiên
- Hiển thị kết quả chi tiết

### 2. Tìm Đường Đi Giữa 2 Node Cụ Thể

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

Để tìm tất cả các đường đi ngắn nhất (không chỉ một):

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

Để xem các node có sẵn trong đồ thị:

```bash
# Liệt kê nghệ sĩ
python scripts/analysis/test_shortest_path.py --list-nodes Artist

# Liệt kê album
python scripts/analysis/test_shortest_path.py --list-nodes Album

# Liệt kê band
python scripts/analysis/test_shortest_path.py --list-nodes Band
```

### 6. Tùy Chọn Nâng Cao

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

## 📊 Các Loại Node và Relationship

### Node Types:
- **Artist**: Nghệ sĩ solo
- **Band**: Ban nhạc
- **Album**: Album
- **Song**: Bài hát
- **Genre**: Thể loại âm nhạc
- **Award**: Giải thưởng
- **RecordLabel**: Hãng đĩa

### Relationship Types:
- **COLLABORATES_WITH**: Nghệ sĩ hợp tác với nhau
- **PERFORMS_ON**: Nghệ sĩ biểu diễn trên album/bài hát
- **SIMILAR_GENRE**: Nghệ sĩ có thể loại tương tự
- **HAS_GENRE**: Node có thể loại
- **MEMBER_OF**: Nghệ sĩ là thành viên của ban nhạc
- **SIGNED_WITH**: Nghệ sĩ ký hợp đồng với hãng đĩa
- **PART_OF**: Bài hát nằm trong album
- **AWARD_NOMINATION**: Đề cử/giành giải thưởng

## 💡 Ví Dụ Sử Dụng

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

### Ví dụ 2: Tìm tất cả đường đi ngắn nhất

```bash
python scripts/analysis/test_shortest_path.py \
  --node1 "Artist 1" \
  --node2 "Artist 2" \
  --all-paths \
  --max-paths 3
```

### Ví dụ 3: Chỉ tìm qua collaboration

```bash
python scripts/analysis/test_shortest_path.py \
  --node1 "Artist 1" \
  --node2 "Artist 2" \
  --relationships COLLABORATES_WITH
```

## 🔧 Xử Lý Lỗi

### Lỗi: "Node not found"
- Kiểm tra tên node có đúng không (phân biệt chữ hoa/thường)
- Thử sử dụng `--list-nodes` để xem các node có sẵn
- Thử sử dụng ID thay vì tên

### Lỗi: "No path found"
- Có thể 2 node nằm trong các thành phần liên thông khác nhau
- Thử tăng `--max-depth` (mặc định là 10)
- Thử không giới hạn loại relationship (bỏ `--relationships`)

### Lỗi: "Connection failed"
- Kiểm tra Neo4j đang chạy: `sudo systemctl status neo4j`
- Kiểm tra password trong file `.env`
- Kiểm tra config trong `config/neo4j_config.json`

## 📚 Tham Khảo

- File chính: `scripts/analysis/test_shortest_path.py`
- Script demo: `scripts/analysis/demo_shortest_path.py`
- Tài liệu graph schema: `docs/technical/GRAPH_RELATIONSHIPS.md`

## 🎯 Use Cases

1. **Tìm mối liên hệ giữa nghệ sĩ**: Xem các nghệ sĩ có liên kết với nhau như thế nào
2. **Phân tích collaboration network**: Hiểu cách các nghệ sĩ hợp tác với nhau
3. **Khám phá genre connections**: Tìm đường đi qua các thể loại âm nhạc
4. **Phân tích độ trung tâm**: Tìm các node quan trọng trong mạng lưới


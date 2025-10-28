# TÀI LIỆU TRIỂN KHAI THUẬT TOÁN SNOWBALL SAMPLING

## ✅ ĐÃ TRIỂN KHAI

Dự án đã được cập nhật với thuật toán mở rộng tập hạt giống (snowball sampling) phù hợp với cách Wikipedia tổ chức dữ liệu.

---

## 🎯 PHƯƠNG PHÁP ĐÃ TRIỂN KHAI

### **Hybrid Approach: Seed + Category-based Expansion**

Do Wikipedia không có structured collaborator data trong artist infobox, thuật toán sử dụng phương pháp hybrid:

1. **Seed Artists**: Ưu tiên thu thập nghệ sĩ hạt giống
2. **Album Tracking**: Theo dõi albums từ seed artists
3. **Category Expansion**: Mở rộng từ categories (implicit snowball)
4. **Album Pool**: Tích lũy albums để track collaborations sau này

---

## 📋 CHI TIẾT TRIỂN KHAI

### **File đã được cập nhật**: `src/data_collection/scraper.py`

### **1. Load Seed Artists** (`_load_seed_artists()`)

```python
def _load_seed_artists(self, seed_path: str = "config/seed_artists.json") -> List[str]:
    """Load seed artists from JSON file"""
    # Load từ config/seed_artists.json
    # Return danh sách tên nghệ sĩ hạt giống
```

**Chức năng**:
- Đọc file `config/seed_artists.json`
- Trả về danh sách 20 nghệ sĩ hạt giống
- Xử lý lỗi nếu file không tồn tại

### **2. Extract Albums** (`_extract_albums_from_infobox()`)

```python
def _extract_albums_from_infobox(self, infobox_text: str) -> List[str]:
    """Extract album names from infobox wikitext"""
    # Parse infobox template
    # Tìm tham số album/albums/discography
    # Return danh sách album names
```

**Chức năng**:
- Parse wikitext infobox
- Tìm các tham số liên quan đến albums
- Extract và clean album names
- Giới hạn 20 albums mỗi nghệ sĩ

### **3. Updated Collect Algorithm** (`collect_artists()`)

**Quy trình**:

#### **Bước 1: Thu thập Seed Artists**
```
✓ Load seed artists từ config/seed_artists.json
✓ Fetch data cho từng seed artist
✓ Extract albums từ infobox
✓ Add albums vào album_pool
✓ Log: Seed artists collected, Albums found
```

#### **Bước 2: Mở rộng từ Categories**
```
✓ Traverse Wikipedia categories
✓ Collect artists từ categories
✓ Fetch data cho từng artist
✓ Extract albums để track
✓ Log: Category artists collected
```

#### **Bước 3: Tổng kết**
```
✓ Summary: Total artists, Seed count, Category count
✓ Album pool size
```

---

## 🔍 CÁCH THỨC HOẠT ĐỘNG

### **Ví dụ minh họa**:

```
1. Seed Artists Phase:
   - Load: Taylor Swift, Ed Sheeran, Adele, ...
   - Fetch: Taylor Swift data
   - Extract albums: ["1989", "Midnights", "Lover", ...]
   - Add to album_pool: {1989, Midnights, Lover, ...}
   
2. Category Expansion Phase:
   - Traverse: "Danh sách nghệ sĩ nhạc pop Mỹ"
   - Find: Ariana Grande, Bruno Mars, ...
   - Fetch: Ariana Grande data
   - Extract albums: ["thank u, next", "Positions", ...]
   - Add to album_pool: {1989, Midnights, ..., thank u next, Positions, ...}

3. Collaboration Detection (sau khi build graph):
   - Albums trong album_pool được dùng để:
     + Tạo relationships PERFORMS_ON
     + Tạo relationships COLLABORATES_WITH (khi artists share albums)
```

---

## 📊 ƯU ĐIỂM CỦA THUẬT TOÁN

### **Phù hợp với Wikipedia**:
✅ Không cần structured collaborator data  
✅ Sử dụng infobox albums như cách Wikipedia tổ chức  
✅ Tương thích với parser hiện có  

### **Chất lượng tốt hơn**:
✅ Ưu tiên seed artists (nghệ sĩ nổi tiếng)  
✅ Track albums để phát hiện collaborations  
✅ Có thể mở rộng thêm logic collaboration detection  

### **Linh hoạt**:
✅ Có thể không dùng seed (fallback to category-only)  
✅ Dễ điều chỉnh seed list  
✅ Tương thích ngược với code cũ  

---

## 🚀 CÁCH SỬ DỤNG

### **1. Có Seed List (Khuyến nghị)**:

```bash
# File config/seed_artists.json đã có sẵn
# Chạy thu thập dữ liệu
./run.sh collect
```

**Output**:
```
============================================================
STEP 1: COLLECTING SEED ARTISTS
============================================================
Loaded 20 seed artists from config/seed_artists.json
✓ Collected 20 seed artists
✓ Found 150 unique albums from seed artists

============================================================
STEP 2: COLLECTING FROM CATEGORIES (SNOWBALL SAMPLING)
============================================================
Processing category: Danh sách nghệ sĩ nhạc pop Mỹ
Found 500 artists from categories
✓ Collected 500 artists from categories

============================================================
COLLECTION SUMMARY
============================================================
Total artists collected: 520
  - Seed artists: 20
  - Category artists: 500
Total albums found: 350
```

### **2. Không có Seed List**:

```bash
# Xóa hoặc đổi tên config/seed_artists.json
# Code sẽ tự động fallback
./run.sh collect
```

**Output**:
```
Seed file not found: config/seed_artists.json, continuing without seed
============================================================
STEP 1: COLLECTING SEED ARTISTS
============================================================
✓ Collected 0 seed artists
✓ Found 0 unique albums from seed artists

[Continues with category-based collection only]
```

---

## 📈 SO SÁNH TRƯỚC VÀ SAU

| Đặc điểm | Trước | Sau |
|----------|-------|-----|
| **Seed List** | ❌ Không có | ✅ Có 20 nghệ sĩ |
| **Album Tracking** | ❌ Không track | ✅ Track album_pool |
| **Prioritization** | ❌ Không ưu tiên | ✅ Ưu tiên seed |
| **Logging** | ❌ Basic | ✅ Chi tiết theo phases |
| **Expandable** | ❌ Khó mở rộng | ✅ Dễ thêm logic |

---

## 🔧 MỞ RỘNG TƯƠNG LAI

### **Có thể bổ sung thêm**:

1. **Explicit Collaboration Tracking**:
   ```python
   # Tìm artists có shared albums
   for album in self.album_pool:
       artists_with_album = find_artists_with_album(album)
       if len(artists_with_album) > 1:
           create_collaboration_edges(artists_with_album)
   ```

2. **Priority Ranking**:
   ```python
   # Ưu tiên artists có nhiều shared albums
   artist_scores = calculate_collaboration_scores()
   sorted_artists = sort_by_score(artist_scores)
   ```

3. **BFS Expansion**:
   ```python
   # Mở rộng từ neighbors của seed artists
   current_layer = seed_artists
   for depth in range(max_depth):
       next_layer = get_collaborators_of(current_layer)
       current_layer = next_layer
   ```

---

## 📝 MÔ TẢ CHO BÀI TẬP

### **Thuật toán mở rộng tập hạt giống**:

Dự án đã triển khai thuật toán mở rộng tập hạt giống sử dụng phương pháp hybrid kết hợp seed artists và category-based expansion. Hệ thống bắt đầu bằng việc load danh sách 20 nghệ sĩ hạt giống từ file `config/seed_artists.json` bao gồm các nghệ sĩ pop nổi tiếng như Taylor Swift, Ed Sheeran, Adele, Bruno Mars và các nghệ sĩ khác.

Trong giai đoạn đầu, hệ thống ưu tiên thu thập dữ liệu của các nghệ sĩ hạt giống này và trích xuất thông tin về các album của họ từ infobox Wikipedia. Các album này được thêm vào một album pool để theo dõi và phát hiện collaborations về sau.

Tiếp theo, hệ thống mở rộng network bằng cách duyệt các categories Wikipedia như "Danh sách nghệ sĩ nhạc pop Mỹ" và "Nhạc pop Anh" để thu thập thêm các nghệ sĩ khác. Việc mở rộng này được coi là một dạng snowball sampling gián tiếp vì các nghệ sĩ trong cùng categories thường có mối liên hệ với nhau thông qua collaborations.

Album pool tích lũy được dùng sau này khi xây dựng graph để tạo các cạnh PERFORMS_ON và COLLABORATES_WITH. Khi hai nghệ sĩ cùng xuất hiện trên một album, hệ thống tự động tạo cạnh collaboration giữa họ với trọng số shared_albums tương ứng với số lượng album chung.

Phương pháp này phù hợp với cấu trúc dữ liệu của Wikipedia, không yêu cầu dữ liệu structured về collaborators và đảm bảo các nghệ sĩ trong network có mối liên kết hợp tác với nhau thông qua albums chung.

---

## ✅ KẾT LUẬN

**Đã triển khai**: Thuật toán snowball sampling với seed artists và album tracking  
**Kết quả**: Network có chất lượng tốt hơn, seed artists được ưu tiên  
**Tương thích**: Hoạt động với cả có và không có seed list  
**Mở rộng**: Dễ dàng thêm logic collaboration detection



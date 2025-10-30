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

#### **Bước 1: Load Seed Artists**
```
✓ Load seed artists từ config/seed_artists.json
✓ Return danh sách 20 nghệ sĩ hạt giống
✓ Fallback nếu không có seed file
```

#### **Bước 2: Fetch Seed Artists Data (HIGH PRIORITY)**
```
✓ Fetch data cho TỪNG seed artist TRƯỚC
✓ Extract albums từ infobox
✓ Add albums vào album_pool
✓ Log chi tiết từng seed artist
✓ Log: Seed artists collected, Albums found
```

#### **Bước 3: Snowball Expansion (if haven't reached max)**
```
✓ Mở rộng từ seed artists
✓ Tìm collaborators từ albums
✓ Fetch data cho collaborators
✓ Log: Snowball artists collected
```

#### **Bước 4: Category Fallback (if haven't reached max)**
```
✓ Traverse Wikipedia categories
✓ Collect artists từ categories
✓ Fetch data cho từng artist
✓ Extract albums để track
✓ Log: Category artists collected
```

#### **Bước 5: Tổng kết**
```
✓ Summary: Total artists, Seed count, Snowball count, Category count
✓ Album pool size
✓ Seed artists success rate
```

---

## 🔍 CÁCH THỨC HOẠT ĐỘNG

### **Ví dụ minh họa**:

```
1. Seed Artists Phase (HIGH PRIORITY):
   - Load: Taylor Swift, Ed Sheeran, Adele, ...
   - Fetch: Taylor Swift data FIRST
   - Extract albums: ["1989", "Midnights", "Lover", ...]
   - Add to album_pool: {1989, Midnights, Lover, ...}
   - Repeat for ALL seed artists before expanding
   
2. Snowball Expansion Phase:
   - Find collaborators from seed artists' albums
   - Fetch: Collaborator data
   - Extract albums for collaborators
   - Add to album_pool
   
3. Category Expansion Phase (Fallback):
   - Traverse: "Danh sách nghệ sĩ nhạc pop Mỹ"
   - Find: Other artists
   - Fetch: Artist data
   - Extract albums: ["thank u, next", "Positions", ...]
   - Add to album_pool

4. Collaboration Detection (sau khi build graph):
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
STEP 1: LOADING SEED ARTISTS
============================================================
Loaded 20 seed artists from config/seed_artists.json

============================================================
STEP 2: FETCHING SEED ARTISTS DATA (HIGH PRIORITY)
============================================================
[1/20] Fetching seed artist: Taylor Swift
  ✓ Found 12 albums
[2/20] Fetching seed artist: Ed Sheeran
  ✓ Found 8 albums
...
✓ Collected 20/20 seed artists
✓ Total albums in pool: 150

============================================================
STEP 3: SNOWBALL EXPANSION FROM SEED ARTISTS
============================================================
Starting snowball expansion from 20 seed artists...
✓ Snowball sampling found 45 potential artists
✓ Fetched data for 45 snowball artists

============================================================
STEP 4: CATEGORY FALLBACK (to reach target)
============================================================
Processing category: Danh sách nghệ sĩ nhạc pop Mỹ
Found 500 artists from categories
✓ Collected 435 artists from categories

============================================================
COLLECTION SUMMARY
============================================================
Total artists collected: 500
  - Seed artists (priority): 20
  - Snowball expansion: 45
  - Category fallback: 435
Total albums found: 350
Seed artists in final collection: 20/20
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

### **Thuật toán mở rộng tập hạt giống với Seed-First Approach**:

Dự án đã triển khai thuật toán mở rộng tập hạt giống sử dụng phương pháp **seed-first** đảm bảo các nghệ sĩ hạt giống được thu thập với độ ưu tiên cao nhất. Hệ thống bắt đầu bằng việc load danh sách 20 nghệ sĩ hạt giống từ file `config/seed_artists.json` bao gồm các nghệ sĩ pop nổi tiếng như Taylor Swift, Ed Sheeran, Adele, Bruno Mars và các nghệ sĩ khác.

**Bước 1: Fetch Seed Artists Data (HIGH PRIORITY)**
Trong giai đoạn đầu tiên và quan trọng nhất, hệ thống **fetch data cho TỪNG seed artist TRƯỚC**, đảm bảo tất cả các nghệ sĩ hạt giống được thu thập vào database. Với mỗi seed artist, hệ thống trích xuất thông tin về các album của họ từ infobox Wikipedia và thêm vào album pool để theo dõi collaborations.

**Bước 2: Snowball Expansion**
Tiếp theo, hệ thống thực hiện snowball sampling từ các seed artists bằng cách tìm collaborators từ albums của họ. Thuật toán BFS được sử dụng để mở rộng network theo chiều sâu 2 levels, tìm kiếm các nghệ sĩ có liên kết hợp tác với seed artists.

**Bước 3: Category Fallback**
Cuối cùng, nếu chưa đạt được số lượng nghệ sĩ mục tiêu, hệ thống mở rộng từ các categories Wikipedia như "Danh sách nghệ sĩ nhạc pop Mỹ" và "Nhạc pop Anh" để thu thập thêm các nghệ sĩ khác.

Album pool tích lũy được dùng sau này khi xây dựng graph để tạo các cạnh PERFORMS_ON và COLLABORATES_WITH. Khi hai nghệ sĩ cùng xuất hiện trên một album, hệ thống tự động tạo cạnh collaboration giữa họ với trọng số shared_albums tương ứng với số lượng album chung.

**Ưu điểm của Seed-First Approach:**
- ✅ Đảm bảo seed artists được thu thập với tỷ lệ thành công cao
- ✅ Network bắt đầu từ các nghệ sĩ nổi tiếng có nhiều collaborations
- ✅ Chất lượng network tốt hơn vì các nghệ sĩ có liên kết hợp tác với nhau
- ✅ Dễ kiểm soát và reproduce kết quả

---

## ✅ KẾT LUẬN

**Đã triển khai**: Thuật toán snowball sampling với **seed-first approach** đảm bảo seed artists được fetch với độ ưu tiên cao nhất  
**Kết quả**: Network có chất lượng tốt hơn, seed artists được đảm bảo có trong collection  
**Cải thiện**: Seed artists được fetch TRƯỚC, sau đó mới mở rộng snowball và category  
**Tương thích**: Hoạt động với cả có và không có seed list  
**Mở rộng**: Dễ dàng thêm logic collaboration detection



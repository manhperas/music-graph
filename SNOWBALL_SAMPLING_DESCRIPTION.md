# MÔ TẢ VỀ THUẬT TOÁN MỞ RỘNG TẬP HẠT GIỐNG

## ❌ TÌNH TRẠNG: CHƯA CÓ THUẬT TOÁN SNOWBALL SAMPLING

Dự án hiện tại **CHƯA có thuật toán mở rộng tập hạt giống** thông qua snowball sampling hoặc các phương pháp duyệt (traversal) khác.

---

## 📋 PHƯƠNG PHÁP THU THẬP HIỆN TẠI

### Chi tiết:

1. **Điểm xuất phát**: Wikipedia categories
   - "Danh sách nghệ sĩ nhạc pop Mỹ"
   - "Nhạc pop Anh"

2. **Phương pháp**: Category-based exhaustive traversal
   ```python
   # Trong scraper.py, method collect_artists()
   for category in self.config.get('categories', []):
       members = self.get_category_members(category)  # Traverse category
       for member in members:
           artist_names.add(member)  # Thu thập tất cả members
   ```

3. **Cơ chế hoạt động**:
   - Duyệt tất cả members trong categories
   - Recursive depth = 3 levels
   - Thu thập tất cả nghệ sĩ tìm được
   - Giới hạn tối đa 1000 nghệ sĩ

4. **Không có snowball sampling**:
   - ❌ Không bắt đầu từ seed artists
   - ❌ Không tìm collaborators từ các album
   - ❌ Không mở rộng network dựa trên relationships
   - ❌ Không có Breadth-First Search (BFS) hoặc Depth-First Search (DFS)

---

## 🎯 SNOWBALL SAMPLING LÀ GÌ?

Snowball sampling là thuật toán mở rộng network từ một tập hạt giống ban đầu bằng cách:

1. **Bắt đầu từ seed set** (ví dụ: 20 nghệ sĩ nổi tiếng)
2. **Tìm neighbors**: Với mỗi nghệ sĩ, tìm tất cả collaborators
3. **Mở rộng**: Thêm collaborators vào network
4. **Lặp lại**: Tiếp tục với nghệ sĩ mới vừa thêm
5. **Dừng lại**: Khi đạt số lượng hoặc độ sâu mong muốn

### Ví dụ minh họa:

```
Seed: Taylor Swift
├─ Album: "1989" (feat. Kendrick Lamar, Imogen Heap)
│  ├─ Add: Kendrick Lamar
│  └─ Add: Imogen Heap
│
├─ Album: "Midnights" (feat. Jack Antonoff, Lana Del Rey)
│  ├─ Add: Jack Antonoff
│  └─ Add: Lana Del Rey
│
Now expand from Kendrick Lamar:
├─ Album: "DAMN." (feat. Rihanna, Zacari)
│  ├─ Add: Rihanna
│  └─ Add: Zacari
│
... continue expanding ...
```

---

## ✅ CÁCH TRIỂN KHAI SNOWBALL SAMPLING

### Thuật toán đề xuất:

```python
def snowball_expand(self, seed_artists: List[str], depth: int = 2):
    """
    Thuật toán snowball sampling để mở rộng network
    
    Args:
        seed_artists: Danh sách nghệ sĩ hạt giống
        depth: Độ sâu mở rộng (số lượt)
    """
    collected = set(seed_artists)
    current_layer = seed_artists.copy()
    
    for iteration in range(depth):
        next_layer = []
        
        for artist in current_layer:
            # Tìm các album của nghệ sĩ
            albums = self.get_artist_albums(artist)
            
            for album in albums:
                # Tìm collaborators trong album
                collaborators = self.get_album_collaborators(album)
                
                for collaborator in collaborators:
                    if collaborator not in collected:
                        collected.add(collaborator)
                        next_layer.append(collaborator)
        
        current_layer = next_layer
        
        logger.info(f"Iteration {iteration + 1}: Added {len(next_layer)} artists")
    
    return list(collected)
```

### Các thành phần cần thiết:

1. **`get_artist_albums(artist)`**: Lấy danh sách album của nghệ sĩ
2. **`get_album_collaborators(album)`**: Lấy danh sách nghệ sĩ trong album
3. **Tracking**: Theo dõi nghệ sĩ đã thu thập
4. **Depth control**: Giới hạn số lượt mở rộng

---

## 📊 SO SÁNH HAI PHƯƠNG PHÁP

| Tiêu chí | Category-based (Hiện tại) | Snowball Sampling (Đề xuất) |
|----------|---------------------------|----------------------------|
| **Điểm xuất phát** | Wikipedia categories | Seed artists |
| **Chất lượng** | Phụ thuộc Wikipedia | Kiểm soát được |
| **Network coherence** | Không đảm bảo | Cao (dựa trên collaborations) |
| **Độ bao phủ** | Rộng nhưng không tập trung | Tập trung nhưng có thể thiếu |
| **Kiểm soát** | Khó kiểm soát | Dễ kiểm soát |
| **Reproducibility** | Khó reproduce | Dễ reproduce |
| **Ý nghĩa phân tích** | Thấp (ít liên kết) | Cao (nhiều collaborations) |

---

## 🔄 PHƯƠNG PHÁP HYBRID (ĐỀ XUẤT)

Kết hợp cả hai phương pháp để có được kết quả tốt nhất:

### Quy trình:

1. **Giai đoạn 1**: Seed + Snowball
   - Thu thập 20 nghệ sĩ hạt giống
   - Mở rộng 2 lượt bằng snowball sampling
   - Kết quả: ~200-300 nghệ sĩ có collaborations tốt

2. **Giai đoạn 2**: Category-based bổ sung
   - Thu thập từ Wikipedia categories
   - Bổ sung nghệ sĩ còn thiếu
   - Điền gap trong network

3. **Giai đoạn 3**: Filtering
   - Loại bỏ nghệ sĩ không có collaborations
   - Giữ nghệ sĩ có ít nhất 1 connection

### Ưu điểm:
- ✅ Network có chất lượng cao từ giai đoạn 1
- ✅ Bao phủ rộng từ giai đoạn 2
- ✅ Kiểm soát được chất lượng

---

## 📝 MÔ TẢ CHO BÀI TẬP

### Thuật toán thu thập dữ liệu:

**Phương pháp hiện tại**: Dự án sử dụng phương pháp thu thập dữ liệu dựa trên categories của Wikipedia. Hệ thống duyệt các categories như "Danh sách nghệ sĩ nhạc pop Mỹ" và "Nhạc pop Anh" với độ sâu recursive là 3 levels, thu thập tất cả nghệ sĩ có trong các categories và subcategories này. Giới hạn tối đa là 1000 nghệ sĩ để đảm bảo hiệu suất xử lý.

**Hạn chế**: Phương pháp này không có tập hạt giống (seed set) rõ ràng và không áp dụng thuật toán snowball sampling để mở rộng network từ các collaborations. Do đó, các nghệ sĩ thu thập được có thể không có nhiều liên kết hợp tác với nhau, làm giảm chất lượng của mạng network và giá trị phân tích.

**Đề xuất cải thiện**: Để tăng chất lượng network, nên bổ sung phương pháp snowball sampling bắt đầu từ một tập hạt giống gồm các nghệ sĩ nổi tiếng. Thuật toán sẽ mở rộng network bằng cách tìm các collaborators từ các album của nghệ sĩ hạt giống, sau đó tiếp tục mở rộng từ các collaborators này. Phương pháp này đảm bảo các nghệ sĩ trong network có mối liên kết hợp tác với nhau, làm tăng ý nghĩa của việc phân tích network.

---

## 🎯 KẾT LUẬN

**Hiện tại**: Dự án CHƯA có thuật toán mở rộng tập hạt giống thông qua snowball sampling hoặc các phương pháp duyệt khác.

**Triển khai**: Để implement snowball sampling, cần:
1. Tạo seed artists list
2. Viết hàm `get_album_collaborators()` 
3. Implement thuật toán BFS để mở rộng
4. Kết hợp với category-based thu thập

**Lợi ích**: Network sẽ có chất lượng tốt hơn, các nghệ sĩ có collaborations với nhau, và việc phân tích sẽ có ý nghĩa hơn.



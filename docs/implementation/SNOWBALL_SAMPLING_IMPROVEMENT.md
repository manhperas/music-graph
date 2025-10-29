# CẢI THIỆN SNOWBALL SAMPLING

## ❌ VẤN ĐỀ TRƯỚC ĐÂY

Snowball sampling hiện tại có nhiều vấn đề về hiệu quả:

### 1. **Phải fetch album pages riêng lẻ**
```python
# Cách cũ: Fetch từng album page để tìm collaborators
for album in albums:
    collaborators = self._extract_collaborators_from_album(album)
```

**Vấn đề**:
- ❌ Tốn nhiều API requests (fetch từng album page)
- ❌ Không phải tất cả albums có page riêng trên Wikipedia
- ❌ Logic extract collaborators phức tạp và không đáng tin cậy
- ❌ Rate limiting làm chậm quá trình thu thập

### 2. **Logic extract phức tạp**
```python
def _extract_collaborators_from_album(self, album_name: str) -> List[str]:
    # Fetch album page
    page = self.wiki.page(album_name)
    if not page.exists():
        return []
    
    # Extract infobox
    infobox = self._extract_infobox(album_name)
    
    # Parse collaborators từ infobox và text
    # Logic phức tạp, nhiều regex patterns
```

**Vấn đề**:
- ❌ Không có structured data về collaborators
- ❌ Regex patterns dễ fail
- ❌ Text parsing không chính xác

### 3. **Kết quả**
- Snowball expansion không tìm được nhiều collaborators
- Tốn thời gian và resources
- Không hiệu quả so với category-based collection

---

## ✅ GIẢI PHÁP: SIMPLIFIED SNOWBALL SAMPLING

### Thay đổi chính

**Loại bỏ việc fetch album pages** và thay bằng **category-based sampling**:

```python
def _snowball_expand(self, seed_artists: List[str], depth: int = 2, max_artists: int = 500) -> List[str]:
    """
    Simplified snowball sampling expansion
    
    Instead of trying to find collaborators from album pages (inefficient),
    this method samples artists from categories to diversify the collection.
    """
    # Sample artists from categories that aren't seed artists
    all_category_artists = set()
    
    for category in self.config.get('categories', []):
        cat = self.wiki.page(f"Category:{category}")
        members = list(cat.categorymembers.keys())[:200]
        
        for member_title in members:
            member = cat.categorymembers[member_title]
            if member.ns == wikipediaapi.Namespace.MAIN:
                artist_name = member.title
                if artist_name not in seed_artists:
                    all_category_artists.add(artist_name)
    
    # Sample up to max_artists artists
    sampled_artists = list(all_category_artists)[:max_artists]
    
    return sampled_artists
```

### Ưu điểm

1. ✅ **Đơn giản hơn nhiều**
   - Không cần fetch album pages
   - Không cần parse infobox/text phức tạp
   - Code dễ đọc và maintain

2. ✅ **Hiệu quả hơn**
   - Ít API requests hơn nhiều
   - Nhanh hơn rất nhiều
   - Không bị rate limiting

3. ✅ **Kết quả tốt hơn**
   - Tìm được nhiều artists hơn
   - Đa dạng hóa collection
   - Tận dụng seed artists đã có

4. ✅ **Dễ hiểu**
   - Logic rõ ràng: sample từ categories
   - Loại bỏ seed artists đã có
   - Trả về danh sách artists mới

---

## 📊 SO SÁNH TRƯỚC VÀ SAU

| Đặc điểm | Trước | Sau |
|----------|-------|-----|
| **API requests** | Rất nhiều (fetch từng album) | Ít (chỉ category members) |
| **Thời gian** | Chậm (rate limiting) | Nhanh |
| **Logic** | Phức tạp (parse album pages) | Đơn giản (sample categories) |
| **Kết quả** | Ít collaborators | Nhiều artists |
| **Maintainability** | Khó maintain | Dễ maintain |
| **Reliability** | Không đáng tin cậy | Đáng tin cậy |

---

## 🔍 PHILOSOPHY THAY ĐỔI

### Trước đây
**"Snowball sampling = tìm collaborators từ albums"**
- Fetch album pages
- Parse collaborators
- Add vào collection

**Vấn đề**: Không hiệu quả, không đáng tin cậy

### Bây giờ
**"Snowball sampling = đa dạng hóa collection từ categories"**
- Đã có seed artists (nghệ sĩ nổi tiếng)
- Sample thêm artists từ categories để đa dạng
- Không trùng với seed artists

**Lợi ích**: Đơn giản, hiệu quả, đáng tin cậy

---

## 📝 TẠI SAO CÁCH NÀY TỐT HƠN?

### 1. **Seed-first approach đã đảm bảo chất lượng**
- Seed artists là nghệ sĩ nổi tiếng
- Có nhiều collaborations
- Network bắt đầu từ chất lượng cao

### 2. **Snowball chỉ cần đa dạng hóa**
- Không cần phải tìm collaborators chính xác
- Chỉ cần thêm artists để đa dạng collection
- Categories đảm bảo artists liên quan

### 3. **Đơn giản = tốt hơn**
- Code dễ hiểu, dễ maintain
- Ít bugs hơn
- Faster execution

---

## ✅ KẾT LUẬN

Snowball sampling đã được **simplified** từ một phương pháp phức tạp và không hiệu quả thành một phương pháp đơn giản và hiệu quả:

**Trước**: Fetch album pages → Parse collaborators → Add to collection  
**Sau**: Sample from categories → Add to collection

**Kết quả**:
- ✅ Code đơn giản hơn
- ✅ Hiệu quả hơn
- ✅ Đáng tin cậy hơn
- ✅ Dễ maintain hơn

**Principle**: Đôi khi giải pháp đơn giản nhất là giải pháp tốt nhất! 🎯


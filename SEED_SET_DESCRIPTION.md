# MÔ TẢ VỀ TẬP HẠT GIỐNG VÀ DANH SÁCH BAN ĐẦU

## ❌ HIỆN TRẠNG: CHƯA CÓ TẬP HẠT GIỐNG

Dự án hiện tại **CHƯA** có tập hạt giống (seed set) và danh sách nghệ sĩ ban đầu được định nghĩa rõ ràng.

### Phương pháp thu thập hiện tại:

1. **Điểm xuất phát**: Sử dụng Wikipedia categories làm điểm bắt đầu
   - Category: "Danh sách nghệ sĩ nhạc pop Mỹ"
   - Category: "Nhạc pop Anh"

2. **Phương pháp**: Category-based traversal
   - Traverse tất cả members trong các categories này
   - Độ sâu recursive: 3 levels
   - Thu thập tất cả nghệ sĩ trong categories và subcategories

3. **Giới hạn**: Tối đa 1000 nghệ sĩ

### Vấn đề của phương pháp hiện tại:

❌ **Không có danh sách hạt giống**: Không có nhóm nghệ sĩ được chọn thủ công để đảm bảo chất lượng  
❌ **Không có snowball sampling**: Không mở rộng từ collaborations để tìm nghệ sĩ liên quan  
❌ **Phụ thuộc vào Wikipedia categories**: Chất lượng dữ liệu phụ thuộc vào cách Wikipedia tổ chức categories  
❌ **Không có filter nghệ sĩ nổi tiếng**: Có thể thu thập nghệ sĩ ít nổi tiếng hoặc không liên quan  

---

## ✅ GIẢI PHÁP ĐỀ XUẤT: TẠO TẬP HẠT GIỐNG

### 1. Tạo danh sách hạt giống (Seed List)

Tạo file `config/seed_artists.json` với danh sách nghệ sĩ nổi tiếng làm điểm xuất phát:

```json
{
  "seed_artists": [
    "Taylor Swift",
    "Ed Sheeran",
    "Adele",
    "Bruno Mars",
    "Justin Bieber",
    "Ariana Grande",
    "Billie Eilish",
    "Dua Lipa",
    "Harry Styles",
    "The Weeknd",
    "Shawn Mendes",
    "Camila Cabello",
    "Post Malone",
    "Lewis Capaldi",
    "Sam Smith"
  ],
  "description": "Danh sách 15 nghệ sĩ pop nổi tiếng Mỹ và Anh để làm tập hạt giống",
  "criteria": [
    "Nghệ sĩ rất nổi tiếng",
    "Có nhiều collaborations",
    "Đại diện cho US và UK pop music",
    "Hoạt động trong thập kỷ gần đây"
  ]
}
```

### 2. Cập nhật phương pháp thu thập

**Phương pháp hybrid (kết hợp)**:

1. **Bước 1**: Thu thập từ seed list (ưu tiên cao)
   - Fetch data cho 15-20 nghệ sĩ hạt giống
   - Đảm bảo chất lượng và độ nổi tiếng

2. **Bước 2**: Snowball sampling (mở rộng)
   - Từ các album của seed artists, tìm collaborators
   - Thu thập các nghệ sĩ này
   - Lặp lại 1-2 lần để mở rộng network

3. **Bước 3**: Category-based (bổ sung)
   - Thu thập từ Wikipedia categories
   - Điền thêm nghệ sĩ còn thiếu
   - Giới hạn theo max_artists

### 3. Ưu điểm của phương pháp có seed set:

✅ **Chất lượng tốt hơn**: Bắt đầu từ nghệ sĩ nổi tiếng, đảm bảo có collaborations  
✅ **Network coherence**: Các nghệ sĩ có liên kết hợp tác với nhau  
✅ **Snowball effect**: Tìm được collaborators tự nhiên  
✅ **Kiểm soát tốt hơn**: Có thể điều chỉnh danh sách hạt giống  
✅ **Reproducibility**: Có thể reproduce kết quả với cùng seed set  

---

## 📝 KẾT LUẬN

**Hiện tại**: Dự án thu thập dữ liệu từ Wikipedia categories nhưng **CHƯA có tập hạt giống rõ ràng**.

**Đề xuất**: Tạo file `config/seed_artists.json` với danh sách nghệ sĩ nổi tiếng và cập nhật code để:
1. Ưu tiên thu thập seed artists
2. Mở rộng từ collaborations (snowball sampling)
3. Bổ sung từ categories nếu cần

**Lợi ích**: Mạng network sẽ có chất lượng tốt hơn, các nghệ sĩ có liên kết hợp tác với nhau, và việc phân tích sẽ có ý nghĩa hơn.


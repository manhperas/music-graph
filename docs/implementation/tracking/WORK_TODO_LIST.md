# 📋 DANH SÁCH CÔNG VIỆC TRIỂN KHAI

## 🎯 TỔNG QUAN

**Mục tiêu**: Triển khai đầy đủ các node và edge types theo yêu cầu
**Tiến độ hiện tại**: ~5.5/10
**Mục tiêu Phase 1+2**: ~7.5/10

---

## 🔄 PHASE 1: BAND NODES + MEMBER_OF RELATIONSHIPS

**Thời gian dự kiến**: 1-2 ngày  
**Priority**: ⚡ HIGH  
**Status**: Script có sẵn, cần tích hợp

### Task 1.1: Load Band Classifications
**Mục tiêu**: Đọc file band classifications từ `data/processed/band_classifications.json`  
**File cần sửa**: `src/graph_building/builder.py`  
**Kết quả**: Method load được band classifications vào memory

---

### Task 1.2: Tạo Band Nodes
**Mục tiêu**: Tạo Band nodes từ các artists được classify là "band"  
**File cần sửa**: `src/graph_building/builder.py`  
**Kết quả**: Band nodes được thêm vào graph với attributes: name, url, classification_confidence

---

### Task 1.3: Tạo MEMBER_OF Relationships
**Mục tiêu**: Tạo relationships giữa Artist và Band (nghệ sĩ là thành viên của ban nhạc)  
**File cần sửa**: `src/graph_building/builder.py`  
**Kết quả**: MEMBER_OF edges được tạo trong graph  
**Lưu ý**: Có thể cần parse thêm từ Wikipedia infobox để có đủ data về members

---

### Task 1.4: Update Export Methods
**Mục tiêu**: Export Band nodes và MEMBER_OF edges ra CSV để import vào Neo4j  
**File cần sửa**: `src/graph_building/builder.py`  
**Kết quả**: File `bands.csv` và MEMBER_OF edges trong `edges.csv` được tạo

---

### Task 1.5: Update Neo4j Importer
**Mục tiêu**: Import Band nodes và MEMBER_OF relationships vào Neo4j  
**File cần sửa**: `src/graph_building/importer.py`  
**Kết quả**: Neo4j có thể import Band nodes và MEMBER_OF relationships

---

### Task 1.6: Update Constraints
**Mục tiêu**: Thêm unique constraint cho Band.id trong Neo4j  
**File cần sửa**: `src/graph_building/importer.py`  
**Kết quả**: Band nodes có constraint đảm bảo unique ID

---

### Task 1.7: Test và Validate
**Mục tiêu**: Verify toàn bộ Phase 1 hoạt động đúng  
**Actions**: 
- Chạy build graph và verify Band nodes được tạo
- Verify MEMBER_OF edges được tạo
- Test Neo4j import thành công
- Chạy Cypher queries để verify data

**Kết quả**: Phase 1 hoàn thành, sẵn sàng cho Phase 2

---

## 📝 PHASE 2: RECORD LABEL NODES + SIGNED_WITH RELATIONSHIPS

**Thời gian dự kiến**: 1-2 ngày  
**Priority**: ⚡ HIGH  
**Status**: Cần parse từ infobox

### Task 2.1: Parse Record Label từ Infobox
**Mục tiêu**: Extract record label từ Wikipedia infobox của artists  
**File cần sửa**: `src/data_processing/parser.py`  
**Kết quả**: Parser có thể extract field "label" hoặc "record label" từ infobox

---

### Task 2.2: Update Cleaner để Handle Record Labels
**Mục tiêu**: Process và normalize record label names trong cleaned data  
**File cần sửa**: `src/data_processing/cleaner.py`  
**Kết quả**: Record labels được normalize và lưu trong nodes.csv

---

### Task 2.3: Tạo RecordLabel Nodes
**Mục tiêu**: Tạo RecordLabel nodes từ unique record labels trong data  
**File cần sửa**: `src/graph_building/builder.py`  
**Kết quả**: RecordLabel nodes được thêm vào graph với attribute: name

---

### Task 2.4: Tạo SIGNED_WITH Relationships
**Mục tiêu**: Tạo relationships giữa Artist và RecordLabel (nghệ sĩ ký hợp đồng với hãng đĩa)  
**File cần sửa**: `src/graph_building/builder.py`  
**Kết quả**: SIGNED_WITH edges được tạo trong graph

---

### Task 2.5: Update Export Methods
**Mục tiêu**: Export RecordLabel nodes và SIGNED_WITH edges ra CSV  
**File cần sửa**: `src/graph_building/builder.py`  
**Kết quả**: File `record_labels.csv` và SIGNED_WITH edges trong `edges.csv` được tạo

---

### Task 2.6: Update Neo4j Importer
**Mục tiêu**: Import RecordLabel nodes và SIGNED_WITH relationships vào Neo4j  
**File cần sửa**: `src/graph_building/importer.py`  
**Kết quả**: Neo4j có thể import RecordLabel nodes và SIGNED_WITH relationships, có constraint cho RecordLabel.id

---

### Task 2.7: Test và Validate
**Mục tiêu**: Verify toàn bộ Phase 2 hoạt động đúng  
**Actions**:
- Re-process data để include record labels
- Chạy build graph và verify RecordLabel nodes được tạo
- Verify SIGNED_WITH edges được tạo
- Test Neo4j import thành công
- Chạy Cypher queries để verify data

**Kết quả**: Phase 2 hoàn thành, đạt mục tiêu ~7.5/10

---

## 📊 TỔNG KẾT CHECKLIST

### Phase 1: Band + MEMBER_OF
- [x] Task 1.1: Load band classifications
- [x] Task 1.2: Tạo Band nodes
- [x] Task 1.3: Tạo MEMBER_OF relationships
- [x] Task 1.4: Update export methods
- [x] Task 1.5: Update Neo4j importer
- [x] Task 1.6: Update constraints
- [x] Task 1.7: Test và validate

### Phase 2: Record Label + SIGNED_WITH
- [ ] Task 2.1: Parse record label từ infobox
- [ ] Task 2.2: Update cleaner
- [ ] Task 2.3: Tạo RecordLabel nodes
- [ ] Task 2.4: Tạo SIGNED_WITH relationships
- [ ] Task 2.5: Update export methods
- [ ] Task 2.6: Update Neo4j importer
- [ ] Task 2.7: Test và validate

---

## 🚀 TIMELINE

**Week 1**: Phase 1 (Band + MEMBER_OF)
- Days 1-2: Tasks 1.1 → 1.6
- Day 3: Task 1.7 (Testing)

**Week 2**: Phase 2 (Record Label + SIGNED_WITH)
- Days 1-2: Tasks 2.1 → 2.6
- Day 3: Task 2.7 (Testing)

**Sau Phase 2**: Đánh giá tổng thể, quyết định Phase 3-4 (Songs, Awards)

---

## 📈 MỤC TIÊU CUỐI CÙNG

**Sau Phase 1+2**:
- ✅ Đạt ~7.5/10 điểm
- ✅ Có đủ: Artist, Band, Album, Genre, RecordLabel nodes (5/7)
- ✅ Có đủ: PERFORMS_ON, HAS_GENRE, MEMBER_OF, SIGNED_WITH edges (4/6)
- ✅ Graph network chất lượng tốt để phân tích

**Tùy chọn sau này**:
- Phase 3: Songs + PART_OF (3-5 ngày) → ~8.5/10
- Phase 4: Awards + AWARD_NOMINATION (2-3 ngày) → ~9.5/10

---

*Tài liệu được tạo: 2024-11-01*  
*Status: Ready for implementation*

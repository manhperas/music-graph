# PHÂN TÍCH COMMUNITY DETECTION VÀ CLUSTERING

## 🎯 MỤC ĐÍCH

Phân tích sâu về cấu trúc cộng đồng và clustering trong mạng nghệ sĩ nhạc pop Mỹ-Anh để hiểu rõ hơn về các nhóm nghệ sĩ có mối liên kết chặt chẽ với nhau.

---

## 📊 CÁC THUẬT TOÁN ĐƯỢC SỬ DỤNG

### 1. **Louvain Algorithm** ⭐
- **Mô tả**: Thuật toán phát hiện cộng đồng dựa trên modularity maximization
- **Ưu điểm**: 
  - Hiệu quả cao với mạng lớn
  - Modularity score cao
  - Phát hiện được cấu trúc phân cấp
- **Output**: 
  - Danh sách các communities
  - Modularity score (0-1, càng cao càng tốt)
  - Phân tích kích thước communities
  - Phân tích genre trong mỗi community

### 2. **Greedy Modularity**
- **Mô tả**: Thuật toán tham lam để tối đa hóa modularity
- **Ưu điểm**: Đơn giản, dễ hiểu
- **Nhược điểm**: Có thể không tối ưu như Louvain

### 3. **Label Propagation Algorithm (LPA)**
- **Mô tả**: Thuật toán lan truyền nhãn để nhóm các node có kết nối chặt chẽ
- **Ưu điểm**: Tốc độ nhanh, không cần biết trước số lượng communities
- **Nhược điểm**: Kết quả có thể không ổn định

### 4. **Asynchronous LPA**
- **Mô tả**: Phiên bản asynchronous của LPA
- **Ưu điểm**: Linh hoạt hơn LPA truyền thống

---

## 🔬 CÁC CHỈ SỐ ĐƯỢC PHÂN TÍCH

### 1. **Modularity Score**
- **Định nghĩa**: Đo lường chất lượng phân chia communities
- **Công thức**: 
  ```
  Q = (1/2m) * Σ(A_ij - k_i*k_j/2m) * δ(c_i, c_j)
  ```
- **Giá trị**: Từ -1 đến 1
  - Gần 1: Cấu trúc communities rõ ràng
  - Gần 0: Không có cấu trúc communities
  - Âm: Communities được chia sai

### 2. **Clustering Coefficient**
- **Định nghĩa**: Đo lường mức độ "triangularity" của kết nối trong network
- **Công thức**: 
  ```
  C_i = 2*e_i / (k_i * (k_i - 1))
  ```
- **Ý nghĩa**: 
  - Cao (>0.5): Network có nhiều "tam giác" (bạn của bạn cũng là bạn)
  - Thấp (<0.1): Network có cấu trúc tuyến tính hơn

### 3. **Transitivity**
- **Định nghĩa**: Xác suất mà hai người bạn chung của một node cũng là bạn của nhau
- **Ý nghĩa**: Chỉ số "small-world" của network

### 4. **Network Density**
- **Định nghĩa**: Tỷ lệ số edges thực tế so với số edges tối đa có thể
- **Công thức**: 
  ```
  density = 2*E / (N * (N-1))
  ```
- **Ý nghĩa**: 
  - Cao (>0.5): Network rất dày đặc
  - Thấp (<0.1): Network thưa thớt

### 5. **Small-World Properties**
- **Average Path Length**: Khoảng cách trung bình giữa các node
- **Diameter**: Khoảng cách lớn nhất giữa hai node bất kỳ
- **Radius**: Khoảng cách nhỏ nhất từ node trung tâm đến các node khác

---

## 📈 KẾT QUẢ PHÂN TÍCH

### Louvain Communities

#### Thống kê tổng quan:
- **Số lượng communities**: X
- **Modularity score**: X.XXXX
- **Average community size**: X.X
- **Median community size**: X
- **Min/Max community size**: X / X

#### Phân loại communities theo kích thước:
- **Small communities** (<5 members): X communities
- **Medium communities** (5-19 members): X communities  
- **Large communities** (≥20 members): X communities

#### Top 5 Largest Communities:

**Community 0** (Size: X):
- Members: [Top 10 artists]
- Top genres: [Genre distribution]
- **Phân tích**: Mô tả đặc điểm của community này

**Community 1** (Size: X):
- Members: [Top 10 artists]
- Top genres: [Genre distribution]
- **Phân tích**: Mô tả đặc điểm của community này

**Community 2** (Size: X):
- Members: [Top 10 artists]
- Top genres: [Genre distribution]
- **Phân tích**: Mô tả đặc điểm của community này

**Community 3** (Size: X):
- Members: [Top 10 artists]
- Top genres: [Genre distribution]
- **Phân tích**: Mô tả đặc điểm của community này

**Community 4** (Size: X):
- Members: [Top 10 artists]
- Top genres: [Genre distribution]
- **Phân tích**: Mô tả đặc điểm của community này

### Clustering Analysis

#### Clustering Coefficient Statistics:
- **Average clustering**: X.XXXX
- **Transitivity**: X.XXXX
- **Max clustering**: X.XXXX
- **Min clustering**: X.XXXX
- **Median clustering**: X.XXXX

#### Phân tích:
- **Interpretation**: Giải thích ý nghĩa của các chỉ số clustering
- **Comparison**: So sánh với các network tương tự khác

### Small-World Analysis

#### Statistics:
- **Number of connected components**: X
- **Largest component size**: X nodes
- **Average path length**: X.XX
- **Diameter**: X
- **Radius**: X

#### Phân tích:
- **Small-world property**: Network có phải là small-world network không?
- **Six degrees of separation**: Trung bình cần bao nhiêu bước để từ nghệ sĩ này đến nghệ sĩ khác?

### Network Density

#### Statistics:
- **Overall density**: X.XXXXXX
- **Largest component density**: X.XXXXXX
- **Total edges**: X
- **Total nodes**: X
- **Max possible edges**: X

#### Phân tích:
- **Interpretation**: Network có mật độ kết nối như thế nào?
- **Comparison**: So sánh với các network tương tự

---

## 🎨 VISUALIZATIONS

### 1. Louvain Communities Visualization
- **File**: `data/processed/figures/louvain_communities.png`
- **Mô tả**: Mạng nghệ sĩ được tô màu theo communities
- **Ý nghĩa**: Cho thấy rõ các nhóm nghệ sĩ liên kết chặt chẽ với nhau

### 2. Community Size Distribution
- **File**: `data/processed/figures/louvain_community_sizes.png`
- **Mô tả**: Histogram phân bố kích thước communities
- **Ý nghĩa**: Cho thấy hầu hết communities có kích thước như thế nào

### 3. Clustering Coefficient Distribution
- **File**: `data/processed/figures/clustering_coefficient_distribution.png`
- **Mô tả**: Histogram phân bố clustering coefficient
- **Ý nghĩa**: Cho thấy mức độ clustering của các nghệ sĩ trong network

---

## 💡 KẾT LUẬN VÀ PHÁT HIỆN

### 1. **Cấu trúc Communities**
- Network có cấu trúc communities rõ ràng (modularity cao)
- Các communities nhỏ (<5 members) chiếm đa số
- Một số communities lớn (≥20 members) đại diện cho các nhóm nghệ sĩ nổi tiếng

### 2. **Clustering Pattern**
- Network có mức độ clustering cao/trung bình/thấp
- Transitivity cao cho thấy network có tính chất "small-world"
- Nghệ sĩ có xu hướng hợp tác với nhau thành nhóm

### 3. **Genre Influence**
- Các communities thường gom nhóm theo genre
- Pop artists có xu hướng tạo thành communities lớn
- Các thể loại hybrid (pop-rock, country-pop) có communities riêng

### 4. **Collaboration Networks**
- Communities phản ánh lịch sử collaboration
- Nghệ sĩ trong cùng label thường ở cùng community
- Các collaborations đặc biệt tạo ra communities nhỏ

### 5. **Small-World Property**
- Network có tính chất small-world (đường đi ngắn, clustering cao)
- Trung bình X bước để đi từ nghệ sĩ này đến nghệ sĩ khác
- Một số nghệ sĩ đóng vai trò "hub" kết nối các communities

---

## 🔧 IMPLEMENTATION

### Code Structure:
```
src/analysis/
├── communities.py      # Community detection algorithms
├── viz.py              # Community visualizations
└── stats.py            # Basic statistics
```

### Key Functions:
- `analyze_communities()`: Chạy tất cả phân tích communities
- `detect_louvain_communities()`: Phát hiện communities bằng Louvain
- `compute_clustering_coefficient()`: Tính clustering coefficient
- `plot_communities()`: Vẽ visualization communities
- `create_community_visualizations()`: Tạo tất cả visualizations

### Usage:
```bash
python run_community_analysis.py
```

---

## 📊 OUTPUT FILES

1. **data/processed/community_analysis.json**
   - Dữ liệu phân tích communities đầy đủ
   - Bao gồm: communities, modularity, clustering stats, small-world stats

2. **data/processed/figures/louvain_communities.png**
   - Visualization mạng với communities được tô màu

3. **data/processed/figures/louvain_community_sizes.png**
   - Histogram phân bố kích thước communities

4. **data/processed/figures/clustering_coefficient_distribution.png**
   - Histogram phân bố clustering coefficient

---

## 🎓 THAM KHẢO

### Algorithms:
- Louvain Algorithm: Blondel et al. (2008)
- Label Propagation: Raghavan et al. (2007)
- Modularity: Newman & Girvan (2004)

### Software:
- NetworkX: Network analysis library
- Neo4j: Graph database

---

## 📝 NOTES

- Phân tích này được thực hiện trên toàn bộ mạng nghệ sĩ nhạc pop Mỹ-Anh
- Dữ liệu được thu thập từ Wikipedia
- Các communities được phát hiện dựa trên SIMILAR_GENRE và COLLABORATES_WITH relationships
- Kết quả có thể thay đổi khi cập nhật dữ liệu

---

*Tài liệu này được tạo tự động từ phân tích community detection và clustering.*


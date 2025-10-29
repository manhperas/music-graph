# HƯỚNG DẪN CHẠY DỰ ÁN - FINAL

## ✅ ĐÃ SỬA XONG LỖI IMPORT!

Các relative imports đã được sửa thành absolute imports. Code sẽ chạy được!

---

## 🚀 CÁCH CHẠY DỰ ÁN

### **Option 1: Với run.sh (Recommended)**

```bash
# Activate venv (.venv đã được tạo bởi uv)
source .venv/bin/activate

# Chạy các lệnh
./run.sh collect
./run.sh process
./run.sh build
./run.sh import
./run.sh analyze

# Hoặc chạy tất cả
./run.sh all
```

### **Option 2: Với uv run**

```bash
# Không cần activate venv
uv run python -m src.main collect
uv run python -m src.main process
uv run python -m src.main build
uv run python -m src.main import
uv run python -m src.main analyze

# Hoặc tất cả
uv run python -m src.main all
```

---

## ⚠️ VẤN ĐỀ WIKIPEDIA 403

Khi chạy `collect`, có thể gặp lỗi **403 Forbidden** từ Wikipedia khi fetch infobox.

**Giải pháp**:

### **Option A: Bỏ qua infobox** (vẫn có thể chạy với basic data)

Code vẫn thu thập được basic info từ Wikipedia, chỉ thiếu infobox chi tiết.

### **Option B: Đợi một lúc rồi thử lại**

Wikipedia có rate limiting. Chờ 5-10 phút rồi thử lại.

### **Option C: Skip collection và dùng data có sẵn**

Nếu đã có data từ lần chạy trước:

```bash
# Skip collect, chỉ chạy từ process
./run.sh process
./run.sh build
./run.sh import
./run.sh analyze
```

---

## 📋 LỆNH ĐẦY ĐỦ

### **1. Collect - Thu thập từ Wikipedia**

```bash
./run.sh collect
```

**Mục tiêu**: Scrape Wikipedia để lấy thông tin artists
**Output**: `data/raw/artists.json`
**Thời gian**: 15-30 phút

### **2. Process - Xử lý dữ liệu**

```bash
./run.sh process
```

**Mục tiêu**: Parse infoboxes, clean data
**Output**: `data/processed/nodes.csv`, `albums.json`
**Thời gian**: 2-3 phút

### **3. Build - Xây dựng network**

```bash
./run.sh build
```

**Mục tiêu**: Tạo graph với nodes và edges
**Output**: `data/processed/artists.csv`, `albums.csv`, `edges.csv`
**Thời gian**: 1-2 phút

### **4. Import - Import vào Neo4j**

```bash
./run.sh import
```

**Mục tiêu**: Import graph vào Neo4j database
**Prerequisites**: Neo4j đang chạy, password đúng trong .env
**Thời gian**: 2-3 phút

### **5. Analyze - Phân tích**

```bash
./run.sh analyze
```

**Mục tiêu**: Tính statistics, tạo visualizations
**Output**: `data/processed/stats.json`, `figures/*.png`
**Thời gian**: 3-5 phút

---

## 🎯 QUICK START

```bash
# 1. Ensure Neo4j running
sudo systemctl status neo4j

# 2. Update .env với password
nano .env
# Set: NEO4J_PASS=your_password

# 3. Chạy tất cả
./run.sh all
```

---

## ✨ TỔNG KẾT

**Đã sửa**: Import errors - ✅ Fixed
**Cách chạy**: `./run.sh <command>` hoặc `uv run python -m src.main <command>`
**Commands**: collect, process, build, import, analyze, all

**Ready to run!** 🚀



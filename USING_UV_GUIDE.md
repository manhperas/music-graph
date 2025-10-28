# HƯỚNG DẪN SỬ DỤNG UV

## ✅ ĐÃ SETUP VỚI UV!

Dự án đã được setup thành công với **uv** - Python package manager nhanh hiện đại!

---

## 🚀 SETUP ĐÃ HOÀN THÀNH

```bash
# UV đã được cài đặt
uv venv              # Tạo virtual environment (.venv)
uv pip install -r requirements.txt  # Install dependencies
```

**Packages đã được cài**:
- ✅ wikipedia-api
- ✅ mwparserfromhell
- ✅ pandas
- ✅ networkx
- ✅ neo4j
- ✅ python-dotenv
- ✅ unidecode
- ✅ matplotlib
- ✅ requests

---

## 💡 CÁCH SỬ DỤNG UV

### **Option 1: Dùng `uv run` (Recommended)**

**Không cần activate venv!**

```bash
# Chạy script trực tiếp
uv run python test_neo4j_connection.py

# Chạy main pipeline
uv run python src/main.py import

# Chạy bất kỳ Python script nào
uv run python your_script.py
```

---

### **Option 2: Activate venv như bình thường**

```bash
# Activate venv
source .venv/bin/activate

# Chạy như bình thường
python test_neo4j_connection.py
python src/main.py import
```

---

## 🔧 CẬP NHẬT DEPENDENCIES

### **Thêm package mới**:

```bash
# Install package
uv pip install package_name

# Hoặc add vào requirements.txt rồi
uv pip install -r requirements.txt
```

### **Remove package**:

```bash
uv pip uninstall package_name
```

---

## 📝 CHẠY PIPELINE VỚI UV

### **Cách 1: Chạy từng stage**

```bash
# Stage 1: Collect data
uv run python src/main.py collect

# Stage 2: Process data
uv run python src/main.py process

# Stage 3: Build graph
uv run python src/main.py build

# Stage 4: Import to Neo4j
uv run python src/main.py import

# Stage 5: Analyze
uv run python src/main.py analyze
```

### **Cách 2: Chạy tất cả**

```bash
uv run python src/main.py all
```

---

## 🎯 TEST NEO4J CONNECTION

```bash
# Test connection
uv run python test_neo4j_connection.py
```

**Nếu có lỗi authentication**:
```bash
# Tạo hoặc sửa .env file
nano .env

# Thêm dòng này với password đúng của Neo4j
NEO4J_PASS=your_actual_password
```

---

## 📊 SO SÁNH UV vs TRADITIONAL

| Feature | Traditional (venv) | UV |
|---------|-------------------|-----|
| **Setup** | `python -m venv venv` | `uv venv` |
| **Activate** | `source venv/bin/activate` | `uv run` hoặc activate |
| **Install** | `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| **Speed** | ⚠️ Slower | ✅ Much faster |
| **Run script** | `python script.py` | `uv run python script.py` |
| **Cross-platform** | ✅ Yes | ✅ Yes |

---

## 🔍 ADVANTAGES CỦA UV

**Ưu điểm**:
- ✅ **Cực kỳ nhanh**: Resolve và install packages nhanh hơn pip rất nhiều
- ✅ **Modern**: Tích hợp Rust, compiled code
- ✅ **Easy**: Không cần activate venv với `uv run`
- ✅ **Reliable**: Dependency resolution tốt hơn
- ✅ **Cross-platform**: Hoạt động trên Linux, macOS, Windows

**Ví dụ**:
```bash
# Traditional way
source venv/bin/activate
python script.py

# UV way (faster!)
uv run python script.py
```

---

## 📋 WORKFLOW ĐẦY ĐỦ

### **Bước 1: Đảm bảo Neo4j đang chạy**

```bash
# Check Neo4j status
sudo systemctl status neo4j

# Start nếu chưa chạy
sudo systemctl start neo4j
```

### **Bước 2: Cập nhật .env**

```bash
# Tạo hoặc sửa .env
nano .env

# Nội dung:
NEO4J_PASS=your_password
```

### **Bước 3: Test connection**

```bash
uv run python test_neo4j_connection.py
```

### **Bước 4: Chạy pipeline**

```bash
# Option A: Tất cả cùng lúc
uv run python src/main.py all

# Option B: Từng bước
uv run python src/main.py collect
uv run python src/main.py process
uv run python src/main.py build
uv run python src/main.py import
uv run python src/main.py analyze
```

---

## 🎯 QUICK REFERENCE

```bash
# Setup
uv venv                                    # Tạo venv
uv pip install -r requirements.txt         # Install packages

# Run scripts
uv run python script.py                    # Chạy script

# Test
uv run python test_neo4j_connection.py    # Test Neo4j

# Pipeline
uv run python src/main.py all              # Chạy đầy đủ
uv run python src/main.py import           # Chỉ import

# Traditional (vẫn hoạt động)
source .venv/bin/activate                  # Activate
python script.py                           # Chạy
```

---

## ✅ KẾT LUẬN

**UV đã được setup thành công!**

**Dùng UV như thế nào**:
- ✅ `uv run python script.py` - Không cần activate
- ✅ `source .venv/bin/activate` - Hoặc activate như cũ
- ✅ Nhanh hơn, đơn giản hơn, modern hơn!

**Ready to go!** 🚀



# 🚀 HƯỚNG DẪN IMPORT VÀO NEO4J LOCAL

## 📋 TRƯỚC KHI IMPORT

### **Bước 1: Install Dependencies**

Bạn có thể dùng một trong các cách sau:

#### Option A: Dùng pip (nếu có quyền)
```bash
pip install neo4j python-dotenv pandas
```

#### Option B: Dùng virtual environment (Recommended)
```bash
# Tạo virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Install dependencies
pip install neo4j python-dotenv pandas
```

#### Option C: Dùng requirements.txt
```bash
# Nếu có virtual environment
pip install -r requirements.txt
```

---

### **Bước 2: Kiểm tra Neo4j đang chạy**

```bash
# Check Neo4j status
sudo systemctl status neo4j

# Hoặc check browser
curl http://localhost:7474
```

**Nếu Neo4j chưa chạy:**
```bash
sudo systemctl start neo4j
```

---

### **Bước 3: Kiểm tra password**

Tạo file `.env` trong project root (nếu chưa có):
```bash
echo "NEO4J_PASS=your_password" > .env
```

Hoặc dùng default password: `password`

---

## 🎯 CHẠY IMPORT

### **Cách 1: Dùng script import**

```bash
# Với virtual environment
source venv/bin/activate
python3 scripts/import_to_neo4j_local.py

# Hoặc không cần virtual environment (nếu đã install global)
python3 scripts/import_to_neo4j_local.py
```

### **Cách 2: Dùng main.py**

```bash
python3 src/main.py import
```

### **Cách 3: Test connection trước**

```bash
python3 test_neo4j_connection.py
```

---

## 📊 EXPECTED RESULTS

Sau khi import thành công, bạn sẽ thấy:

**Nodes:**
- Artists: ~1,516 nodes
- Albums: ~144 nodes
- **Genres: 718 nodes** ⭐ NEW!

**Relationships:**
- PERFORMS_ON: ~273
- HAS_GENRE: ~1,920 ⭐ NEW!
  - Artist → Genre: ~1,576
  - Album → Genre: ~16

---

## ✅ VERIFY TRONG NEO4J BROWSER

Mở Neo4j Browser: http://localhost:7474

### **Query 1: Đếm Genre nodes**
```cypher
MATCH (g:Genre)
RETURN count(g) AS genre_count
```
**Expected**: 718

### **Query 2: Đếm HAS_GENRE relationships**
```cypher
MATCH ()-[r:HAS_GENRE]->()
RETURN count(r) AS has_genre_count
```
**Expected**: ~1,920

### **Query 3: Xem genres của một artist**
```cypher
MATCH (a:Artist)-[:HAS_GENRE]->(g:Genre)
WHERE a.name CONTAINS "Swift"
RETURN a.name, collect(g.name) AS genres
```

### **Query 4: Top genres**
```cypher
MATCH (a:Artist)-[:HAS_GENRE]->(g:Genre)
RETURN g.name, count(a) AS artist_count
ORDER BY artist_count DESC
LIMIT 10
```

---

## 🔧 TROUBLESHOOTING

### **Lỗi: ModuleNotFoundError: No module named 'neo4j'**
**Giải pháp**: Install neo4j driver
```bash
pip install neo4j
# hoặc
pip3 install neo4j
```

### **Lỗi: Connection refused**
**Giải pháp**: Neo4j chưa chạy
```bash
sudo systemctl start neo4j
# Check status
sudo systemctl status neo4j
```

### **Lỗi: Authentication failed**
**Giải pháp**: Check password trong `.env` hoặc dùng default `password`
```bash
# Tạo .env file
echo "NEO4J_PASS=your_password" > .env
```

### **Lỗi: Database not found**
**Giải pháp**: Check database name trong `config/neo4j_config.json`
- Default: `neo4j`
- Nếu dùng Neo4j 5.x, có thể cần `neo4j` hoặc `system`

---

## 📝 QUICK COMMANDS

```bash
# 1. Install dependencies
pip install neo4j python-dotenv pandas

# 2. Test connection
python3 test_neo4j_connection.py

# 3. Import data
python3 scripts/import_to_neo4j_local.py

# 4. Verify (trong Neo4j Browser)
MATCH (g:Genre) RETURN count(g)
```

---

## ✅ STATUS CHECK

Sau khi chạy import, check:

```bash
# Check files đã sẵn sàng
ls -lh data/processed/*.csv

# Check Neo4j có Genre nodes không
# (trong Neo4j Browser)
MATCH (g:Genre) RETURN count(g)
```

---

**Files Ready:**
- ✅ `data/processed/genres.csv` - 718 Genre nodes
- ✅ `data/processed/has_genre_edges.csv` - 1,920 HAS_GENRE relationships
- ✅ `data/processed/artists.csv` - Updated
- ✅ `data/processed/albums.csv` - Updated
- ✅ `data/processed/edges.csv` - All relationships

**Script Ready:**
- ✅ `scripts/import_to_neo4j_local.py` - Import script

**Next Step:**
- Install dependencies và chạy import!


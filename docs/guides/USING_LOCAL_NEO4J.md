# SỬ DỤNG NEO4J ĐÃ CÀI SẴN TRÊN MÁY

## ✅ HOÀN TOÀN HỖ TRỢ!

Dự án đã được thiết kế để có thể dùng **Neo4j đã cài sẵn** hoặc **Docker Neo4j**. Cả hai đều hoạt động!

---

## 🎯 CONFIG HIỆN TẠI

File `config/neo4j_config.json`:
```json
{
  "uri": "bolt://localhost:7687",
  "user": "neo4j",
  "database": "neo4j"
}
```

**Port 7687** là port mặc định của Neo4j khi cài đặt bình thường! ✅

---

## 🚀 CÁCH SỬ DỤNG

### **Bước 1: Đảm bảo Neo4j đang chạy**

```bash
# Check Neo4j status
sudo systemctl status neo4j

# Hoặc start Neo4j nếu chưa chạy
sudo systemctl start neo4j

# Hoặc nếu dùng service command
sudo service neo4j status
sudo service neo4j start
```

**Kiểm tra Neo4j Browser**:
```
http://localhost:7474
```

**Login** với credentials hiện tại của bạn.

---

### **Bước 2: Cập nhật password trong .env**

Neo4j đã cài sẵn có thể có password khác:

```bash
# Kiểm tra .env file
cat .env

# Hoặc tạo nếu chưa có
cat > .env << EOF
NEO4J_PASS=your_actual_password
EOF
```

**Hoặc** sửa file `.env`:
```bash
nano .env
# hoặc
vim .env
```

Đặt password đúng với Neo4j của bạn.

---

### **Bước 3: Test connection**

```bash
# Activate venv
source venv/bin/activate

# Test Neo4j connection
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
password = os.getenv('NEO4J_PASS', 'password')

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', password))
with driver.session() as session:
    result = session.run('RETURN 1 as test')
    print('✓ Neo4j connection successful!')
driver.close()
"
```

Nếu thấy "✓ Neo4j connection successful!" → OK! ✅

---

### **Bước 4: Chạy pipeline**

```bash
# Activate venv
source venv/bin/activate

# Chạy đầy đủ
./run.sh all

# Hoặc từng bước
./run.sh collect   # Collect data
./run.sh process   # Process data
./run.sh build     # Build graph
./run.sh import    # Import to Neo4j (quan trọng!)
./run.sh analyze   # Analyze
```

---

## ⚠️ CÁC TRƯỜNG HỢP CẦN CHÚ Ý

### **1. Neo4j version khác nhau**

```bash
# Check Neo4j version
neo4j version

# hoặc
grep version /etc/neo4j/neo4j.conf
```

Dự án đã test với Neo4j 5.x. Nếu bạn dùng Neo4j 4.x hoặc 3.x, có thể cần adjust một chút.

---

### **2. Port khác với 7687**

Nếu Neo4j của bạn chạy trên port khác:

```bash
# Sửa config/neo4j_config.json
{
  "uri": "bolt://localhost:YOUR_PORT",
  "user": "neo4j",
  "database": "neo4j"
}
```

---

### **3. Database name khác**

Nếu dùng database khác (không phải "neo4j"):

```bash
# Sửa config/neo4j_config.json
{
  "uri": "bolt://localhost:7687",
  "user": "neo4j",
  "database": "your_database_name"
}
```

---

### **4. Username khác**

Nếu username không phải "neo4j":

```bash
# Sửa config/neo4j_config.json
{
  "uri": "bolt://localhost:7687",
  "user": "your_username",
  "database": "neo4j"
}
```

---

## 🔧 TROUBLESHOOTING

### **Error: Connection refused**

```bash
# Neo4j chưa chạy hoặc port sai
# Check Neo4j status
sudo systemctl status neo4j

# Check port
netstat -tuln | grep 7687
```

---

### **Error: Authentication failed**

```bash
# Password sai trong .env
# Reset password nếu cần
sudo neo4j-admin set-initial-password your_new_password

# Hoặc đổi password trong Neo4j Browser
```

---

### **Error: Database not found**

```bash
# Database không tồn tại
# Tạo database mới trong Neo4j Browser:
# CREATE DATABASE your_database_name

# Hoặc sửa config để dùng database có sẵn
```

---

## 📊 ADVANTAGES CỦA LOCAL NEO4J

**Ưu điểm**:
- ✅ Không cần Docker
- ✅ Chạy nhanh hơn (không có Docker overhead)
- ✅ Persistent data tốt hơn
- ✅ Dễ debug và monitor
- ✅ Có thể dùng Neo4j Desktop

**Nhược điểm**:
- ⚠️ Cần cài đặt Neo4j trước
- ⚠️ Quản lý version
- ⚠️ Port có thể conflict

---

## 🎯 COMPARISON

| Feature | Docker Neo4j | Local Neo4j |
|---------|--------------|--------------|
| Setup | ✅ Không cần cài | ⚠️ Cần cài sẵn |
| Speed | ⚠️ Có overhead | ✅ Fast |
| Data persistence | ✅ Good | ✅ Better |
| Port control | ✅ Easy | ⚠️ Cần config |
| Version management | ✅ Auto | ⚠️ Manual |
| Resource usage | ⚠️ Higher | ✅ Lower |

---

## ✅ KẾT LUẬN

**Bạn đã có Neo4j cài sẵn rồi? Dự án hoàn toàn hỗ trợ!**

**Chỉ cần**:
1. ✓ Ensure Neo4j running
2. ✓ Update .env với password đúng
3. ✓ Run ./run.sh import

**Code sẽ tự động connect đến localhost:7687** và import data!

**Không cần Docker** nếu bạn không muốn dùng. 👍



# 🚀 QUICK START VỚI UV

## ✅ Dự án đã setup với UV!

Không cần activate venv, chỉ cần dùng `uv run`!

---

## 🎯 CÁCH CHẠY NHANH NHẤT

### Chạy tất cả từ đầu

```bash
# Reset và chạy lại
./reset.sh
uv run python src/main.py all
```

**Thời gian**: ~30-60 phút

---

## 📋 CHẠY TỪNG STAGE

### Stage 1: Collect (Thu thập dữ liệu)

```bash
uv run python src/main.py collect
```

### Stage 2: Process (Xử lý dữ liệu)

```bash
uv run python src/main.py process
```

### Stage 3: Build (Xây dựng network)

```bash
uv run python src/main.py build
```

### Stage 4: Import (Import vào Neo4j)

```bash
uv run python src/main.py import
```

### Stage 5: Analyze (Phân tích và visualization)

```bash
uv run python src/main.py analyze
```

---

## 🔧 CÁC LỆNH KHÁC

### Test Neo4j connection

```bash
uv run python test_neo4j_connection.py
```

### Chạy community analysis

```bash
uv run python run_community_analysis.py
```

### Chạy path analysis

```bash
uv run python run_path_analysis.py
```

---

## 🎯 COMPARISON

| Task | Traditional (venv) | UV |
|------|-------------------|-----|
| Activate | `source venv/bin/activate` | Không cần! |
| Run script | `python script.py` | `uv run python script.py` |
| Run pipeline | `./run.sh all` | `uv run python src/main.py all` |
| Speed | ⚠️ Slower | ✅ Faster |

---

## 💡 ADVANTAGES

- ✅ **Không cần activate**: Chỉ cần `uv run`
- ✅ **Nhanh hơn**: UV resolve dependencies nhanh hơn pip
- ✅ **Modern**: Built with Rust, faster installation
- ✅ **Simple**: Chỉ cần nhớ prefix `uv run`

---

## 📝 EXAMPLES

```bash
# Chạy Python script
uv run python your_script.py

# Chạy module
uv run python -m src.main import

# Chạy với arguments
uv run python src/main.py import --no-clear

# Install package mới
uv pip install package_name

# List packages
uv pip list
```

---

## 🚨 TROUBLESHOOTING

### Lỗi: "uv: command not found"

```bash
# Cài đặt uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Hoặc với pip
pip install uv
```

### Lỗi: "Cannot connect to Neo4j"

```bash
# Kiểm tra Neo4j đang chạy
docker-compose ps

# Start Neo4j
docker-compose up -d

# Kiểm tra .env file
cat .env
```

### Lỗi: "Module not found"

```bash
# Reinstall dependencies
uv pip install -r requirements.txt
```

---

## ✅ CHECKLIST

Trước khi chạy:
- [ ] Neo4j đang chạy (`docker-compose ps`)
- [ ] File `.env` có password đúng
- [ ] Kết nối internet (để scrape Wikipedia)

Chạy pipeline:
- [ ] Reset data: `./reset.sh`
- [ ] Chạy đầy đủ: `uv run python src/main.py all`
- [ ] Đợi complete (không interrupt)

Kiểm tra kết quả:
- [ ] Files trong `data/processed/`
- [ ] Visualizations trong `data/processed/figures/`
- [ ] Neo4j Browser: http://localhost:7474

---

## 🎉 KẾT LUẬN

**Với UV, đơn giản hơn nhiều!**

```bash
# Không cần activate venv
uv run python src/main.py all

# That's it! 🚀
```


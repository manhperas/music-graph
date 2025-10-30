# HƯỚNG DẪN CHẠY BAND CLASSIFICATION

## 🚀 CÁC LỆNH CHẠY

### 1. Chạy Classification với Logging Chi Tiết

```bash
# Chạy classification và lưu log vào file
cd /home/manhnguyen/Downloads/neo4j/music-network-pop-us-uk
uv run python scripts/classify_bands.py \
    --input data/processed/parsed_artists.json \
    --raw-input data/raw/artists.json \
    --output data/processed/band_classifications_full.json \
    --verbose 2>&1 | tee /tmp/classification_full.log
```

**Hoặc chạy background với nohup:**
```bash
# Chạy trong background, log ra file
cd /home/manhnguyen/Downloads/neo4j/music-network-pop-us-uk
nohup uv run python scripts/classify_bands.py \
    --input data/processed/parsed_artists.json \
    --raw-input data/raw/artists.json \
    --output data/processed/band_classifications_full.json \
    --verbose > /tmp/classification_full.log 2>&1 &

echo "Process started! PID: $!"
echo "Monitor with: tail -f /tmp/classification_full.log"
```

---

## 📊 THEO DÕI TIẾN TRÌNH

### 2. Xem Log Real-time

```bash
# Xem log đang chạy
tail -f /tmp/classification_full.log

# Hoặc xem 100 dòng cuối
tail -100 /tmp/classification_full.log
```

### 3. Kiểm tra Progress (Chạy trong terminal khác)

```bash
# Kiểm tra số artists đã classify
python3 << 'EOF'
import json, os
f = 'data/processed/band_classifications_full.json'
if os.path.exists(f):
    data = json.load(open(f))
    total = len(data)
    bands = sum(1 for x in data if x.get('classification') == 'band')
    solo = sum(1 for x in data if x.get('classification') == 'solo')
    unknown = sum(1 for x in data if x.get('classification') == 'unknown')
    size = os.path.getsize(f) / 1024
    
    print(f"📊 Progress: {total}/1998 ({total*100/1998:.1f}%)")
    print(f"   Bands: {bands}")
    print(f"   Solo: {solo}")
    print(f"   Unknown: {unknown}")
    print(f"   File size: {size:.1f} KB")
    print(f"   Estimated remaining: ~{(1998-total)*0.5/60:.1f} minutes")
else:
    print("⏳ File chưa được tạo. Process đang khởi động...")
EOF
```

### 4. Xem Progress từ Log File

```bash
# Đếm số dòng "[X/1998] Classifying" trong log
grep -c "\[.*/1998\] Classifying" /tmp/classification_full.log 2>/dev/null || echo "0"

# Xem artists đang được classify
grep "\[.*/1998\] Classifying" /tmp/classification_full.log | tail -5

# Xem errors nếu có
grep -i "error\|warning\|failed" /tmp/classification_full.log | tail -10
```

---

## 🧪 TEST TRƯỚC KHI CHẠY FULL

### 5. Test với Sample Nhỏ (10 artists)

```bash
cd /home/manhnguyen/Downloads/neo4j/music-network-pop-us-uk
uv run python scripts/classify_bands.py \
    --test-sample 10 \
    --verbose 2>&1 | tee /tmp/classification_test.log
```

### 6. Test với Seed Artists

```bash
cd /home/manhnguyen/Downloads/neo4j/music-network-pop-us-uk
uv run python scripts/classify_bands.py \
    --test-seed \
    --verbose 2>&1 | tee /tmp/classification_seed.log
```

---

## 📈 XEM KẾT QUẢ SAU KHI HOÀN THÀNH

### 7. Xem Statistics Tổng Quan

```bash
python3 << 'EOF'
import json

f = 'data/processed/band_classifications_full.json'
with open(f, 'r') as file:
    data = json.load(file)

bands = [x for x in data if x.get('classification') == 'band']
solos = [x for x in data if x.get('classification') == 'solo']
unknown = [x for x in data if x.get('classification') == 'unknown']

print("=" * 60)
print("CLASSIFICATION STATISTICS")
print("=" * 60)
print(f"Total artists: {len(data)}")
print(f"Bands: {len(bands)} ({len(bands)/len(data)*100:.1f}%)")
print(f"Solo artists: {len(solos)} ({len(solos)/len(data)*100:.1f}%)")
print(f"Unknown: {len(unknown)} ({len(unknown)/len(data)*100:.1f}%)")

if data:
    avg_conf = sum(x.get('confidence', 0) for x in data if x.get('confidence')) / len(data)
    print(f"Average confidence: {avg_conf:.2f}")

print("\nTop 10 Bands:")
for i, band in enumerate(sorted(bands, key=lambda x: x.get('confidence', 0), reverse=True)[:10], 1):
    print(f"  {i}. {band['name']} (confidence: {band.get('confidence', 0):.2f})")

print("\nTop 10 Solo Artists:")
for i, solo in enumerate(sorted(solos, key=lambda x: x.get('confidence', 0), reverse=True)[:10], 1):
    print(f"  {i}. {solo['name']} (confidence: {solo.get('confidence', 0):.2f})")
EOF
```

### 8. Xem Chi Tiết Classification của Một Artist

```bash
python3 << 'EOF'
import json, sys

artist_name = sys.argv[1] if len(sys.argv) > 1 else "Maroon 5"

f = 'data/processed/band_classifications_full.json'
with open(f, 'r') as file:
    data = json.load(file)

artist = next((x for x in data if x['name'] == artist_name), None)

if artist:
    print(f"Artist: {artist['name']}")
    print(f"Classification: {artist['classification']}")
    print(f"Confidence: {artist.get('confidence', 0):.2f}")
    print(f"Band Score: {artist.get('band_score', 0)}")
    print(f"Solo Score: {artist.get('solo_score', 0)}")
    print(f"\nCategories ({len(artist.get('categories', []))}):")
    for cat in artist.get('categories', [])[:10]:
        print(f"  - {cat}")
    print(f"\nKey Indicators:")
    for ind in artist.get('indicators', [])[:10]:
        print(f"  - {ind}")
else:
    print(f"Artist '{artist_name}' not found")
EOF
```

**Usage:**
```bash
# Xem Maroon 5
python3 -c "import json; ..." "Maroon 5"

# Xem Taylor Swift  
python3 -c "import json; ..." "Taylor Swift"
```

---

## 🛠️ UTILITY COMMANDS

### 9. Kiểm tra Process đang chạy

```bash
# Tìm process
ps aux | grep classify_bands.py | grep -v grep

# Kill process nếu cần
pkill -f classify_bands.py
```

### 10. Xem File Size đang tăng

```bash
# Watch file size (chạy watch -n 2 ...)
watch -n 2 "ls -lh data/processed/band_classifications_full.json 2>/dev/null || echo 'File not created yet'"
```

### 11. So sánh kết quả giữa các lần chạy

```bash
# Backup kết quả hiện tại
cp data/processed/band_classifications_full.json \
   data/processed/band_classifications_full_backup_$(date +%Y%m%d_%H%M%S).json
```

---

## 📝 WORKFLOW ĐỀ XUẤT

### Option 1: Chạy trực tiếp với monitoring

```bash
# Terminal 1: Chạy classification
cd /home/manhnguyen/Downloads/neo4j/music-network-pop-us-uk
uv run python scripts/classify_bands.py \
    --input data/processed/parsed_artists.json \
    --raw-input data/raw/artists.json \
    --output data/processed/band_classifications_full.json \
    --verbose 2>&1 | tee /tmp/classification_full.log
```

```bash
# Terminal 2: Monitor progress (chạy định kỳ)
watch -n 30 'python3 << EOF
import json, os
f = "data/processed/band_classifications_full.json"
if os.path.exists(f):
    data = json.load(open(f))
    print(f"Progress: {len(data)}/1998 ({len(data)*100/1998:.1f}%)")
    bands = sum(1 for x in data if x.get("classification") == "band")
    print(f"Bands: {bands}, Solo: {len(data)-bands}")
else:
    print("File chưa tạo...")
EOF
'
```

### Option 2: Chạy background với monitoring

```bash
# Start background process
cd /home/manhnguyen/Downloads/neo4j/music-network-pop-us-uk
nohup uv run python scripts/classify_bands.py \
    --input data/processed/parsed_artists.json \
    --raw-input data/raw/artists.json \
    --output data/processed/band_classifications_full.json \
    --verbose > /tmp/classification_full.log 2>&1 &

PID=$!
echo "Process started with PID: $PID"
echo "Monitor with: tail -f /tmp/classification_full.log"
echo "Check progress with: python3 -c \"import json, os; f='data/processed/band_classifications_full.json'; print(f'{len(json.load(open(f)))}/1998') if os.path.exists(f) else print('0/1998')\""
```

```bash
# Monitor log
tail -f /tmp/classification_full.log

# Hoặc check progress định kỳ
while true; do
    clear
    python3 << 'EOF'
import json, os
f = 'data/processed/band_classifications_full.json'
if os.path.exists(f):
    data = json.load(open(f))
    print(f"Progress: {len(data)}/1998 ({len(data)*100/1998:.1f}%)")
    bands = sum(1 for x in data if x.get('classification') == 'band')
    print(f"Bands: {bands}, Solo: {len(data)-bands}")
else:
    print("File chưa tạo...")
EOF
    sleep 30
done
```

---

## ⚠️ LƯU Ý

1. **Thời gian**: Với 1998 artists và rate limit 0.5s mỗi request, sẽ mất khoảng **15-20 phút**
2. **Rate Limiting**: Wikipedia có thể có rate limiting, nếu gặp lỗi 429, chờ 5-10 phút rồi retry
3. **Disk Space**: File output sẽ khoảng **5-10 MB**
4. **Monitoring**: Nên monitor trong terminal riêng để theo dõi tiến trình

---

## ✅ KHI HOÀN THÀNH

Sau khi hoàn thành, file sẽ ở:
- `data/processed/band_classifications_full.json`

Kiểm tra kết quả:
```bash
# Xem statistics
python3 scripts/classify_bands.py --input data/processed/parsed_artists.json --raw-input data/raw/artists.json --output data/processed/band_classifications_full.json --test-sample 0 2>&1 | grep -A 20 "STATISTICS"
```


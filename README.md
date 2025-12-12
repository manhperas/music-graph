# 🎵 Music Knowledge Graph Chatbot

Chatbot về âm nhạc sử dụng Knowledge Graph và GraphRAG để trả lời câu hỏi về nghệ sĩ, ban nhạc, album, bài hát, thể loại và giải thưởng.

## ✨ Tính Năng

- **GraphRAG**: Truy vấn đồ thị Neo4j để lấy context cho câu trả lời
- **Multi-hop Reasoning**: Trả lời câu hỏi phức tạp cần suy luận qua nhiều bước
- **Qwen3 + LoRA**: Fine-tuned model cho domain âm nhạc
- **Giao diện Web**: Gradio UI và FastAPI server
- **Tìm đường đi ngắn nhất**: Tìm mối liên hệ giữa các entities trong đồ thị

## 🚀 Cài Đặt

### Yêu Cầu

- Python 3.10+
- Neo4j (chạy qua Docker hoặc local)
- GPU (khuyến nghị cho model inference)

### Cài Đặt

```bash
# Clone repo
git clone <repo-url>
cd music-graph

# Cài đặt dependencies
pip install -r requirements.txt

# Khởi động Neo4j (Docker)
docker-compose up -d

# Cấu hình Neo4j password trong file .env
echo "NEO4J_PASS=your_password" > .env
```

## 💻 Sử Dụng

### Chạy Chatbot (Gradio UI)

```bash
# Demo mode (không cần model)
python run_chatbot.py --ui gradio

# Với model Qwen3
python run_chatbot.py --ui gradio --load-model

# Với GraphRAG (Neo4j)
python run_chatbot.py --ui gradio --load-model --use-neo4j
```

### Chạy API Server

```bash
python run_chatbot.py --ui api
```

### Tìm Đường Đi Ngắn Nhất

```bash
python scripts/analysis/test_shortest_path.py \
  --node1 "Taylor Swift" \
  --node2 "Ed Sheeran"
```

## 🏗️ Kiến Trúc

- **Neo4j**: Lưu trữ music knowledge graph
- **GraphRAG**: Retrieve context từ graph để augment LLM
- **Qwen3-0.6B**: Base model với LoRA fine-tuning
- **Gradio/FastAPI**: Giao diện web và API

## 📁 Cấu Trúc

```
├── src/
│   ├── graph_rag/      # GraphRAG implementation
│   ├── models/         # Qwen3 model & LoRA
│   ├── api/            # Gradio & FastAPI
│   └── analysis/       # Graph analysis tools
├── data/               # Raw & processed data
├── scripts/            # Utility scripts
└── run_chatbot.py      # Main entry point
```

## 📝 License

Dự án phục vụ mục đích giáo dục và nghiên cứu.

# 📚 yu-rag-papers

A **Retrieval‑Augmented Generation (RAG)** playground that wires up FastAPI, PostgreSQL, FAISS vector storage, an embedding worker, and a LINE Bot into a single reproducible environment.

*Built for quick experiments, demos, and personal projects.*

---

## ✨ What's inside?

| Layer        | Tech (主要套件 / 映像)                                          | Purpose / Role                                                          |
| -------------| -------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **API**      | FastAPI + Uvicorn <br>LangChain (RAG Orchestration)           | REST / Webhook endpoints, stitches **Retriever → LLM** into chat flow   |
| **Vector DB**| FAISS (index-flat/IP)                                         | Stores document chunks & dense vectors for semantic search              |
| **Embedding**| Worker container (`docker/Dockerfile.embed`) <br>Hugging Face Transformers + LangChain Embeddings | Offline job：chunk files → generate embeddings → write to Vector DB     |
| **LLM**      | TinyLlama-1.1B-Chat (GGUF) <br>llama-cpp-python / ctransformers | Local inference for answer generation (keeps data on-prem)             |
| **Bot**      | LINE Messaging API (SDK)                                       | Chat interface for end users; forwards queries to API                   |
| **Tunnel**   | ngrok                                                          | Expose local API to LINE for webhook callbacks during dev               |

> 🐳 **Everything is containerised** – simply run `docker compose up` and you'll have the database, embedding worker, local LLM and API + LINE webhook all wired together.

---

## 🔍 Key Features

- **Academic Paper RAG**: The system can ingest arXiv papers and make them searchable (currently loaded with papers about transformers in NLP)
- **Fully Dockerized**: All components run in containers for easy deployment and testing
- **FAISS Vector Storage**: Efficient similarity search with FAISS vector indices
- **Local LLM Support**: Uses TinyLlama for inference, keeping all data local
- **Conversation Memory**: Maintains chat history in PostgreSQL database per user
- **LINE Bot Integration**: Ready-to-use LINE messaging interface with automated webhook setup
- **Production-Ready Architecture**: Follows best practices with multi-stage Docker builds and component isolation

---

## 🗂 Project layout

```text
├── app/                          # FastAPI 服務 ─ Web Layer
│   ├── main.py                   # 入口：掛載 router、事件、CORS
│   │                             # ➜ 亦統一注入 settings、啟動／關閉事件
│   ├── routes/                   # REST / Webhook 路由
│   │   └── line.py               # LINE Bot Webhook + 驗證簽名
│   └── db/                       # 資料庫相關封裝
│       ├── database.py           # 建立 SQLAlchemy Engine & SessionLocal
│       ├── memory.py             # ➜ 快取最近對話，用於 RAG Memory
│       └── models.py             # ORM Models（User & ChatHistory）
│
├── crawler/                      # 網站爬蟲 & 定時排程
│   ├── fetcher.py                # 抓指定網址 /S3 /RSS，落地到 data/pdf
│   └── scheduler.py              # APScheduler 任務，定時呼叫 fetcher
│
├── rag/                          # Retrieval-Augmented Generation 核心
│   ├── embeddings.py             # 讀取 sentence-transformers or local embedding
│   ├── rag_chain.py              # 建立 LLMChain（Retriever + LLM + Memory）
│   └── fine_tune.py              # ➜ LoRA / PEFT 微調腳本（可選用）
│
├── data/                         # 使用者與爬蟲資料、向量庫（持久化）
│   ├── faiss/                    # FAISS index ；embed 容器會寫入
│   ├── pdf/                      # 原始 PDF
│   └── pdf_text/                 # 解析後的純文字（chunk 前）
│
├── models/                       # 本地 LLM / Embedding（gguf、bin）
│   └── tinyllama-q4_K_M.gguf     # 示例；實際路徑依自行掛載
│
├── requirements/                 # 依賴拆分，減少重建時間
│   ├── requirements.core.txt     # langchain, pydantic, tqdm...
│   ├── requirements.api.txt      # fastapi, uvicorn[standard], psycopg2...
│   └── requirements.embed.txt    # sentence-transformers, faiss-cpu...
│
├── docker/                       # 多階段構建腳本
│   ├── Dockerfile.api            # FastAPI + ngrok + tinyllama runtime
│   └── Dockerfile.embed          # 嵌入批次：僅安裝核心 & embedding
│
├── bin/                          # 容器內啟動腳本 / 本機輔助指令
│   ├── start_api.sh              # 設定 uvicorn workers、expose 8000
│   ├── ingest.sh                 # 快速導入並處理一篇論文
│   └── dev_start_api.sh          # 用於本地開發的API啟動指令
│
├── .env.example                  # 範例環境變數，cp 為 .env
├── docker-compose.yml            # db + embed + api 三容器協調
└── README.md                     # 專案文件（安裝、執行、FAQ）
```

---

## 📋 Current Implementation

This project currently includes:

1. **Academic Paper RAG**: Four NLP papers from arXiv have been ingested:
   - 2004.11886v1.pdf
   - 2007.06257v2.pdf
   - 2106.02242v2.pdf
   - 2305.08800v1.pdf

2. **Embedding Pipeline**:
   - PDF fetching from arXiv via `crawler/fetcher.py`
   - Text extraction and paragraph segmentation
   - Vector generation using `sentence-transformers/all-MiniLM-L6-v2`
   - FAISS index storage for efficient retrieval

3. **Database Structure**:
   - User storage with LINE user IDs
   - Chat history with timestamps for conversation memory
   - Conversation persistence for contextual responses

4. **LLM Integration**:
   - TinyLlama local inference
   - Support for PEFT/LoRA fine-tuning

5. **LINE Bot**:
   - Automatic webhook setup using ngrok
   - Message validation and processing
   - Response formatting for LINE's character limits

---

## 🚀 Quick start (Docker Compose)

> **Prerequisites**  Docker Desktop 24+ or Docker Engine 20.10+.

1. **Clone & configure**

   ```bash
   git clone https://github.com/<yourname>/yu-rag-papers.git
   cd yu-rag-papers
   cp .env.example .env   # fill in the blanks
   ```

   | Variable                                            | Description                                                            |
   | --------------------------------------------------- | ---------------------------------------------------------------------- |
   | `OPENAI_API_KEY`                                    | Key for generating embeddings (or leave empty if you use local models) |
   | `NGROK_AUTHTOKEN`                                   | Your ngrok auth token (get one at ngrok.com)                           |
   | `LINE_CHANNEL_ACCESS_TOKEN` / `LINE_CHANNEL_SECRET` | Credentials for LINE Bot                                               |

2. **Launch everything**

   ```bash
   docker compose up --build
   ```

   ‑ API → [http://localhost:8000](http://localhost:8000)
   ‑ Swagger → [http://localhost:8000/docs](http://localhost:8000/docs)
   ‑ Postgres → localhost:5432 (`rag_user` / `rag_pass`)

   The API container will print the autogenerated **Webhook URL** (ngrok) to register in the LINE console, e.g.

   ```text
   🔗  Webhook URL: https://xxxxx.ngrok-free.app/webhook/line
   ✅  LINE Bot ready!
   ```

3. **Tear down**

   ```bash
   docker compose down -v   # -v removes the named volume `db_data`
   ```

---

## 🧪 Running locally without Docker

1. **Start Postgres** (native, Homebrew, or a tiny container):

   ```bash
   docker run -d --name pg -e POSTGRES_USER=rag_user -e POSTGRES_PASSWORD=rag_pass -e POSTGRES_DB=rag_db -p 5432:5432 postgres:16
   ```

2. **Create a virtualenv & install deps**

   ```bash
   python -m venv venv && source venv/bin/activate
   pip install -r requirements/requirements.core.txt -r requirements/requirements.api.txt
   ```

3. **Set env vars & run**

   ```bash
   export DATABASE_URL="postgresql+psycopg2://rag_user:rag_pass@localhost:5432/rag_db"
   export OPENAI_API_KEY=...
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   (Optional) run `ngrok http 8000` to expose the webhook.

---

## 🔧 Adding New Papers

To add new academic papers to the system:

```bash
# Quick import using bin/ingest.sh
source bin/ingest.sh

# Or manually run the crawler with custom parameters
python -m crawler.fetcher --query "cat:cs.CL AND transformers" --max 5
```

After adding papers, you need to generate embeddings:

```bash
# Generate embeddings for all PDFs in the data/pdf directory
python -m rag.embeddings
```

---

## 📱 Testing the LINE Bot

After starting the system and seeing the webhook URL:

1. Go to the [LINE Developers Console](https://developers.line.biz/console/)
2. Navigate to your bot's settings
3. Update the webhook URL to match the one provided by the system
4. Enable webhook in the settings
5. Send a message to your bot and it should respond using RAG from your academic papers

---

## 🧩 Extending the System

This framework is designed to be modular. You can:

1. Replace the LLM by changing the model in `rag/rag_chain.py`
2. Add new document sources by implementing custom crawlers
3. Implement additional chat interfaces beyond LINE
4. Fine-tune the LLM using the provided scripts in `fine_tune/`

---

## 📄 License

See the [LICENSE](LICENSE) file for details.

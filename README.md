# 📚 yu-rag-papers

> An AI-powered academic assistant that crawls research papers, indexes them with embeddings, and answers questions using a Retrieval-Augmented Generation (RAG) pipeline. Built with Hugging Face, LangChain, FastAPI, and designed for containerized cloud deployment.

---

## 🚀 Features

- 🔍 **Daily Research Paper Crawling**  
  Automatically fetches and indexes papers from target institutions.

- 🧠 **RAG-based Question Answering**  
  Combines retrieval and generation to answer questions grounded in actual paper content.

- 💬 **Multi-turn Memory Support**  
  Remembers conversation history with each user (via PostgreSQL + LangChain memory).

- 🤖 **LINE Bot Ready**  
  Users can chat with the system via LINE (extensible to other platforms).

- ⚙️ **FastAPI Backend**  
  RESTful API server for handling requests, chatbot messages, and internal services.

- 🐳 **Dockerized & K8s Compatible**  
  Fully containerized, scalable deployment architecture with CI/CD support.

---

## 🛠 Tech Stack

- **Language**: Python
- **AI Frameworks**: Hugging Face Transformers, LangChain
- **API Backend**: FastAPI
- **Database**: PostgreSQL
- **Vector Search**: FAISS
- **Deployment**: Docker + Kubernetes
- **CI/CD**: GitHub Actions

---

## 📦 Project Folder Structure

```
yu-rag-papers/
├── app/ # FastAPI main application
│ ├── main.py # Entry point
│ ├── routes/ # API & webhook routes
│ ├── services/ # API logic layer
│ ├── database/ # PostgreSQL interaction
│ └── memory/ # Conversation memory handling
├── rag/ # LangChain-based QA logic
│ ├── rag_chain.py # Full RAG pipeline logic
│ ├── embeddings.py # Vector embedding generator
│ └── vectorstore/ # FAISS vector DB tools
├── crawler/ # Paper fetching + scheduler
│ ├── fetcher.py
│ └── scheduler.py
├── fine_tune/ # Hugging Face fine-tuning scripts
│ ├── prepare_dataset.py
│ └── train.py
├── docker/ # Docker build setup
├── k8s/ # Kubernetes manifests
├── .github/workflows/ # GitHub Actions pipelines
│ └── ci-cd.yml
├── .env # Environment variables
├── requirements.txt # Python dependencies
└── README.md
```

## ⚙️ How to Run (Dev)

```bash
# 1. Clone project
git clone https://github.com/yourname/yu-rag-papers.git
cd yu-rag-papers

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env

# 4. Run server
uvicorn app.main:app --reload

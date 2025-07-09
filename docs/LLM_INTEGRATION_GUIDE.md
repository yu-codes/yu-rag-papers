# LLM Integration Guide

這份文件彙整了 **LangChain** 中最常用的 LLM Wrapper、所需安裝套件、必備環境變數，以及最小可行程式碼片段 (MVP)。複製貼上即可接入。

---

## 0 — 快速索引表

| Wrapper                   | 服務商 / 模型                            | 依賴 (`pip install …`)                                | 必備環境變數              | MVP 程式碼片段                                                                                                     |
| ------------------------- | ----------------------------------- | --------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------- |
| `ChatOpenAI`              | OpenAI GPT‑3.5 / GPT‑4o             | `openai langchain`                                  | `OPENAI_API_KEY`    | `llm = ChatOpenAI(model_name="gpt-4o", temperature=0)`                                                        |
| `ChatAnthropic`           | Anthropic Claude 3                  | `anthropic langchain-community`¹                    | `ANTHROPIC_API_KEY` | `llm = ChatAnthropic(model_name="claude-3-sonnet-20240229")`                                                  |
| `ChatGoogleGenerativeAI`  | Google Gemini Pro / 1.5             | `google-generativeai langchain-community`           | `GOOGLE_API_KEY`    | `llm = ChatGoogleGenerativeAI(model="gemini-pro", top_p=0)`                                                   |
| `ChatMistralAI`           | Mistral Cloud (Mixtral, Mistral‑7B) | `mistralai langchain-community`                     | `MISTRAL_API_KEY`   | `llm = ChatMistralAI(model_name="mistral-small-latest")`                                                      |
| `ChatHuggingFace`         | HF Inference Endpoints              | `huggingface_hub langchain-community`               | `HF_API_KEY`        | `llm = ChatHuggingFace(endpoint_url="https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct")` |
| `ChatOllama`              | 本機 Ollama 伺服器 (Llama3, Gemma…)      | `ollama langchain-community`                        | 無                   | `llm = ChatOllama(model="llama3:8b-instruct-q4_K_M")`                                                         |
| `ChatHuggingFacePipeline` | 任何本地 transformers 模型                | `torch transformers accelerate langchain-community` | 無                   | 先用 transformers 建立 pipeline，再 `ChatHuggingFacePipeline(pipeline=pipe)`                                        |

> ¹Anthropic 仍屬「community integration」，故安裝在 `langchain-community` 套件。

---

## 1 — 接入範例

以下片段均可直接放入 `rag/rag_chain.py`，只需修改 `llm = …` 其餘程式碼不動。

### 1.1 OpenAI GPT‑4o

```python
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(model_name="gpt-4o", temperature=0, streaming=True)
```

### 1.2 Anthropic Claude 3 Sonnet

```python
from langchain.chat_models import ChatAnthropic
llm = ChatAnthropic(model_name="claude-3-sonnet-20240229", max_tokens=1024)
```

### 1.3 Google Gemini 1.5 Pro

```python
from langchain.chat_models import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", top_k=40)
```

### 1.4 Mistral Cloud — Mixtral 8×22B

```python
from langchain.chat_models import ChatMistralAI
llm = ChatMistralAI(model_name="mixtral-8x22b", temperature=0.3)
```

### 1.5 本機 Ollama (Llama 3 8B, 4‑bit)

1. 安裝並啟動 ollama：`brew install ollama && ollama run llama3`
2. 代碼：

```python
from langchain.chat_models import ChatOllama
llm = ChatOllama(model="llama3:8b-instruct-q4_K_M", streaming=True)
```

### 1.6 本地 transformers 模型 (GPU/CPU 皆可)

```python
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain.chat_models import ChatHuggingFacePipeline

name = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name, device_map="auto", torch_dtype="auto")
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)

llm = ChatHuggingFacePipeline(pipeline=pipe)
```

---

## 2 — 如何在 `rag_chain.py` 快速切換

```python
from rag.rag_chain import build_chain
chain = build_chain(llm=my_llm)  # 傳入自訂 llm
```

若沒有傳 `llm` 參數，`build_chain()` 會預設採用 OpenAI GPT‑3.5 或您在環境變數指定的模型。

---

## 3 — GitHub Actions 範例工作流程

以下 workflow 每次 push 或每日凌晨 2 點自動：

1. 建置虛擬環境、安裝依賴
2. 跑 `bin/ingest.sh` 抓新 paper & 重新向量化
3. 執行 smoke test 確保 RAG Chain 可回應

`.github/workflows/rag-pipeline.yml`

```yaml
name: RAG Pipeline

on:
  push:
    branches: [main]
  schedule:
    - cron: "0 18 * * *"   # 每天 02:00 (Taipei)

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps (cache)
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ hashFiles('requirements.txt') }}
      - run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt langchain openai google-generativeai anthropic mistralai hugggingface_hub ollama-cli
      - name: Run ingestion (PDF ➜ 向量)
        run: |
          bash bin/ingest.sh "cat:cs.CL" --max 5
      - name: Smoke test (RAG)
        run: |
          python - <<'PY'
          from rag.rag_chain import build_chain
          chain = build_chain()
          res = chain.invoke({"question": "What is a Transformer model?"})
          assert res["answer"], "Empty answer!"
          print("✅ smoke passed")
          PY
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

> *若要使用本機 Ollama 或本地 transformers，需要改用 self‑hosted runner，因為 GitHub Hosted Runner 沒有 GPU，也無法安裝 daemon 服務。*

---

## 4 — 常見問題 (FAQ)

| 問題                             | 解答                                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------------- |
| **GitHub Actions 沒 GPU 可以跑嗎？** | 可以，只要使用雲端 LLM (OpenAI、Anthropic…) 或 8B 以下量化模型。不過大型開源模型在 CPU 會非常慢。                           |
| **多模型 A/B 測試怎麼做？**             | 在 `build_chain()` 外層寫迴圈，多次呼叫不同 `llm`，比對回答或調用 `langsmith` 追蹤。                                |
| **想要 RAG 記住對話超長上下文？**          | 把 `ConversationBufferMemory` 換成 `VectorStoreRetrieverMemory` 或 `ConversationSummaryMemory`。 |

---

> 有新的模型或平台想接入，只要在本檔「快取索引表」新增一列，並照 `pip -install / env / snippet` 三步驟，就能無痛插拔。

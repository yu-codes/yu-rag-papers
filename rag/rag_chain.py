"""
rag/rag_chain.py
================
把 FAISS 向量資料庫接成 LangChain Conversational RAG，
並加上一段最小互動 CLI，方便直接測試。

先確定已經執行過：
    python -m rag.embeddings --max 3
產生  data/faiss/index.faiss  與 metadata.pkl
"""
from pathlib import Path
import os
import typer

# from ctransformers.langchain import ChatCTransformers  # 新增

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI  # ↖ 新路徑

from langchain_community.chat_models import ChatLlamaCpp  # ← 新

# ---------- 常數 ----------
INDEX_DIR = Path("data/faiss")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
K = 3

MODEL_PATH = "models/tinyllama-q4_K_M.gguf"  # 存放於 repo 或 CI 下載

# ---------- 工具函式 ----------
def build_retriever():
    embedder = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    vs = FAISS.load_local(
        str(INDEX_DIR),
        embedder,
    allow_dangerous_deserialization=True,   # ← 新增
)
    return vs.as_retriever(search_kwargs={"k": K})


"""def build_chain():

    llm = ChatOpenAI(
        model="gpt-3.5-turbo", temperature=0, api_key=os.getenv("OPENAI_API_KEY")
    )
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=build_retriever(),
        memory=ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        ),
        return_source_documents=True,
    )"""


def build_chain():
    llm = ChatLlamaCpp(
        model_path=MODEL_PATH,
        temperature=0.1,
        max_tokens=512,
        n_ctx=4096,  # 視模型支援調整
        n_threads=4,  # GitHub runner = 2 vCPU，可設 2
        verbose=False,
    )
    retriever = build_retriever()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,
    )
    

# ---------- Typer CLI ----------
cli = typer.Typer()


@cli.command()
def chat():
    """進入互動式 RAG 對話；輸入 exit 離開。"""
    chain = build_chain()
    print("🤖 RAG Chat 啟動，輸入 'exit' 離開")
    while True:
        q = input("你： ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        print("AI：", chain({"question": q})["answer"], "\n")


if __name__ == "__main__":
    cli()

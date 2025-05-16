"""
rag/rag_chain.py
================
把 FAISS 向量資料庫接成 LangChain Conversational RAG，
並保留一個簡易 CLI 方便在本機測試。

先執行：
    python -m rag.embeddings --max 3
以產生 data/faiss/index.faiss 與 metadata.pkl
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatLlamaCpp
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from peft import PeftModel
# ---------- 常數 ----------
INDEX_DIR = Path("data/faiss")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
K = 3

MODEL_PATH = "models/tinyllama-q4_K_M.gguf"  # TinyLLaMA-GGUF 路徑


# ---------- 工具函式 ----------
def build_retriever():
    if not (INDEX_DIR / "index.faiss").exists():
        raise RuntimeError(f"❌ 向量庫不存在：{INDEX_DIR}")
    embedder = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    vs = FAISS.load_local(
        str(INDEX_DIR),
        embedder,
        allow_dangerous_deserialization=True,  # 為了在 CI 載入 pickle
    )
    return vs.as_retriever(search_kwargs={"k": K})


def build_chain(
    memory: Optional[ConversationBufferMemory] = None,
):
    """
    建立 ConversationalRetrievalChain.

    Parameters
    ----------
    memory : ConversationBufferMemory | None, default None
        若傳入自訂記憶體（例如含資料庫歷史），
        直接掛載；否則使用預設的 In-RAM Buffer。
    """
    llm = ChatLlamaCpp(
        model_path=MODEL_PATH,
        temperature=0.1,
        max_tokens=512,
        n_ctx=4096,
        n_threads=4,  # GitHub runner 有 2 vCPU，可視情況調整
        verbose=False,
    )
    adapter_dir = Path("rag/lora_adapter")
    if adapter_dir.exists():
        llm.client = PeftModel.from_pretrained(llm.client, adapter_dir.as_posix())


    retriever = build_retriever()
    if memory is None:
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,
    )
    return chain


# ---------- Typer CLI ----------
cli = typer.Typer()


@cli.command()
def chat():
    """進入互動式 RAG 對話；輸入 exit 離開。"""
    chain = build_chain()
    print("🤖  RAG Chat 啟動，輸入 'exit' 離開")
    while True:
        q = input("你： ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        print("AI：", chain({"question": q})["answer"], "\n")


if __name__ == "__main__":
    cli()

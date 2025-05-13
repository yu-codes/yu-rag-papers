"""
rag/embeddings.py
=================
將段落文字轉成向量並寫入 **LangChain 相容** 的 FAISS VectorStore，並提供簡易查詢功能。
"""

from pathlib import Path
import logging
from typing import List, Dict

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS as LC_FAISS
from langchain.schema import Document
from sentence_transformers import SentenceTransformer  # 只用於 CLI demo 查詢

# ---------- 目錄設定 ----------
FAISS_DIR = Path("data/faiss")
FAISS_DIR.mkdir(parents=True, exist_ok=True)

# 預設嵌入模型（可替換）
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ---------- 主要流程 ----------
def build_embeddings(corpus: Dict[str, List[str]]) -> None:
    """將 `{paper_id: [paragraph, …]}` 轉成向量並以 LangChain 格式存磁碟。"""
    if not corpus:
        raise ValueError("傳入的 corpus 為空！")

    embedder = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    docs: List[Document] = []

    logging.info("Packaging paragraphs as Documents …")
    for pid, paras in corpus.items():
        for idx, text in enumerate(paras):
            docs.append(
                Document(
                    page_content=text,
                    metadata={"paper_id": pid, "paragraph": idx},
                )
            )

    logging.info("Building LangChain FAISS VectorStore …")
    store = LC_FAISS.from_documents(docs, embedder)
    store.save_local(str(FAISS_DIR))
    logging.info(f"✅ 向量數量：{len(docs)}  已寫入 {FAISS_DIR / 'index.faiss'}")


def query(text: str, top_k: int = 5):
    """用句子 `text` 查詢最相似段落，回傳 [(score, metadata, paragraph_text), …]"""
    embedder = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    store = LC_FAISS.load_local(
        str(FAISS_DIR),
        embedder,
        allow_dangerous_deserialization=True,  # 我們自己生成的檔案可信
    )

    results = store.similarity_search_with_score(text, k=top_k)
    out = []
    for doc, dist in results:  # dist 是 L2 距離；轉成簡易相似度
        sim = 1 / (1 + dist)
        out.append((sim, doc.metadata, doc.page_content))
    return out


# ---------- CLI ----------
def _cli():
    import argparse
    from crawler.fetcher import crawl

    parser = argparse.ArgumentParser(
        description="將 arXiv 文章嵌入並寫入 FAISS，並可立即測試檢索"
    )
    parser.add_argument(
        "--query", default="cat:cs.CL AND transformers", help="arXiv API 查詢字串"
    )
    parser.add_argument(
        "--max", type=int, default=3, metavar="N", help="下載最多 N 篇 (default: 3)"
    )
    parser.add_argument(
        "--test", default="transformer pretraining", help="完成後用此句測試檢索"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 1) 抓 PDF ➜ 文字
    corpus = crawl(args.query, args.max)

    # 2) 產生向量索引
    build_embeddings(corpus)

    # 3) 查詢示範
    print("\n---- Query demo ----")
    for score, meta, txt in query(args.test, 3):
        print(f"[{score:.3f}] {meta['paper_id']}#{meta['paragraph']}: {txt[:80]}…")


if __name__ == "__main__":
    _cli()

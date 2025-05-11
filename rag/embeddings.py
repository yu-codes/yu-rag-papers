"""
rag/embeddings.py
=================
將段落文字轉成向量並寫入 FAISS，並提供簡易查詢功能。
"""

from pathlib import Path
import pickle
import logging

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ---------- 目錄設定 ----------
FAISS_DIR = Path("data/faiss")
FAISS_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = FAISS_DIR / "index.faiss"
META_PATH = FAISS_DIR / "metadata.pkl"

# 預設嵌入模型（可替換）
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ---------- 主要流程 ----------
def build_embeddings(corpus: dict[str, list[str]]) -> None:
    """
    將 {paper_id: [段落, ...]} 轉成向量並存磁碟。

    會輸出：
      • data/faiss/index.faiss   —— 向量索引
      • data/faiss/metadata.pkl —— [(paper_id, paragraph_idx, paragraph_text), ...]
    """
    if not corpus:
        raise ValueError("傳入的 corpus 為空！")

    model = SentenceTransformer(MODEL_NAME)
    vectors: list[np.ndarray] = []
    metadata: list[tuple[str, int, str]] = []

    logging.info("Encoding paragraphs …")
    for pid, paras in corpus.items():
        for idx, text in enumerate(paras):
            vec = model.encode(text, normalize_embeddings=True)
            vectors.append(vec)
            metadata.append((pid, idx, text))

    vectors_np = np.vstack(vectors).astype("float32")
    dim = vectors_np.shape[1]

    logging.info("Building FAISS index …")
    index = faiss.IndexFlatIP(dim)  # 內積相似度；快速、免訓練
    index.add(vectors_np)

    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_bytes(pickle.dumps(metadata))
    logging.info(f"✅ 向量數量：{len(metadata)}  已寫入 {INDEX_PATH}")


def query(text: str, top_k: int = 5):
    """
    用句子 `text` 查詢最相似的段落，回傳
      [(score, paper_id, paragraph_idx, paragraph_text), ...]
    """
    if not INDEX_PATH.exists() or not META_PATH.exists():
        raise FileNotFoundError("找不到向量索引；請先執行 build_embeddings()")

    model = SentenceTransformer(MODEL_NAME)
    index = faiss.read_index(str(INDEX_PATH))
    metadata = pickle.loads(META_PATH.read_bytes())

    qvec = model.encode(text, normalize_embeddings=True).astype("float32")
    scores, ids = index.search(qvec.reshape(1, -1), top_k)

    results = [
        (float(scores[0][i]), *metadata[ids[0][i]])
        for i in range(top_k)
        if ids[0][i] != -1
    ]
    return results


# ---------- CLI ----------
def _cli():
    import argparse
    from crawler.fetcher import crawl

    parser = argparse.ArgumentParser(
        description="將 arXiv 文章嵌入並寫入 FAISS，並可立即測試查詢"
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

    # 3) 簡單查詢示範
    print("\n---- Query demo ----")
    for score, pid, idx, txt in query(args.test, 3):
        print(f"[{score:.3f}] {pid}#{idx}: {txt[:80]}…")


if __name__ == "__main__":
    _cli()

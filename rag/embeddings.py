"""
把段落文字轉向量並寫入 FAISS
"""

from pathlib import Path
import pickle

import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

FAISS_DIR = Path("data/faiss")
FAISS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = FAISS_DIR / "index.faiss"
META_PATH = FAISS_DIR / "metadata.pkl"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def build_embeddings(corpus: dict[str, list[str]]):
    model = SentenceTransformer(MODEL_NAME)
    vectors = []
    metadata = []  # [(paper_id, paragraph_idx, paragraph_text), ...]

    for pid, paras in corpus.items():
        for idx, text in enumerate(paras):
            vec = model.encode(text, normalize_embeddings=True)
            vectors.append(vec)
            metadata.append((pid, idx, text))

    dim = vectors[0].shape[0]
    index = faiss.IndexFlatIP(dim)  # 内積 (相似度)；可換 L2 版本
    index.add(faiss.numpy.array(vectors))
    faiss.write_index(index, str(INDEX_PATH))
    with META_PATH.open("wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ 向量數量: {len(metadata)}  已寫入 {INDEX_PATH}")


def query(text: str, top_k: int = 5):
    model = SentenceTransformer(MODEL_NAME)
    index = faiss.read_index(str(INDEX_PATH))
    with META_PATH.open("rb") as f:
        metadata = pickle.load(f)

    qvec = model.encode(text, normalize_embeddings=True)
    scores, ids = index.search(qvec.reshape(1, -1), top_k)
    results = [(float(scores[0][i]), *metadata[ids[0][i]]) for i in range(top_k)]
    return results


if __name__ == "__main__":
    from crawler.fetcher import crawl

    corpus = crawl("cat:cs.CL AND large language model", max_results=10)
    build_embeddings(corpus)

    print("---- 測試查詢 ----")
    for s, pid, idx, txt in query("instruction tuning methods", 3):
        print(f"[{s:.3f}] {pid}#{idx}: {txt[:80]}…")

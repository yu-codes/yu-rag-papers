# 先到專案根目錄
cd ~/Side-Project/yu-rag-papers

# 建議用虛擬環境
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 跑 1 篇 paper 減少等待
python - <<'PY'
from crawler.fetcher import crawl
corpus = crawl("cat:cs.CL AND transformers", max_results=1)
print("段落數:", sum(len(p) for p in corpus.values()))
PY

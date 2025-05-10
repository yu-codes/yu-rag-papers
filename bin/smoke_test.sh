#!/usr/bin/env bash
# 簡易 Smoke Test：抓 1 篇 arXiv PDF ➜ 印段落數
set -euo pipefail

# 切到 repo 根目錄，確保任何地方呼叫都 OK
cd "$(dirname "$0")/.."

# 建議用獨立 venv（CI 裡跑也安全，重複建立沒副作用）
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 跑 1 篇 paper
python - <<'PY'
from crawler.fetcher import crawl
corpus = crawl("cat:cs.CL AND transformers", max_results=1)
print("段落數:", sum(len(p) for p in corpus.values()))
PY

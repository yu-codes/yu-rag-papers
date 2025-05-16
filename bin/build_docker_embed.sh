# -f 指定檔名；自訂個好記的 tag
docker build -f docker/Dockerfile.embed -t rag-embed:dev .


## docker run --rm -v $(pwd):/code rag-embed:dev
# 看到「✅ 向量數量：... 已寫入 data/faiss/index.faiss」即 OK

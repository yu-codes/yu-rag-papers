# 檢查映像是否存在
docker images rag-embed:dev

# 直接跑一次向量化流程（把 data/ 與 models/ 掛進去才能寫檔）
docker run --rm \
  -v "$PWD/data":/code/data \
  -v "$PWD/models":/code/models \
  --name rag-embed-test rag-embed:dev

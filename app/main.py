from fastapi import FastAPI
from dotenv import load_dotenv

# 本地開發環境自動讀取 .env
load_dotenv()

# 資料庫初始化
from app.db.database import init_db

# 路由
from app.routes.line import router as line_router

app = FastAPI(title="RAG × LINE Bot")
# 註冊 webhook 路由
app.include_router(line_router)

# 啟動時建立資料表
@app.on_event("startup")
def startup_event():
    init_db()

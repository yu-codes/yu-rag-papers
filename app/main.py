from fastapi import FastAPI
from dotenv import load_dotenv

# 本地開發自動讀 .env
load_dotenv()

from app.routes.line import router as line_router

app = FastAPI(title="RAG × LINE Bot")
app.include_router(line_router, prefix="/webhook/line")

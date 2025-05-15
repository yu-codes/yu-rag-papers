import os
from fastapi import APIRouter, Header, HTTPException, Request
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from rag.rag_chain import build_chain  # ← 建 RAG chain，支援 memory=...
from app.db.database import SessionLocal  # DB Session
from app.db.models import User, ChatHistory  # ORM models
from app.db.memory import build_memory  # 依 user_id 取 ConversationBufferMemory

# -------- LINE SDK 設定 --------
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
if not (channel_secret and channel_token):
    raise RuntimeError("LINE_CHANNEL_SECRET / ACCESS_TOKEN missing")

bot_api = LineBotApi(channel_token)
parser = WebhookParser(channel_secret)

# -------- FastAPI router --------
router = APIRouter()


@router.post("/webhook/line")  # 必須與 LINE Console 填寫完全一致
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(..., alias="X-Line-Signature"),
):
    body = await request.body()

    # 1) 簽名驗證
    try:
        events = parser.parse(body.decode(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2) 逐則事件處理
    for ev in events:
        if isinstance(ev, MessageEvent) and isinstance(ev.message, TextMessage):

            user_id = ev.source.user_id
            q = ev.message.text.strip()

            # --- 取出「針對該使用者」的記憶 & 建 RAG chain ---
            memory = build_memory(user_id)  # ConversationBufferMemory (已含歷史)
            rag_chain = build_chain(memory=memory)

            # RAG 查詢
            a = rag_chain({"question": q})["answer"]

            # --- 回覆 LINE 使用者 ---
            bot_api.reply_message(
                ev.reply_token, TextSendMessage(text=a[:1000])  # LINE 最長 1000 字
            )

            # --- 將今回合寫回資料庫 ---
            session = SessionLocal()
            # 確保 user 存在
            if not session.query(User).filter_by(id=user_id).first():
                session.add(User(id=user_id))
            session.add_all(
                [
                    ChatHistory(user_id=user_id, role="user", content=q),
                    ChatHistory(user_id=user_id, role="ai", content=a),
                ]
            )
            session.commit()
            session.close()

    return {"status": "ok"}

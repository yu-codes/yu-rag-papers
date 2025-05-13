import os
import hmac, hashlib, base64

from fastapi import APIRouter, Header, HTTPException, Request
from linebot import LineBotApi, WebhookParser
from linebot.models import TextMessage, MessageEvent

from rag.rag_chain import build_chain  # 直接呼叫我們的 RAG

router = APIRouter()
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not channel_secret or not channel_token:
    raise RuntimeError("LINE channel secret / access token not set")

bot_api = LineBotApi(channel_token)
parser = WebhookParser(channel_secret)

rag_chain = build_chain()  # 預載模型較慢，可考慮懶載


@router.post("/")
async def callback(
    request: Request,
    x_line_signature: str = Header(..., alias="X-Line-Signature"),
):
    body = await request.body()
    # ----- 驗證簽名 -----
    hash = hmac.new(channel_secret.encode(), body, hashlib.sha256).digest()
    signature = base64.b64encode(hash).decode()
    if signature != x_line_signature:
        raise HTTPException(400, "Invalid signature")

    # ----- 解析事件 -----
    events = parser.parse(body.decode(), x_line_signature)
    for ev in events:
        if isinstance(ev, MessageEvent) and isinstance(ev.message, TextMessage):
            q = ev.message.text.strip()
            a = rag_chain({"question": q})["answer"]
            bot_api.reply_message(
                ev.reply_token, TextMessage(text=a[:1000])
            )  # LINE 單訊息最長 1000 字
    return {"status": "ok"}

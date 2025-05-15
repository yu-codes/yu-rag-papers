#!/bin/bash
set -e

# 載入 .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# 檢查 ngrok
if ! command -v ngrok &> /dev/null; then
  echo "❌ 請先安裝 ngrok！"
  exit 1
fi

# 檢查 jq
if ! command -v jq &> /dev/null; then
  echo "❌ 請先安裝 jq（macOS: brew install jq）"
  exit 1
fi

# 檢查 token（現在會讀 .env）
if [[ -z "$LINE_CHANNEL_ACCESS_TOKEN" ]]; then
  echo "❌ 未在 .env 中設定 LINE_CHANNEL_ACCESS_TOKEN"
  exit 1
fi

# 啟動 FastAPI（背景）
echo "🚀 啟動本地 FastAPI 伺服器 …"
uvicorn app.main:app --port 8000 --host 127.0.0.1 &
FASTAPI_PID=$!
sleep 2

# 啟動 ngrok（背景）
echo "🌐 啟動 ngrok …"
ngrok http 8000 > /dev/null &
NGROK_PID=$!
sleep 3

# 擷取公開網址
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
WEBHOOK_URL="${NGROK_URL}/webhook/line"

echo "🔗 Webhook URL 為：$WEBHOOK_URL"

# 更新 LINE webhook
echo "📡 更新 LINE webhook ..."
curl -s -X PUT "https://api.line.me/v2/bot/channel/webhook/endpoint" \
  -H "Authorization: Bearer $LINE_CHANNEL_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"endpoint\":\"$WEBHOOK_URL\"}" | jq .

echo "✅ 完成！你現在可以在 LINE 聊天室與機器人對話了。"

# 等待中斷
trap "kill $FASTAPI_PID $NGROK_PID" EXIT
wait

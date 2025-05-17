#!/usr/bin/env bash
set -euo pipefail

# --- 讀取 .env（若有掛 volume） ---
if [[ -f /code/.env ]]; then
  export $(grep -v '^#' /code/.env | xargs)
fi

# --- 基本檢查 ---
: "${LINE_CHANNEL_ACCESS_TOKEN:?need LINE_CHANNEL_ACCESS_TOKEN}"
: "${LINE_CHANNEL_SECRET:?need LINE_CHANNEL_SECRET}"
: "${NGROK_AUTHTOKEN:?need NGROK_AUTHTOKEN}"

# --- 啟動 FastAPI ---
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!
sleep 3

# --- 啟動 ngrok（先寫入 authtoken） ---
ngrok config add-authtoken "$NGROK_AUTHTOKEN"
ngrok http --log=stdout 8000 > /tmp/ngrok.log &
NGROK_PID=$!

# 等 ngrok 起來
until curl -s http://localhost:4040/api/tunnels >/dev/null 2>&1; do
  sleep 1
done
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
WEBHOOK_URL="${NGROK_URL}/webhook/line"

echo "🔗  Webhook URL: $WEBHOOK_URL"

# --- 設定 LINE Webhook ---
curl -s -X PUT "https://api.line.me/v2/bot/channel/webhook/endpoint" \
  -H "Authorization: Bearer $LINE_CHANNEL_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"endpoint\":\"$WEBHOOK_URL\"}" >/dev/null

echo "✅  LINE Bot ready!"

trap "kill $FASTAPI_PID $NGROK_PID" SIGINT SIGTERM
wait $FASTAPI_PID

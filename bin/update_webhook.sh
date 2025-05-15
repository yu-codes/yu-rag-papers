#!/bin/bash
# 取得 ngrok 的公開網址
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url')

# 拼 webhook endpoint
WEBHOOK_URL="$NGROK_URL/webhook/line"

# 顯示 webhook URL
echo "🔗 Updating LINE webhook to: $WEBHOOK_URL"

# 傳送 PATCH 請求到 LINE Messaging API
curl -X PUT "https://api.line.me/v2/bot/channel/webhook/endpoint" \
  -H "Authorization: Bearer $LINE_CHANNEL_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"endpoint\":\"$WEBHOOK_URL\"}"

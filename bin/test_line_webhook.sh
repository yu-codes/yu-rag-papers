#!/usr/bin/env bash
# test_line_webhook.sh  ——  本地 / ngrok LINE Webhook 驗證腳本

# LINE_CHANNEL_SECRET="xxxxxxxx" bin/test_line_webhook.sh
set -euo pipefail

WEBHOOK_PATH="/webhook/line"
LOCAL_URL="http://127.0.0.1:8000${WEBHOOK_PATH}"

# ---------- 1) Channel secret ----------
if [[ -z "${LINE_CHANNEL_SECRET:-}" ]]; then
  read -rsp "🔑  請輸入 LINE_CHANNEL_SECRET: " LINE_CHANNEL_SECRET
  echo
fi

# ---------- 2) 準備 body ----------
BODY_FILE="body.json"
if [[ ! -f $BODY_FILE ]]; then
  cat >"$BODY_FILE" <<'JSON'
{
  "events": [
    {
      "type": "message",
      "replyToken": "00000000000000000000000000000000",
      "source": { "userId": "Uxxxxxxxxx", "type": "user" },
      "timestamp": 0,
      "mode": "active",
      "message": { "id": "1", "type": "text", "text": "Hello from shell!" }
    }
  ]
}
JSON
  echo "✅  建立預設 $BODY_FILE"
fi

BODY=$(cat "$BODY_FILE")

# ---------- 3) 計算簽名 ----------
SIG=$(python - <<PY
import hmac, hashlib, base64, os, json, sys
secret = os.environ["LINE_CHANNEL_SECRET"].encode()
body   = open("$BODY_FILE","rb").read()
sig    = base64.b64encode(hmac.new(secret, body, hashlib.sha256).digest()).decode()
print(sig)
PY
)
echo "📝  X-Line-Signature = $SIG"

# ---------- 4) 判斷測試目標 ----------
TARGETS=("$LOCAL_URL")

# 若偵測到 ngrok tunnel.json，取第一個 https forwarding
if command -v curl >/dev/null && curl -fs http://127.0.0.1:4040/api/tunnels >/dev/null 2>&1; then
  NGURL=$(curl -fs http://127.0.0.1:4040/api/tunnels | \
          python -c "import sys, json, re; t=json.load(sys.stdin)['tunnels']; print(next((i['public_url'] for i in t if i['public_url'].startswith('https')), ''))")
  if [[ -n "$NGURL" ]]; then
    TARGETS+=("${NGURL}${WEBHOOK_PATH}")
  fi
fi

# ---------- 5) 逐一 curl ----------
for url in "${TARGETS[@]}"; do
  echo -e "\n🚀  POST $url"
  http_code=$(curl -s -o /tmp/resp.$$ -w '%{http_code}' \
              -X POST "$url" \
              -H "Content-Type: application/json" \
              -H "X-Line-Signature: $SIG" \
              --data-binary @"$BODY_FILE" || true)
  echo "HTTP $http_code  →  $(cat /tmp/resp.$$)"
done
rm -f /tmp/resp.$$

#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://127.0.0.1:8080"

command -v jq >/dev/null || { echo "jq is required"; exit 1; }

UA="user_a_$RANDOM"
UB="user_b_$RANDOM"
PA="secret"
PB="secret"

A_REG=$(curl -sS --fail -X POST "$BASE_URL/auth/register" -H "Content-Type: application/json" -d "{\"username\":\"$UA\",\"email\":\"$UA@example.com\",\"password\":\"$PA\"}")
A_TOKEN=$(echo "$A_REG" | jq -r '.access_token')

B_REG=$(curl -sS --fail -X POST "$BASE_URL/auth/register" -H "Content-Type: application/json" -d "{\"username\":\"$UB\",\"email\":\"$UB@example.com\",\"password\":\"$PB\"}")
B_TOKEN=$(echo "$B_REG" | jq -r '.access_token')

A_POST_RESP=$(curl -sS --fail -X POST "$BASE_URL/posts/" -H "Authorization: Bearer $A_TOKEN" -H "Content-Type: application/json" -d '{"title":"A Post","content":"Hello from A"}')
POST_A_ID=$(echo "$A_POST_RESP" | jq -r '.id')
USER_A_ID=$(echo "$A_POST_RESP" | jq -r '.owner_id')

B_POST_RESP=$(curl -sS --fail -X POST "$BASE_URL/posts/" -H "Authorization: Bearer $B_TOKEN" -H "Content-Type: application/json" -d '{"title":"B Post","content":"Hello from B"}')
POST_B_ID=$(echo "$B_POST_RESP" | jq -r '.id')
USER_B_ID=$(echo "$B_POST_RESP" | jq -r '.owner_id')

curl -sS --fail -X POST "$BASE_URL/follows/$USER_B_ID" -H "Authorization: Bearer $A_TOKEN" >/dev/null
curl -sS --fail -X POST "$BASE_URL/follows/$USER_A_ID" -H "Authorization: Bearer $B_TOKEN" >/dev/null

curl -sS --fail -X POST "$BASE_URL/posts/$POST_A_ID/rate" -H "Authorization: Bearer $B_TOKEN" -H "Content-Type: application/json" -d '{"score":9}' >/dev/null
curl -sS --fail "$BASE_URL/posts/$POST_A_ID/rating" >/dev/null

C_RESP=$(curl -sS --fail -X POST "$BASE_URL/comments/" -H "Authorization: Bearer $B_TOKEN" -H "Content-Type: application/json" -d "{\"post_id\":$POST_A_ID,\"content\":\"Nice post!\"}")
COMMENT_ID=$(echo "$C_RESP" | jq -r '.id')

curl -sS --fail -X POST "$BASE_URL/comments/$COMMENT_ID/rate" -H "Authorization: Bearer $A_TOKEN" -H "Content-Type: application/json" -d '{"score":8}' >/dev/null
curl -sS --fail -X DELETE "$BASE_URL/comments/$COMMENT_ID/rating" -H "Authorization: Bearer $A_TOKEN" >/dev/null

curl -sS --fail -X DELETE "$BASE_URL/comments/$COMMENT_ID" -H "Authorization: Bearer $B_TOKEN" >/dev/null
curl -sS --fail -X DELETE "$BASE_URL/posts/$POST_A_ID/rating" -H "Authorization: Bearer $B_TOKEN" >/dev/null
curl -sS --fail -X DELETE "$BASE_URL/posts/$POST_A_ID" -H "Authorization: Bearer $A_TOKEN" >/dev/null

echo 'lowkey test' > /tmp/lowkey.txt
L_RESP=$(curl -sS --fail -X POST "$BASE_URL/lowkeys/" -H "Authorization: Bearer $A_TOKEN" -F "file=@/tmp/lowkey.txt" -F "title=Lowkey A" -F "visibility=public")
LOWKEY_ID=$(echo "$L_RESP" | jq -r '.id')

curl -sS --fail "$BASE_URL/lowkeys/$LOWKEY_ID" -H "Authorization: Bearer $B_TOKEN" >/dev/null
curl -sS --fail -X POST "$BASE_URL/lowkeys/$LOWKEY_ID/rate" -H "Authorization: Bearer $B_TOKEN" -H "Content-Type: application/json" -d '{"score":7}' >/dev/null
curl -sS --fail -X DELETE "$BASE_URL/lowkeys/$LOWKEY_ID/rating" -H "Authorization: Bearer $B_TOKEN" >/dev/null
curl -sS --fail -X DELETE "$BASE_URL/lowkeys/$LOWKEY_ID" -H "Authorization: Bearer $A_TOKEN" >/dev/null

curl -sS --fail -X DELETE "$BASE_URL/auth/me" -H "Authorization: Bearer $A_TOKEN" >/dev/null
curl -sS --fail -X DELETE "$BASE_URL/auth/me" -H "Authorization: Bearer $B_TOKEN" >/dev/null

echo "E2E succeeded: UA=$UA UB=$UB"
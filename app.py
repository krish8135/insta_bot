import os
import hmac
import hashlib
import random
import requests
from flask import Flask, request, abort

app = Flask(__name__)

# ---- Environment variables (set these, don't hardcode) ----
VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]        # any string you choose
APP_SECRET = os.environ["APP_SECRET"]            # Meta app secret
ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]     # Instagram user access token
IG_USER_ID = os.environ["IG_USER_ID"]            # your Instagram professional account ID

GRAPH = "https://graph.instagram.com/v23.0"

# ---- Customize here ----
# Only react if comment contains one of these (empty list = react to every comment)
KEYWORDS = []  # e.g. ["link", "price", "details"]

PUBLIC_REPLIES = [
    "Thanks! DM check karo 📩",
    "Done ✅ Aapko DM bhej diya hai!",
    "Shukriya! Inbox dekho 🙌",
]
DM_TEXT = "Hey! Comment karne ke liye thanks 🙏 Ye lo aapka link/info: https://example.com"

seen_comments = set()  # simple dedupe (resets on restart)


def valid_signature(req):
    sig = req.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(
        APP_SECRET.encode(), req.get_data(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(sig, expected)


def reply_to_comment(comment_id):
    r = requests.post(
        f"{GRAPH}/{comment_id}/replies",
        params={"message": random.choice(PUBLIC_REPLIES), "access_token": ACCESS_TOKEN},
        timeout=15,
    )
    print("comment reply:", r.status_code, r.text)


def private_reply_dm(comment_id):
    r = requests.post(
        f"{GRAPH}/{IG_USER_ID}/messages",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"recipient": {"comment_id": comment_id}, "message": {"text": DM_TEXT}},
        timeout=15,
    )
    print("private reply:", r.status_code, r.text)


@app.get("/webhook")
def verify():
    if (
        request.args.get("hub.mode") == "subscribe"
        and request.args.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return request.args.get("hub.challenge", ""), 200
    abort(403)


@app.post("/webhook")
def webhook():
    if not valid_signature(request):
        abort(403)

    data = request.get_json(silent=True) or {}
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "comments":
                continue
            v = change.get("value", {})
            comment_id = v.get("id")
            text = (v.get("text") or "").lower()
            commenter = (v.get("from") or {}).get("id")

            if not comment_id or comment_id in seen_comments:
                continue
            if commenter == IG_USER_ID:  # don't reply to own comments
                continue
            if KEYWORDS and not any(k.lower() in text for k in KEYWORDS):
                continue

            seen_comments.add(comment_id)
            reply_to_comment(comment_id)
            private_reply_dm(comment_id)

    return "ok", 200


@app.get("/")
def home():
    return "running", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

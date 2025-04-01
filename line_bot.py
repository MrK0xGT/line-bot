from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ReplyMessageRequest, PushMessageRequest
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import TextMessage
import schedule
import time
import threading
import random
import os

app = Flask(__name__)

# 從環境變數中獲取 Channel Access Token 和 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "your_channel_access_token")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "your_channel_secret")

# 初始化 Line Bot (v3)
configuration = Configuration()
configuration.access_token = LINE_CHANNEL_ACCESS_TOKEN
configuration.host = "https://api.line.me"  # 確保設置正確的 API 主機
line_bot_api = MessagingApi(configuration)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 儲存用戶 ID（用於推播）
user_ids = []

# 幽默的碎碎念訊息列表
funny_messages = [
    "滷小小碎碎念：今天有沒有吃滷肉飯呀？🍚 快去完成任務，晚上有驚喜哦！😉",
    "滷小小情勒時間：你今天有沒有偷懶呀？😏 快去完成任務，不然滷肉飯不給你吃！🍖",
    "滷小小提醒你：滷肉飯的香味在呼喚你～🍲 快去完成任務，我幫你留一份！😋",
    "滷小小碎碎念：今天天氣好適合吃滷肉飯！🌞 完成任務後一起去吃吧～🍚",
    "滷小小情勒你：別一直滑手機啦！📱 快去完成任務，不然滷小小要生氣了！😤"
]

# Webhook 路由，用於接收 Line 訊息
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理用戶發送的訊息
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    if user_id not in user_ids:
        user_ids.append(user_id)  # 儲存用戶 ID 用於推播

    user_message = event.message.text.lower()
    if "滷小小" in user_message:
        reply_text = "我是滷小小！今天要一起完成什麼任務呢？😋 快告訴我吧～🍖"
    elif "任務" in user_message:
        reply_text = "今天的任務是：吃一碗滷肉飯，然後告訴滷小小你有多開心！🍚 你完成了嗎？😉"
    elif "吃飯" in user_message or "滷肉飯" in user_message:
        reply_text = "哇！你提到滷肉飯了！🍲 滷小小也想吃～你今天吃的滷肉飯好吃嗎？😋"
    else:
        reply_text = "滷小小聽不懂啦～請說『滷小小』、『任務』或『滷肉飯』來跟我互動吧！🍖"

    # 使用 MessagingApi 發送回覆訊息
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
    )

# 定時推播訊息
def push_message():
    if user_ids:  # 確保有用戶 ID
        message = random.choice(funny_messages)  # 隨機選擇一條幽默訊息
        for user_id in user_ids:
            line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=message)]
                )
            )

# 排程定時推播（每天 12:00 和 18:00 推播）
schedule.every().day.at("12:00").do(push_message)
schedule.every().day.at("18:00").do(push_message)

# 啟動排程的背景執行緒
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分鐘檢查一次

if __name__ == "__main__":
    # 啟動排程執行緒
    threading.Thread(target=run_schedule, daemon=True).start()
    # 啟動 Flask 伺服器
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

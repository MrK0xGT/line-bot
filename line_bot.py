from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import schedule
import time
import threading
import random
import os
import logging

app = Flask(__name__)

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 從環境變數中獲取 Channel Access Token 和 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "your_channel_access_token")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "your_channel_secret")

# 初始化 Line Bot
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 儲存 OpenChat 的 chatId（用於推播）
chat_ids = []

# 幽默的碎碎念訊息列表
funny_messages = [
    "滷小 SMALL 碎碎念：今天有沒有吃滷肉飯呀？🍚 快去完成任務，晚上有驚喜哦！😉",
    "滷小 SMALL 情勒時間：你今天有沒有偷懶呀？😏 快去完成任務，不然滷肉飯不給你吃！🍖",
    "滷小 SMALL 提醒你：滷肉飯的香味在呼喚你～🍲 快去完成任務，我幫你留一份！😋",
    "滷小 SMALL 碎碎念：今天天氣好適合吃滷肉飯！🌞 完成任務後一起去吃吧～🍚",
    "滷小 SMALL 情勒你：別一直滑手機啦！📱 快去完成任務，不然滷小 SMALL 要生氣了！😤"
]

# Webhook 路由，用於接收 Line 訊息
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logger.info(f"Received webhook request with body: {body}")
    logger.info(f"Signature: {signature}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        logger.error(f"Invalid signature error: {str(e)}")
        abort(400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        abort(500)
    return 'OK'

# 處理用戶發送的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 檢查是否來自 OpenChat
    if event.source.type == "group" or event.source.type == "room":
        chat_id = event.source.group_id if event.source.type == "group" else event.source.room_id
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)  # 儲存 OpenChat 的 chatId 用於推播
            logger.info(f"Added chatId {chat_id} to chat_ids")

    user_id = event.source.user_id if event.source.type == "user" else None
    chat_id = event.source.group_id if event.source.type == "group" else event.source.room_id if event.source.type == "room" else None
    user_message = event.message.text.lower()
    logger.info(f"Received message from user {user_id} in chat {chat_id}: {user_message}")
    if "滷小 small" in user_message:
        reply_text = "我是滷小 SMALL！今天要一起完成什麼任務呢？😋 快告訴我吧～🍖"
    elif "任務" in user_message:
        reply_text = "今天的任務是：吃一碗滷肉飯，然後告訴滷小 SMALL 你有多開心！🍚 你完成了嗎？😉"
    elif "吃飯" in user_message or "滷肉飯" in user_message:
        reply_text = "哇！你提到滷肉飯了！🍲 滷小 SMALL 也想吃～你今天吃的滷肉飯好吃嗎？😋"
    else:
        reply_text = "滷小 SMALL 聽不懂啦～請說『滷小 SMALL』、『任務』或『滷肉飯』來跟我互動吧！🍖"

    # 使用 LineBotApi 發送回覆訊息
    logger.info(f"Replying to chat {chat_id} with: {reply_text}")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# 定時推播訊息到 OpenChat
def push_message():
    if chat_ids:  # 確保有 chatId
        message = random.choice(funny_messages)  # 隨機選擇一條幽默訊息
        for chat_id in chat_ids:
            logger.info(f"Pushing message to chat {chat_id}: {message}")
            line_bot_api.push_message(
                chat_id,
                TextSendMessage(text=message)
            )
    else:
        logger.warning("No chat_ids available for push message")

# 排程定時推播（以 UTC 時間為基準，對應台灣時間 12:00 和 18:00）
schedule.every().day.at("04:00").do(push_message)  # 台灣時間 12:00 (UTC 04:00)
schedule.every().day.at("10:00").do(push_message)  # 台灣時間 18:00 (UTC 10:00)

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

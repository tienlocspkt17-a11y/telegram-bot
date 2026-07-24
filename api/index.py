import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. Lấy thông tin từ cấu hình Vercel
# Hãy đảm bảo 3 dòng này y hệt như thế này, KHÔNG điền key thật vào đây
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_USERNAME = os.environ.get("BOT_USERNAME")

# Khởi tạo Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/api', methods=['POST', 'GET'])
def webhook():
    # Route GET để test xem server có sống không
    if request.method == 'GET':
        return "Bot is running on Vercel!"
    
    # 2. Xử lý tin nhắn từ Telegram (POST)
    update = request.get_json()
    if not update or "message" not in update:
        return jsonify(status="ok")

    message = update["message"]
    chat_id = message["chat"]["id"]
    chat_type = message["chat"]["type"]
    text = message.get("text", "")

    # Logic Group: Chỉ xử lý nếu có nhắc tên bot
    if chat_type in ['group', 'supergroup']:
        if BOT_USERNAME not in text:
            return jsonify(status="ok")
        text = text.replace(BOT_USERNAME, '').strip()

    if not text:
        return jsonify(status="ok")

    # 3. Gọi AI xử lý
    try:
        response = model.generate_content(text)
        reply_text = response.text
    except Exception as e:
        print(f"Lỗi AI: {e}")
        reply_text = "Hệ thống AI đang phản hồi chậm, bạn thử lại sau nhé."

    # 4. Trả lời lại qua Telegram API
    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": reply_text,
        "reply_to_message_id": message.get("message_id")
    }
    requests.post(send_url, json=payload)

    # Trả về HTTP 200 cho Telegram
    return jsonify(status="ok")

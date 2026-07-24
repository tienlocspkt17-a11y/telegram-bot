import os
import requests
from flask import Flask, request, jsonify
from google import genai # Sử dụng thư viện mới

app = Flask(__name__)

# 1. Lấy thông tin cấu hình
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_USERNAME = os.environ.get("BOT_USERNAME")

# Khởi tạo Gemini Client theo chuẩn mới
client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Định nghĩa Route: Bắt mọi đường link để tránh lỗi 404
@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def webhook(path):
    # Nếu truy cập bằng trình duyệt (GET)
    if request.method == 'GET':
        return jsonify(status="Thành công", message="Bot is running and waiting for Telegram webhook!")
    
    # Xử lý tin nhắn từ Telegram (POST)
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

    # 3. Gọi AI xử lý bằng cú pháp mới
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=text
        )
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

    # Cập nhật: Hỗ trợ tự động trả lời đúng luồng cho các Group có bật Topics (Forum)
    if message.get("is_topic_message") or message.get("message_thread_id"):
        payload["message_thread_id"] = message.get("message_thread_id")

    # Gửi tin nhắn và in kết quả ra Logs để bắt bệnh
    try:
        tg_response = requests.post(send_url, json=payload)
        print(f"Telegram API Trả về: {tg_response.status_code} - {tg_response.text}")
    except Exception as e:
        print(f"Lỗi kết nối đến Telegram: {e}")

    return jsonify(status="ok")

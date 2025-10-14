# linebot_gemini.py
from flask import abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import google.generativeai as genai

def main(request, **kwargs):
    # 取得主程式傳入的 LINE 與 Gemini 金鑰
    config=kwargs.get('config', {})
    secret=config.get('LINE_CHANNEL_SECRET')
    token=config.get('LINE_CHANNEL_ACCESS_TOKEN')
    gemini_api_key=config.get('GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))

    # 檢查必要參數
    if not secret or not token or not gemini_api_key:
        return {'error': 'Missing LINE or Gemini credentials'}

    # 初始化 LINE API 與 Webhook Handler
    line_bot_api=LineBotApi(token)
    handler=WebhookHandler(secret)

    # 設定 Gemini API 金鑰
    genai.configure(api_key=gemini_api_key)

    # 建立模型 (選用 gemini-2.0-flash 或 gemini-2.5-flash)
    model=genai.GenerativeModel('gemini-2.5-flash')

    # 註冊 LINE 訊息事件
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_text=event.message.text  # 使用者訊息
        system_instruction='你是一個繁體中文AI助理'
        try:
            # 呼叫 Gemini 生成回應
            response=model.generate_content([
                {'role': 'system', 'parts': [system_instruction]}, # 系統角色
                {'role': 'user', 'parts': [user_text]}
                ])
            reply_text=response.text.strip() if response.text else "（無法取得回覆）"
        except Exception as e:
            reply_text=f'⚠️ 錯誤：{e}'

        # 回覆給使用者
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
            )

    # 驗證簽章
    signature=request.headers.get('X-Line-Signature', '')
    body=request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400, 'Invalid signature')

    return {'status': 'ok'}

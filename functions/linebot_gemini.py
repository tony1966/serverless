# linebot_gemini.py
from flask import abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import google.generativeai as genai
import threading  

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
  
    # 建立一個在背景執行 Gemini 並推送訊息的函式
    def ask_gemini(user_id, user_text):
        system_instruction='你是一個繁體中文AI助理, 請以台灣人的習慣用語回答'
        try:
            # 每次呼叫時都建立模型物件以確保執行緒安全
            model=genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=system_instruction
                )
            # 呼叫 Gemini API (會在背景執行)
            response=model.generate_content(user_text)            
            reply_text=response.text.strip() if response.text else '(無法取得回覆)'
        except Exception as e:
            reply_text = f'處理您的請求時發生錯誤：{e}'
        # 使用 Push API 將 AI 生成結果回覆給使用者
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=reply_text)
            )    

    # 註冊 LINE 訊息事件 (偵測詢問)
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_text=event.message.text  # 取得使用者之詢問訊息
        user_id=event.source.user_id # 取得使用者的 user_id
        # 先回覆一個處理中的訊息避免逾時
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='好的，請稍候 ...')
            )
        # 建立一個新的執行緒來處理可能耗時的生成任務
        thread=threading.Thread(target=ask_gemini, args=(user_id, user_text))  
        thread.start()        

    # 驗證簽章
    signature=request.headers.get('X-Line-Signature', '')
    body=request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400, 'Invalid signature')
    # main() 立即傳回 'ok' 不等待 Gemini 回應
    return {'status': 'ok'}
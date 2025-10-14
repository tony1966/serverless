# linebot_gpt.py
from flask import abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI
import threading

def main(request, **kwargs):
    # 取得主程式傳入的 LINE 與 OpenAI 金鑰權杖
    config=kwargs.get('config', {})
    secret=config.get('LINE_CHANNEL_SECRET')
    token=config.get('LINE_CHANNEL_ACCESS_TOKEN')
    openai_api_key=config.get('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))

    # 檢查必要參數
    if not secret or not token or not openai_api_key:
        return {'error': 'Missing LINE or OpenAI credentials'}

    # 初始化 LINE API 與 Webhook Handler
    line_bot_api=LineBotApi(token)
    handler=WebhookHandler(secret)
    
    # 設定 OpenAI API 金鑰
    client=OpenAI(api_key=openai_api_key)

    # 建立一個在背景執行串接 GPT 並推送訊息的函式
    def ask_gpt(user_id, user_text):
        system_instruction='你是一個繁體中文AI助理, 請以台灣人的習慣用語回答'
        try:
            # 呼叫 OpenAI GPT 生成回應
            response=client.chat.completions.create(
                model='gpt-3.5-turbo',   # GPT 模型
                messages=[
                    {'role': 'system', 'content': '你是一個繁體中文AI助理'},
                    {'role': 'user', 'content': user_text}
                    ],
                #max_tokens=300
                )
            reply_text=response.choices[0].message.content
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
        thread=threading.Thread(target=ask_gpt, args=(user_id, user_text))
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
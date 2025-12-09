# send_ksml_books_messages.py
import asyncio
import sqlite3
from telegram import Bot

async def telegram_send_text(token, chat_id, text):
    """非同步傳送 Telegram 訊息"""
    try:
        bot=Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=text)
        return True
    except Exception as e:
        print(f"傳送失敗: {e}")
        return False

def main(request, **kwargs):
    DB_PATH='./serverless.db'
    config=kwargs.get('config', {})
    telegram_token=config.get('TELEGRAM_TOKEN')
    telegram_id=config.get('TELEGRAM_ID')
    if not telegram_token or not telegram_id:
        return '未設定 TELEGRAM_TOKEN 或 TELEGRAM_ID'
    try:  # 連線資料庫
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        cur.execute("SELECT borrow_books, reserve_books FROM ksml_books;")
        rows=cur.fetchall()
        conn.close()
    except Exception as e:
        return f'資料庫讀取失敗: {e}'
    if not rows:
        return '沒有任何資料可傳送'
    # 傳送訊息
    success_count=0
    fail_count=0
    for borrow_books, reserve_books in rows:
        for msg in [borrow_books, reserve_books]:
            if msg and msg.strip():
                ok=asyncio.run(telegram_send_text(telegram_token, telegram_id, msg))
                if ok:
                    success_count += 1
                else:
                    fail_count += 1
    return f'傳送完成：成功 {success_count} 筆，失敗 {fail_count} 筆'

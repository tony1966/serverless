# update_ksml_books.py
import sqlite3
from datetime import datetime, timedelta

def main(request, **kwargs):
    """
    POST 請求範例：
    {
        "account": "tony",
        "borrow_books": "書名1 (到期日 2025-10-22); 書名2 ...",
        "reserve_books": "書名A (已到館); 書名B (順位 2) ..."
    }
    """
    DB_PATH='./serverless.db'
    try:  # 從 POST 請求 body 中解析 JSON 格式資料並轉成 Python 字典
        data=request.get_json(force=True)
    except Exception as e:
        return {"status": "error", "message": f"解析 JSON 失敗: {str(e)}"}
    # 從字典中取得參數值
    account=data.get('account')
    borrow_books=data.get('borrow_books', '')
    reserve_books=data.get('reserve_books', '')
    # 檢查主鍵 account 
    if not account:
        return {"status": "error", "message": "缺少帳號資訊"}
    try:  # 更新 ksml_books 資料表
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        # 建立 ksml_books 資料表 (若不存在)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ksml_books (
                account TEXT PRIMARY KEY,
                borrow_books TEXT,
                reserve_books TEXT,
                updated_at TEXT
            )
        """)
        # 統一用 UTC 現在時間 + 8 取得台灣目前時間
        utc_now=datetime.utcnow()
        taiwan_now=utc_now + timedelta(hours=8)
        now_str=taiwan_now.strftime('%Y-%m-%d %H:%M:%S')
        # 使用 INSERT OR REPLACE 寫入紀錄，如果帳號已存在就更新
        cur.execute("""
            INSERT OR REPLACE INTO ksml_books (account, borrow_books, reserve_books, updated_at)
            VALUES (?, ?, ?, ?)
        """, (account, borrow_books, reserve_books, now_str))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"{account} 的資料已更新"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

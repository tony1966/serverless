# delete_record.py
import os
import sqlite3
from flask import redirect, request
from html import escape

def main(request, **kwargs):
    table=request.args.get('table', '').strip()
    pk=request.args.get('pk', '').strip()
    DB_PATH='./serverless.db'
    # 檢查參數
    if not table or not pk:
        return f'<p>缺少 table 或 pk 參數！<a href="/function/list_tables">返回列表</a></p>'
    # 檢查資料庫
    if not os.path.exists(DB_PATH):
        return f'<p>資料庫檔案 serverless.db 不存在！<a href="/function/list_tables">返回列表</a></p>'
    try:  # 刪除紀錄
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        # 安全檢查：確認 table 存在
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cur.fetchone():
            return f'<p>資料表 "{escape(table)}" 不存在！<a href="/function/list_tables">返回列表</a></p>'
        # 執行刪除
        cur.execute('DELETE FROM ksml_books WHERE account=?', (pk,))
        conn.commit()
        return redirect(f'/function/view_table?table={table}')
    except sqlite3.Error as e:
        return f'<p>刪除紀錄失敗：{escape(str(e))}</p><a href="/function/view_table?table={escape(table)}">返回</a>'
    finally:
        if 'conn' in locals():
            conn.close()

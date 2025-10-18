# drop_table.py
import os
import sqlite3
from flask import request, redirect

def main(request, **kwargs):
    # 解析 URL 參數取得資料表名稱
    query=request.query_string.decode('utf-8')
    params=parse_qs(query)
    table=params.get('table', [''])[0]
    DB_PATH='./serverless.db'
    # 檢查資料庫是否存在
    if not os.path.exists(DB_PATH):
        return '''
            <p>資料庫檔案 serverless.db 不存在！
            <a href="/function/list_tables">返回資料表列表</a></p>
            '''
    # 設定保護清單，避免刪除重要系統表
    protected=['call_stats']
    if table in protected:
        return f'''
            <p>資料表 {table} 為保護表，無法刪除！
            <a href="/function/list_tables">返回列表</a></p>
            '''
    try:
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        # 執行刪除資料表
        cur.execute(f'DROP TABLE IF EXISTS "{table}"')
        conn.commit()
        conn.close()
        # 刪除成功後返回資料表列表
        return f'''
            <p>資料表 {table} 已刪除成功！
            <a href="/function/list_tables">返回列表</a></p>
            '''
    except sqlite3.Error as e:
        return f'<p>刪除資料表 {table} 失敗: {str(e)}</p>'
    finally:
        if 'conn' in locals():
            conn.close()
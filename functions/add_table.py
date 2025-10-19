# add_table.py
import os
import sqlite3
from flask import request

def main(request, **kwargs):
    DB_PATH='./serverless.db'
    # 還沒送出表單 : 顯示建立表單頁面
    if request.method == 'GET':
        html=(
            "<h2>新增資料表</h2>"
            "<form method='post' action='/function/add_table'>"
            "<label>資料表名稱：</label><br>"
            "<input type='text' name='table' required><br><br>"
            "<label>欄位定義 (Schema, 以逗號分隔)：</label><br>"
            "<textarea name='schema' rows='4' cols='70' "
            "placeholder='例如：id INTEGER PRIMARY KEY, name TEXT, age INTEGER, height REAL' "
            "required></textarea><br><br>"
            "<input type='submit' value='建立資料表'>"
            "</form>"
            "<a href='/function/list_tables'>返回資料表列表</a>"
            )
        return html
    # 處理表單送出
    if request.method == 'POST':
        table=request.form.get('table', '').strip()
        schema=request.form.get('schema', '').strip()
        if not table or not schema:
            return '<p>請輸入資料表名稱與欄位定義！<a href="/function/add_table">返回</a></p>'
        if not os.path.exists(DB_PATH):
            return '''
                <p>資料庫檔案 serverless.db 不存在！
                <a href="/function/list_tables">返回</a></p>
                '''
        try: # 建立資料表
            conn=sqlite3.connect(DB_PATH)
            cur=conn.cursor()
            cur.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({schema});')
            conn.commit()
            conn.close()
            return f'''
                <p>資料表 <b>{table}</b> 建立成功！</p>
                <a href="/function/list_tables">返回資料表列表</a>
                '''
        except sqlite3.Error as e:
            return f'<p>建立資料表失敗：{str(e)} <a href="/function/add_table">返回</a></p>'
        finally:
            if 'conn' in locals():
                conn.close()            

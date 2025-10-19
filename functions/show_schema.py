# show_schema.py
import os
import sqlite3
from urllib.parse import parse_qs

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
    # 檢查 URL 參數中是否有 table 名稱
    if not table:
        return '''
        <p>缺少 table 參數！
        <a href="/function/list_tables">返回資料表列表</a></p>
        '''
    try:
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        # 檢查資料表是否存在
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,))
        exists=cur.fetchone()
        if not exists:
            conn.close()
            return f'''
            <p>資料表 <b>{table}</b> 不存在！
            <a href="/function/list_tables">返回資料表列表</a></p>
            '''
        # 取得欄位資訊
        cur.execute(f"PRAGMA table_info('{table}');")
        columns=cur.fetchall()
        # 取得 Schema 的 SQL
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table,))
        create_sql=cur.fetchone()[0]
        conn.close()
        # 產生 HTML
        html=f'<h2>資料表 {table} 結構 (Schema)</h2>'
        html += '<table border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse;">'
        html += '<tr><th>#</th><th>欄位名稱</th><th>資料型別</th><th>非空</th><th>預設值</th><th>主鍵</th></tr>'
        for col in columns:
            cid, name, ctype, notnull, dflt_value, pk=col
            html += f'<tr>'
            html += f'<td>{cid}</td>'
            html += f'<td>{name}</td>'
            html += f'<td>{ctype}</td>'
            html += f'<td>{"✓" if notnull else ""}</td>'
            html += f'<td>{dflt_value if dflt_value is not None else ""}</td>'
            html += f'<td>{"✓" if pk else ""}</td>'
            html += '</tr>'
        html += '</table>'
        # 顯示 CREATE TABLE 語法
        html += '<h3>CREATE TABLE SQL 語法</h3>'
        html += f'<pre style="background-color:#f4f4f4;padding:10px;">{create_sql}</pre>'
        # 導覽連結
        html += '<a href="/function/list_tables">返回資料表列表</a>'
        return html
    except sqlite3.Error as e:
        return f'<p>讀取資料表結構失敗：{str(e)}</p>'
    finally:
        if 'conn' in locals():
            conn.close()
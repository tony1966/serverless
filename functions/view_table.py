# view_table.py
import os
import sqlite3
import html
from urllib.parse import parse_qs, quote

def main(request, **kwargs):
    # 解析 URL 查詢參數 (?table=xxx&page=1)
    query=request.query_string.decode('utf-8')
    params=parse_qs(query)
    table=params.get('table', [''])[0]
    try:
        page=int(params.get('page', ['1'])[0])
        if page < 1:
            page=1
    except ValueError:
        page=1    
    DB_PATH='./serverless.db'
    ROWS_PER_PAGE=50  # 每頁顯示筆數
    # 檢查資料庫是否存在
    if not os.path.exists(DB_PATH):
        return '''
        <p>資料庫檔案 serverless.db 不存在！<a href="/function/list_tables">返回資料表列表</a></p>
        '''
    if not table:
        return '''
        <p>缺少 table 參數！<a href="/function/list_tables">返回資料表列表</a></p>
        '''
    try:
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        # 安全檢查 (避免惡意表名注入)
        cur.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table,))
        if not cur.fetchone():
            conn.close()
            return f'<p>資料表 "{html.escape(table)}" 不存在！</p>'
        # 取得欄位名稱
        cur.execute(f'SELECT * FROM "{table}" LIMIT 1;')
        colnames=[d[0] for d in cur.description] if cur.description else []
        # 計算總筆數
        cur.execute(f'SELECT COUNT(*) FROM "{table}";')
        total_rows=cur.fetchone()[0]
        total_pages=(total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
        # 取得當前頁的資料
        offset=(page - 1) * ROWS_PER_PAGE
        cur.execute(f'SELECT * FROM "{table}" LIMIT ? OFFSET ?;', (ROWS_PER_PAGE, offset))
        rows=cur.fetchall()
        conn.close()

        # 組成 HTML
        text=f'<h2>資料表 {html.escape(table)} 內容</h2>'
        text += '<table border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse;">'
        # 欄位列
        if colnames:
            text += '<tr>'
            text += ''.join(f'<th>{html.escape(c)}</th>' for c in colnames)
            text += '<th>刪除</th>'  # 新增刪除欄位
            text += '</tr>'
        else:
            text += '<tr><td colspan="99">（無欄位）</td></tr>'
        # 資料列
        if rows:
            for row in rows:
                text += '<tr>'
                for v in row:
                    text += f'<td>{html.escape(str(v)).replace("\n", "<br>")}</td>'
                # 假設第一個欄位是主鍵
                pk_value = quote(str(row[0]))
                text += f'<td><a href="/function/delete_record?table={quote(table)}&pk={pk_value}" ' \
                        f'onclick="return confirm(\'確定要刪除此筆紀錄嗎？\')">刪除</a></td>'
                text += '</tr>'
        else:
            text += '<tr><td colspan="99">（本頁無資料）</td></tr>'
        text += '</table>'
        # 分頁列
        text += f'<p>共 {total_rows} 筆資料，頁 {page}/{total_pages}</p>'
        text += '<div style="margin:10px 0;">'
        if page > 1:
            text += f'<a href="/function/view_table?table={quote(table)}&page={page-1}">上一頁</a> '
        if page < total_pages:
            text += f'<a href="/function/view_table?table={quote(table)}&page={page+1}">下一頁</a>'
        text += '</div>'
        text += '<a href="/function/list_tables">返回資料表列表</a>'
        return text
    except Exception as e:
        return f'<p>讀取資料時發生錯誤：{html.escape(str(e))}</p>'
    finally:
        if 'conn' in locals():
            conn.close()

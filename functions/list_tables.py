# list_tables.py
import os
import sqlite3

def main(request, **kwargs):    
    protected=[]  # 被保護的資料名稱清單 (不顯示)    
    DB_PATH='./serverless.db'  # 資料庫路徑
    # 檢查資料庫檔案是否存在
    if not os.path.exists(DB_PATH):
        html='''
            <p>資料庫檔案 serverless.db 不存在！
            <a href="/function/list_functions">函式列表</a></p>
            '''
        return html
    # 連線資料庫
    try:
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        # 取得所有非系統資料表
        cur.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
            AND name NOT LIKE 'sqlite_%' ORDER BY name;
            """)
        rows=cur.fetchall()
        tables=[r[0] for r in rows]
        html='<h2>資料表列表</h2>'
        html += '<table border="1" cellspacing="0" cellpadding="6" '+\
                'style="border-collapse: collapse;">'
        html += '<tr><th>資料表名稱</th><th>記錄筆數</th><th>Schema</th>' +\
                '<th>檢視記錄</th><th>匯出</th><th>刪除</th></tr>'
        if not tables:
            html += '<tr><td colspan="6">目前無任何資料表</td></tr>'
        else:  # 遍歷所有非系統資料表
            for table in tables:
                if table in protected:  # 不顯示被保護資料表                    
                    continue                
                try:  # 取得該資料表的記錄筆數 (若失敗則顯示 '-')
                    cur2=conn.cursor()
                    cur2.execute(f"SELECT COUNT(*) FROM \"{table}\";")
                    cnt=cur2.fetchone()[0]
                except Exception:  # 資料表無紀錄
                    cnt='-'
                html += '<tr>'
                html += f'<td>{table}</td>'
                html += f'<td align="right">{cnt}</td>'
                html += f'<td><a href="/function/show_schema?table={table}">顯示</a></td>'
                html += f'<td><a href="/function/view_table?table={table}">檢視</a></td>'
                html += f'<td><a href="/function/export_table?table={table}">CSV</a></td>'
                html += f'<td><a href="/function/drop_table?table={table}" onclick=' +\
                        f'"return confirm(\'確定要刪除資料表 {table} 嗎？\')">刪除</a></td>'
                html += '</tr>'
        html += '</table>'
        # 管理連結：新增資料表、回到主頁、登出等
        html += '<br><a href="/function/add_table">新增資料表</a> '
        html += '<a href="/function/execute_sql">執行 SQL</a> '
        html += '<a href="/function/list_functions">返回函式列表</a> '
        html += '<a href="/logout">登出</a>'
        conn.close()
        return html
    except sqlite3.Error as e:
        return f'<p>連線資料庫失敗 {str(e)}</p>'
    finally:
        if 'conn' in locals():
            conn.close()    
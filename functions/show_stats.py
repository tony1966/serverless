# show_stats.py
import sqlite3

DB_PATH='./serverless.db'

def main(request, **kwargs):
    # 取得主程式傳遞之 protected 參數 (被保護之管理模組名稱)
    protected=kwargs.get('protected', [])    
    # 連線資料庫
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute('SELECT func_name, call_count FROM call_stats ORDER BY func_name')
    rows=cursor.fetchall()
    conn.close()
    # 產生回應表格
    html='<h2>函式呼叫統計</h2>'
    html += '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">'
    html += '<tr><th>函式名稱</th><th>呼叫次數</th></tr>'
    for func_name, count in rows:
        if func_name in protected:  # 不顯示管理模組之被呼叫次數
            continue
        html += f'<tr><td>{func_name}</td><td>{count}</td></tr>'
    html += '</table>'
    html += '<br><a href="/function/clear_stats">清除統計資料</a> '
    html += '<a href="/function/list_functions">返回函式列表</a>'
    return html



    # 連線資料庫
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute('SELECT func_name, call_count FROM call_stats ORDER BY func_name')
    rows=cursor.fetchall()
    conn.close()
    # 產生回應表格
    html='<h2>函式呼叫統計</h2>'
    html += '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">'
    html += '<tr><th>函式名稱</th><th>呼叫次數</th></tr>'
    for func_name, count in rows:
        html += f'<tr><td>{func_name}</td><td>{count}</td></tr>'
    html += '</table>'
    html += '<br><a href="/function/clear_stats">清除統計資料</a> '
    html += '<a href="/function/list_functions">返回函式列表</a>'
    return html

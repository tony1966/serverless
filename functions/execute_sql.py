# execute_sql.py
import os
import sqlite3
from flask import request
from html import escape

def main(request, **kwargs):
    DB_PATH='./serverless.db'
    # 還沒送出表單 (GET)：顯示 SQL 輸入頁面
    if request.method == 'GET':
        html=(
            "<h2>執行 SQL 指令</h2>"
            "<form method='post' action='/function/execute_sql'>"
            "<label>輸入 SQL 指令：</label><br>"
            "<textarea name='sql' rows='6' cols='80' "
            "placeholder='例如：SELECT * FROM call_stats;' required></textarea><br><br>"
            "<input type='submit' value='執行'>"
            "</form>"
            "<a href='/function/list_tables'>返回資料表列表</a>"
        )
        return html  # Removed conn.close() since conn is not defined
    # 處理表單送出 (POST)：執行 SQL 指令
    if request.method == 'POST':
        sql=request.form.get('sql', '').strip()  # 取出 sql 欄位
        if not sql:
            return '<p>請輸入 SQL 指令！<a href="/function/execute_sql">返回</a></p>'
        if not os.path.exists(DB_PATH):
            return (
                '<p>資料庫檔案 serverless.db 不存在！'
                '<a href="/function/list_tables">返回</a></p>'
            )
        try:  # 執行 SQL 指令 
            conn=sqlite3.connect(DB_PATH)  # 建立連線與 cursor
            cur=conn.cursor()
            # SELECT 查詢 : 執行查詢後取出所有結果
            if sql.lower().startswith('select'):
                cur.execute(sql)
                rows=cur.fetchall()
                columns=[desc[0] for desc in cur.description]  # 取得欄位名稱
                # 將查詢結果轉成 HTML 表格
                if not rows:
                    result="<p>查無資料。</p>"
                else:
                    result='<table border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse;">'
                    result += "<tr>" + "".join(f"<th>{escape(col)}</th>" for col in columns) + "</tr>"
                    for row in rows: 
                        result += "<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in row) + "</tr>"
                    result += "</table>"
                conn.close()  # 關閉資料庫連線
                return (
                    f"<h2>SQL 查詢結果</h2>"
                    f"<p><b>指令：</b> {escape(sql)}</p>"
                    f"{result}"
                    "<br><a href='/function/execute_sql'>返回</a>"
                )
            else:  # 其他非 SELECT 指令 (INSERT, UPDATE, DELETE, DROP/CREATE TABLE) 
                cur.execute(sql)
                conn.commit()
                affected=cur.rowcount
                conn.close()
                return (
                    f"<p>SQL 指令執行成功！（影響 {affected} 筆紀錄）</p>"
                    f"<p><b>指令：</b> {escape(sql)}</p>"
                    "<a href='/function/execute_sql'>返回</a>"
                )
        except sqlite3.Error as e:
            conn.close()  # 關閉資料庫連線
            return f"<p>SQL 執行錯誤：{escape(str(e))}</p><a href='/function/execute_sql'>返回</a>"
# export_table.py
import os
import sqlite3
import csv
from io import StringIO
from flask import Response, request

def main(request, **kwargs):
    # 解析 URL 查詢參數 (?table=xxx)
    table=request.args.get('table')
    if not table:
        return '<p>未指定資料表名稱！<a href="/function/list_tables">返回列表</a></p>'
    DB_PATH='./serverless.db'
    # 檢查資料庫是否存在   
    if not os.path.exists(DB_PATH):
        return '<p>資料庫檔案 serverless.db 不存在！<a href="/function/list_tables">返回列表</a></p>'
    try:
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        # 取得欄位名稱
        try:
            cur.execute(f'PRAGMA table_info("{table}")')
            columns_info=cur.fetchall()
            if not columns_info:
                return f'<p>資料表 {table} 不存在！<a href="/function/list_tables">返回列表</a></p>'
            columns=[col[1] for col in columns_info]  # col[1] 是欄位名稱
        except Exception as e:
            return f'<p>取得欄位失敗: {str(e)}</p>'
        # 取得所有資料
        try:
            cur.execute(f'SELECT * FROM "{table}"')
            rows=cur.fetchall()
        except Exception as e:
            return f'<p>讀取資料失敗: {str(e)}</p>'
        # 將資料寫入 CSV
        output=StringIO()
        writer=csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)
        csv_data=output.getvalue()
        output.close()
        # 回傳 CSV 給瀏覽器下載
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{table}.csv"'}
            )   
    except sqlite3.Error as e:
        return f'<p>連線資料庫失敗 {str(e)}</p>'
    finally:
        if 'conn' in locals():
            conn.close()

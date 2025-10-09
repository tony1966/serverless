# clear_stats.py
import sqlite3
from flask import jsonify, session

DB_PATH='./serverless.db'

def main(request, **kwargs):
    # 權限檢查確保只有登入用戶能清除呼叫統計
    if not session.get('authenticated'):
        return jsonify({'error': 'Authentication required'}), 401
    # 清除 call_stats 資料表
    try:
        conn=sqlite3.connect(DB_PATH)
        cursor=conn.cursor()
        cursor.execute('DELETE FROM call_stats')
        conn.commit()
        conn.close()
        return f'''
        <p>已成功清除呼叫統計資料.</p>
        <a href="/function/show_stats">返回呼叫統計列表</a>
        '''
    except Exception as e:
        return jsonify({'error': f'清除呼叫統計失敗: {e}'}), 500

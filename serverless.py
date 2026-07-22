# serverless.py
from flask import Flask, request, jsonify, session, redirect
import importlib.util
import os
import logging
from functools import wraps
from dotenv import dotenv_values
import sqlite3

# 指定呼叫統計資料庫位置 (必須在 init_db() 定義之前)
DB_PATH='./serverless.db'

def check_auth():  # 檢查使用者是否已登入
    return session.get('authenticated') == True

def init_db():  # 初始化資料庫（冪等，每次啟動皆執行）
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    # 呼叫統計表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_stats (
            func_name TEXT PRIMARY KEY,
            call_count INTEGER NOT NULL
        )
    """)
    # API Token 認證表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            token      TEXT    NOT NULL UNIQUE,
            owner      TEXT    NOT NULL,
            is_active  INTEGER NOT NULL DEFAULT 1,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

def record_call(func_name):  # 紀錄函式呼叫次數
    if not os.path.exists(DB_PATH):  # 若資料庫檔不存在就建立 
        init_db()    
    try:
        conn=sqlite3.connect(DB_PATH)
        cursor=conn.cursor()
        cursor.execute('SELECT call_count FROM call_stats WHERE func_name=?', (func_name,))
        row=cursor.fetchone()
        if row:  # 有找到 : 呼叫次數增量 1
            cursor.execute('UPDATE call_stats SET call_count=call_count + 1 WHERE func_name=?', (func_name,))
        else:  # 沒找到 : 第一次呼叫設為 1
            cursor.execute('INSERT INTO call_stats (func_name, call_count) VALUES (?, 1)', (func_name,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f'Failed to record call stats for {func_name}: {e}')

def require_api_token(f):  # 裝飾器：驗證請求 Header 中的 X-API-Key
    @wraps(f)
    def decorated(*args, **kwargs):
        token=request.headers.get('X-API-Key')
        if not token:  # Header 遺失
            return jsonify({'error': 'Missing API token', 'hint': 'Provide X-API-Key header'}), 401
        conn=sqlite3.connect(DB_PATH)
        cursor=conn.cursor()
        cursor.execute(
            'SELECT id FROM api_tokens WHERE token=? AND is_active=1',
            (token,)
        )
        row=cursor.fetchone()
        conn.close()
        if not row:  # Token 不存在或已停用
            return jsonify({'error': 'Invalid or inactive API token'}), 401
        return f(*args, **kwargs)
    return decorated

app=Flask(__name__)
# 初始化資料庫
init_db()  
# 從 .env 讀取權杖 (密碼) 與金鑰
config=dotenv_values('.env')
SECRET_TOKEN=config.get('SECRET_TOKEN')  # 易記的令牌 (類似密碼)
SECRET_KEY=config.get('SECRET_KEY')  # 簽章加密用的金鑰
app.secret_key=SECRET_KEY  # 用來簽章與驗證 session cookie
# 指定函式模組所在的資料夾
FUNCTIONS_DIR=os.path.expanduser('./functions')
# 指定錯誤日誌檔 (在目前工作目錄下)
logging.basicConfig(filename='serverless_error.log', level=logging.ERROR)
# 需要 Session 驗證的管理函式列表
PROTECTED_FUNCTIONS=['list_functions',
                     'add_function',
                     'save_function',
                     'edit_function',
                     'update_function',
                     'delete_function',
                     'show_stats',
                     'clear_stats',
                     'list_tables',
                     'add_table',
                     'drop_table',
                     'view_table',
                     'show_schema',
                     'export_table',
                     'execute_sql',
                     'delete_record'
                     ]
# 授權方式：Session 登入（管理者）或有效 API Token，擇一通過即可

# 根目錄
@app.route("/")
def index():
    if check_auth(): # 若已登入導向函式列表頁面        
        return redirect('/function/list_functions')
    else:  # 否則顯示登入提示        
        return '<p>Serverless API 運行中! <a href="/login">登入系統</a></p>' 

# 登入管理功能
@app.route('/login', methods=['GET', 'POST'])
def login():
    # GET 請求 : 顯示登入頁面
    if request.method == 'GET':  
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>系統登入</title></head>
        <body>
            <h2>系統登入</h2>
            <form method="post">
                <input type="password" name="token" placeholder="請輸入密碼" required>
                <button type="submit">登入</button>
            </form>
        </body>
        </html>
        '''
    # POST 請求 : 處理登入請求
    if request.is_json:  # JSON 登入 
        token=request.json.get('token')
    else:   # 表單登入
        token=request.form.get('token')    
    if token == SECRET_TOKEN:  # 驗證登入密碼
        # 將登入狀態儲存在瀏覽器的 session cookie 中 (以明碼方式儲存)
        # Flask 會用金鑰對資料進行簽章 (非加密) 確保內容未被竄改
        session['authenticated']=True    
        # 回應登入成功
        if request.is_json:  
            return jsonify({'message': '登入成功'})
        else:
            return '<p>登入成功！<a href="/function/list_functions">查看函式列表</a></p>'
    else:  # 密碼錯誤 : 回應登入失敗訊息
        if request.is_json:
            return jsonify({'message': '登入失敗'}), 401
        else:
            return '<p>登入失敗！<a href="/login">重新登入</a></p>', 401

# 登出管理功能 
@app.route('/logout')
def logout():
    session.clear()  # 清除伺服端 Flask session 字典中的所有鍵值對
    return '<p>已登出！<a href="/login">重新登入</a></p>'

# 動態載入 & 執行函式模組 (支援 RESTful) 
@app.route('/function/<func_name>', defaults={'subpath': ''}, methods=['GET', 'POST'])
@app.route('/function/<func_name>/<path:subpath>', methods=['GET', 'POST'])
def handle_function(func_name, subpath):  # 傳入 subpath 支援 RESTful
    # 1. 統一授權驗證：Session 登入 OR 有效 API Token，擇一通過
    is_session_auth=check_auth()  # 確認 Session 狀態
    is_token_auth=False
    if not is_session_auth:  # 無 Session 時，嘗試 API Token 驗證
        api_token=request.headers.get('X-API-Key')
        if api_token:
            conn=sqlite3.connect(DB_PATH)
            cursor=conn.cursor()
            cursor.execute(
                'SELECT id FROM api_tokens WHERE token=? AND is_active=1',
                (api_token,)
            )
            is_token_auth=cursor.fetchone() is not None
            conn.close()
    is_authorized=is_session_auth or is_token_auth
    # 2. 管理模組：需要授權（Session 或 Token）
    if func_name in PROTECTED_FUNCTIONS and not is_authorized:
        return jsonify({'error': 'Authentication required', 'login_url': '/login'}), 401
    # 3. 一般函式：同樣需要授權
    if func_name not in PROTECTED_FUNCTIONS and not is_authorized:
        return jsonify({'error': 'Missing API token', 'hint': 'Provide X-API-Key header'}), 401
    # 4. 取得檔案路徑
    func_path=os.path.join(FUNCTIONS_DIR, f'{func_name}.py')
    if not os.path.isfile(func_path):  # 模組檔案不存在 -> 回 404
        return jsonify({'error': f'Function "{func_name}" not found'}), 404
    try:
        # 5. 動態載入模組 (絕對路徑)
        spec=importlib.util.spec_from_file_location(func_name, func_path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # 6. 檢查模組中有無 main() 函式 :
        if not hasattr(module, 'main'):  # 模組中無 main() 函式
            return jsonify({'error': f'Module "{func_name}" has no main()'}), 400
        # 7. 將 subpath 加入 request 中 (支援 RESTful)
        request.view_args['subpath']=subpath
        # 8. 記錄呼叫統計 (除了統計查詢自身避免無限循環)
        if func_name not in PROTECTED_FUNCTIONS:
            record_call(func_name)        
        # 9. 執行模組中的函式 (傳入模組可能需要的參數-但不一定會用到) :        
        result=module.main(request, config=config, protected=PROTECTED_FUNCTIONS)
        # 10. 傳回函式執行結果
        return result 
    except Exception as e:
        logging.exception(f'Error in function {func_name}\n{e}')  # 紀錄錯誤於日誌
        return jsonify({'error': 'Function execution failed : ' + e}), 500

if __name__ == '__main__':
    app.run(debug=True)

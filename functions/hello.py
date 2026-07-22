# hello.py
def main(request, **kwargs):
    # 讀取系統注入的設定（如果有的話）
    config=kwargs.get('config', {})    
    # 這裡可以安全地取得環境變數
    db_timeout=config.get('DB_TIMEOUT', 30)
    # 先從請求字串擷取 name 參數 (?name=)
    name=request.args.get('name')
    if not name:   # 請求字串沒有 name 參數
        # 嘗試從 RESTful 子路徑 (例如 /function/hello/Tony) 中擷取 name 參數 
        subpath=request.view_args.get('subpath', '')   # 取得 Flask 傳入的 subpath 參數
        parts=subpath.strip('/').split('/')   # 拆解成串列例如 ['Tony']
        if parts:
            name=parts[0]   # 取第一段作為 name (例如 'Tony')
    # 從 request 也沒有找到
    if not name:
        name='World'    
    result=f"Hello {name}! Database timeout is set to {db_timeout}s."
    return result
# update_function.py
import os
from flask import jsonify

def main(request, **kwargs):
    if request.method != 'POST':
        return '請使用 POST 方法'
    # 同時支援 JSON（API Client）與 form（瀏覽器）兩種輸入格式
    is_json=request.is_json
    if is_json:
        data=request.get_json()
        # 相容 func_name（deploy.py）與 module_name（瀏覽器表單）兩種欄位名稱
        module_name=(data.get('func_name') or data.get('module_name') or '').strip()
        code=(data.get('code') or '').strip()
    else:
        module_name=request.form.get('module_name', '').strip()
        code=request.form.get('code', '').strip()
    # 檢查檔案名稱合法性
    if not module_name.isidentifier():
        msg='錯誤：模組名稱須為合法的 Python 識別字'
        return jsonify({'error': msg}) if is_json else f'<p>{msg}</p>'
    if '/' in module_name or '\\' in module_name or '..' in module_name:
        msg='錯誤：無效的函式名稱'
        return (jsonify({'error': msg}) if is_json else msg), 400  # 避免目錄穿越攻擊
    if not code:
        msg='錯誤：模組內容不得為空'
        return jsonify({'error': msg}) if is_json else f'<p>{msg}</p>'
    # 組成檔案路徑
    filename=f'./functions/{module_name}.py'
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)  # 若檔名一樣覆蓋原內容, 否則建立新模組
        if is_json:
            return jsonify({'message': f'模組 {module_name} 已成功更新', 'func_name': module_name})
        return f'模組 {module_name} 已成功更新!<br><br><a href="/function/list_functions">返回函式列表</a>'
    except Exception as e:
        if is_json:
            return jsonify({'error': f'更新失敗：{e}'}), 500
        return f'更新失敗：{e}'

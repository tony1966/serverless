# add.py
def main(request, **kwargs):
    try:
        # 從 request.args 取得參數 a 和 b，並轉為 int
        a = int(request.args.get("a", 0))
        b = int(request.args.get("b", 0))
        result = a + b
        return f"{a} + {b} = {result}"
    except (TypeError, ValueError):
        return "錯誤：請提供有效的數字參數 a 與 b，例如 /function/add?a=1&b=2"
import random
import http.client
import json
import time
import os
# uiautomator2工具函数

## 定义一个点击函数参数有text:元素文本 timeout:等待时间  return:无
## 等待时间0-timeout秒 如果找到元素就点击并返回True 没找到就返回False
def click_element(d,text, timeout=5):
    if d(text=text).wait(timeout = timeout):
        d(text=text).click()
        print(f"点击{text}成功")
        return True
    else:
        print(f"没找到{text}按钮")
        return False

## 获取当前页面结构
def get_current_page(d):
    return d.dump_hierarchy()
   
## 滑动到页面最顶部
def scroll_to_top(d, max_swipe=15):
    import time

    print("开始滑动到顶部...")

    last_xml = ""

    for i in range(max_swipe):
        xml = d.dump_hierarchy()

        # ✅ 页面不再变化 → 到顶了
        if xml == last_xml:
            print("已到页面顶部")
            return True

        last_xml = xml

        # 👉 向下滑（看到更上面）
        d.swipe(500, 400, 500, 1600, 0.2)
        time.sleep(0.5)

    print("达到最大滑动次数（可能已到顶）")
    return False

## 滑动到页面最底部
def scroll_to_top(d, max_swipe=15):
    import time

    print("开始滑动到顶部...")

    last_xml = ""

    for i in range(max_swipe):
        xml = d.dump_hierarchy()

        # ✅ 页面不再变化 → 到顶了
        if xml == last_xml:
            print("已到页面顶部")
            return True

        last_xml = xml

        # 👉 向下滑（看到更上面）
        d.swipe(500, 400, 500, 1600, 0.2)
        time.sleep(0.5)

    print("达到最大滑动次数（可能已到顶）")
    return False

# soul

# 定义一个跳过坐标打卡函数 如果出现坐标打卡字样 
# 点击横坐标随机 点击纵坐标中间位置
def click_skip_coordinate(d):
    if d(text="坐标打卡").wait(timeout=1):
        x = random.randint(0, d.info['displayWidth'])
        y = d.info['displayHeight'] // 2
        d.click(x, y)
        print("跳过坐标打卡")

## soul判断当前页面是否是聊天页面 
def is_chat_page(d):
    return (
        d(text="发送").exists and
        d(className="android.widget.EditText").exists
    )
## soul判断 Activity（最底层🔥） xx页面
def is_chat_page2(d):
    # current = d.app_current()
    # print(current)
    # {'package': 'cn.soulapp.android', 'activity': '.component.chat.ConversationActivity', 'pid': 12685}
    return (    
        "ConversationActivity" in d.app_current()['activity']
    )




## 源数据 ：[{'top': 1038, 'type': 'text', 'content': '[吃瓜]', 'sender': 'me', 'timestamp': '3月17日 20:46'}, {'top': 439, 'type': 'text', 'content': '哈喽 你在什么地方呢', 'sender': 'other'}, {'top': 518, 'type': 'text', 'content': '龙岗五和', 'sender': 'me'}, {'top': 719, 'type': 'text', 'content': '你呢', 'sender': 'me'}, {'top': 920, 'type': 'text', 'content': '龙华民治', 'sender': 'other'}, {'top': 1121, 'type': 'text', 'content': '那很近', 'sender': 'me'}, {'top': 1322, 'type': 'text', 'content': '但这个地图显示 11km  🤔', 'sender': 'me'}, {'top': 1716, 'type': 'text', 'content': '我找对象的，你是真心找对象的吗', 'sender': 'other'}]

## 目标数据 
# [
#     {
#       "role": "user", user/assistant   // user --> 'sender': 'other'  // assistant --> 'sender': 'me'
#       "content": "现在是刚加好友第一次聊天请你主动打招呼开启话题"
#     }
#   ]

## 处理从soul读取的源数据-->目标数据:提供ai请求messages
## 合并连续同一sender的消息，按top排序（若存在）以保证时间顺序
def process_messages(messages):
    """
    messages: list of dicts with at least 'sender' and 'content'.
    sender == 'other' -> role 'user', else -> 'assistant'.
    If messages empty, return [system, user_initial_prompt].
    Otherwise prepend system and return merged conversation.
    """
    system = {
        "role": "system",
        "content": "你是微信聊天中的真实男生只回一句话不超过15字像随手发的可以表达态度可以口语可以不完整句不要解释不要写分析不要出现我是不要套话不要用表情 尽量往暧昧聊"
    }
    user_initial = {
        "role": "user",
        "content": "现在是刚加好友第一次聊天请你主动打招呼开启话题"
    }

    if not messages:
        return [system, user_initial]

    # Work on a copy. If 'top' exists on all messages, sort by it (top ascending -> earlier first).
    msgs = list(messages)
    if msgs and all('top' in m for m in msgs):
        msgs = sorted(msgs, key=lambda m: m.get('top', 0))

    merged = []
    for m in msgs:
        role = "user" if m.get('sender') == 'other' else "assistant"
        content = (m.get('content') or '').strip()
        if not content:
            continue
        if not merged:
            merged.append({"role": role, "content": content})
        else:
            if merged[-1]['role'] == role:
                # merge consecutive same-role messages with a space separator
                merged[-1]['content'] = merged[-1]['content'] + " " + content
            else:
                merged.append({"role": role, "content": content})

    # Prepend system role
    return [system] + merged


def has_unread_messages(d):
    # 这个函数需要根据soul的界面元素来判断是否有未读消息
    # 这里假设有一个元素resourceId="cn.soulapp.android:id/unread_indicator"表示有未读消息
    return d(resourceId="cn.soulapp.android:id/unread_indicator").exists


import http.client

def ai_chat(messages):
    messages = process_messages(messages)
    # 将 HTTPSConnection 改为 HTTPConnection
    conn = http.client.HTTPConnection("192.168.190.99", 1234)
    payload = json.dumps({
        "model": "Gemma 3 4B",
        "temperature": 0.9,
        "max_tokens": 40,
        "stream": False,
        "reasoning": {
            "enabled": False
        },
        "messages": messages
    })
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }
    conn.request("POST", "/v1/chat/completions", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    ai_response = json.loads(data.decode("utf-8"))['choices'][0]['message']['content']
    print("AI回复:", ai_response)
    return ai_response

## 获取当前应用包名等相关信息
def get_current_app_info(d):
    return d.app_current()

## 打印当前页面元素
def print_current_page_elements(d):
    # 打印当前页面所有元素（xml）
    xml = d.dump_hierarchy()
    print(xml)

## 重启应用
def restart_app(d, package_name):
    d.app_stop(package_name)
    time.sleep(1)
    d.app_start(package_name)
    print(f"已重启应用: {package_name}")

# -------------------------
# 坐标点击/监听/坐标库
# -------------------------

def _coords_file_path(coords_file: str | None = None) -> str:
    """坐标库文件路径（默认 logging/common/coords.json 同目录）。"""
    if coords_file:
        return os.path.abspath(coords_file)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "coords.json")


def load_coords(coords_file: str | None = None) -> dict:
    path = _coords_file_path(coords_file)
    if not os.path.exists(path):
        return {"coords": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f) or {"coords": {}}


def save_coords(data: dict, coords_file: str | None = None) -> None:
    path = _coords_file_path(coords_file)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_coord(name: str, x: int, y: int, coords_file: str | None = None) -> None:
    data = load_coords(coords_file)
    data.setdefault("coords", {})
    data["coords"][name] = {"x": int(x), "y": int(y)}
    save_coords(data, coords_file)


def get_coord(name: str, coords_file: str | None = None) -> tuple[int, int] | None:
    data = load_coords(coords_file)
    c = (data.get("coords") or {}).get(name)
    if not c:
        return None
    return int(c["x"]), int(c["y"])


def click_xy(d, x: int, y: int, *, name: str | None = None, delay: float = 0.0, save: bool = False, coords_file: str | None = None):
    """点击指定坐标。可选保存到 coords.json。"""
    if delay and delay > 0:
        time.sleep(delay)
    d.click(int(x), int(y))
    if name:
        print(f"点击坐标: {name} ({int(x)},{int(y)})")
        if save:
            set_coord(name, int(x), int(y), coords_file)
    else:
        print(f"点击坐标: ({int(x)},{int(y)})")
    return True


def click_coord_name(d, name: str, *, delay: float = 0.0, coords_file: str | None = None):
    """按坐标名点击（从 coords.json 取坐标）。"""
    xy = get_coord(name, coords_file)
    if not xy:
        print(f"坐标名不存在: {name} (file={_coords_file_path(coords_file)})")
        return False
    x, y = xy
    return click_xy(d, x, y, name=name, delay=delay, save=False, coords_file=coords_file)


def _copy_to_clipboard(text: str):
    """复制到剪贴板（Windows 优先用 clip；失败则仅打印）。"""
    try:
        # Windows: echo xxx | clip
        os.system(f"echo {text} | clip")
        return True
    except Exception:
        return False


def watch_click_and_copy(
    d,
    *,
    name_prefix: str = "coord",
    interval: float = 0.2,
    coords_file: str | None = None,
    save: bool = True,
    copy_format: str = "{name}: ({x},{y})",
):
    """监听你手动点击屏幕的位置，自动打印/复制，并可写入 coords.json。

    说明：uiautomator2 没有稳定的“全局触摸事件订阅”，这里采用轮询 last_click 坐标的方式。
    个别设备/版本可能不支持 last_click；不支持时会提示并退出。

    copy_format 示例：
      - "{name}: ({x},{y})"  -> 复制形如：coord_1: (100,200)
      - "{\"name\":\"{name}\",\"x\":{x},\"y\":{y}}" -> 复制 json 片段
    """

    if not hasattr(d, "last_click"):
        print("当前设备对象不支持 d.last_click，无法监听点击。")
        return

    idx = 1
    prev = None
    print("开始监听点击坐标（手动点击手机/模拟器屏幕）。按 Ctrl+C 停止。")

    try:
        while True:
            cur = d.last_click
            if cur and cur != prev:
                prev = cur
                x, y = int(cur[0]), int(cur[1])
                name = f"{name_prefix}_{idx}"
                idx += 1

                msg = copy_format.format(name=name, x=x, y=y)
                print(msg)
                _copy_to_clipboard(msg)

                if save:
                    set_coord(name, x, y, coords_file)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("已停止监听点击坐标")
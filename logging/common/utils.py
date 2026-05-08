import random
import http.client
import json
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

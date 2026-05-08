import sys
sys.stdout.reconfigure(encoding='utf-8')
import uiautomator2 as u2
import time
import common.utils as utils
import chatSoul as chatSoul
import common.getSoulMsg as getSoulMsg
d = u2.connect_usb()

def main():
    print("设备连接成功:", d)
    
    # 是否在前台（是否新开启）
    is_foreground = d.app_current()['package'] == "cn.soulapp.android"

    # 如果不在前台才启动 # 等待加载
    if not is_foreground:
        d.app_start("cn.soulapp.android")
        time.sleep(2)

    print("等待加载完成")

    # 等待元素出现1
    if not is_foreground:
        utils.click_element(d,"我知道了")

    # 跳过坐标打卡
    if not is_foreground:
        utils.click_skip_coordinate(d)

    # 等待元素出现2 附近的人（在一步中随机出现，优先级最高）
    is_chat = utils.click_element(d,"立即私聊")

    # 可能进入立即匹配聊天界面
    if is_chat:
        print("立即匹配聊天界面")

    #判断是否有未读消息
    msgCount = getSoulMsg.get_message_count(d)
    if msgCount > 0:
        print("有未读消息", msgCount)
        is_chat = True
        utils.click_element(d,"消息")
        utils.scroll_to_top(d)
        getSoulMsg.click_first_unread_on_screen(d)
    else:
        print("没有未读消息")

    # 没进入聊天界面点击星球 且没有未读消息
    if not is_chat:
        utils.click_element(d,"星球")
        # 点击灵魂匹配
        utils.click_element(d,"灵魂匹配")
        # 等待页面跳转到聊天界面
        while not utils.is_chat_page2(d):
            time.sleep(1)

    # 进入聊天流程
    chatSoul.chat(d)

# 执行3次main函数，每次间隔5秒
if __name__ == "__main__":
    for i in range(3):
        print(f"第{i+1}次执行main函数")
        main()
        time.sleep(5)

import uiautomator2 as u2
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import common.utils as utils
import common.game as game
d = u2.connect_usb()
import os

print("设备连接成功:", d)

# 烽火璀璨游戏的日常流程


# 如果不在前台才启动 # 等待加载
if d.app_current()['package'] != "com.MsgSender.io.fycc":
    d.app_start("com.MsgSender.io.fycc")
    time.sleep(1)

# print("等待加载完成")

# get_current_app_info
# app_info = utils.get_current_app_info(d)
# print("当前应用信息:", app_info)
# 当前应用信息: {'package': 'com.MsgSender.io.fycc', 'activity': 'com.cocos.game.AppActivity', 'pid': 0}

# utils.click_element(d, "进入游戏")

# print_current_page_elements
# utils.print_current_page_elements(d)
# d.click(720, 2050)

# 模板图路径使用基于当前文件的绝对路径，避免受启动目录影响
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

game.click_icon(d, os.path.join(BASE_DIR, "icon", "战场.png"))

game.click_text(d,"进入游戏")
game.click_icon(d, os.path.join(BASE_DIR, "icon", "战场.png"))
game.click_text(d,"商城")
game.click_icon(d, os.path.join(BASE_DIR, "icon", "看视频得奖励列表.png"))


import uiautomator2 as u2
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import common.utils as utils
import common.game as game
d = u2.connect_usb()
import os

# print("设备连接成功:", d)

# 烽火璀璨游戏的日常流程


# 如果不在前台才启动 # 等待加载
# if d.app_current()['package'] != "com.MsgSender.io.fycc":
#     d.app_start("com.MsgSender.io.fycc")
#     time.sleep(1)

## 重启app
utils.restart_app(d, "com.MsgSender.io.fycc")

# print("等待加载完成")

# get_current_app_info
# app_info = utils.get_current_app_info(d)
# print("当前应用信息:", app_info)
# 当前应用信息: {'package': 'com.MsgSender.io.fycc', 'activity': 'com.cocos.game.AppActivity', 'pid': 0}


# print_current_page_elements
# utils.print_current_page_elements(d)
# d.click(720, 2050)

# 模板图路径使用基于当前文件的绝对路径，避免受启动目录影响
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 等待3秒 游戏loading动画
time.sleep(3)

# 等待检查更新界面消失：检查是否有这个文字 没有的话等待3秒 ；进入循环每秒检查一次 直到消失
# game.wait_for_text_disappear(d,"更新",60 ,2)
    
# 有一步错误则退出 这次步骤
if not game.click_icon(d,os.path.join(BASE_DIR, "icon", "进入游戏.png")):
    sys.exit("点击进入游戏失败")
time.sleep(1)

# 当出现连接失败  ，30s未消失  10s秒未出现 则重启程序
# while not game.wait_for_text_disappear(d, "连接失败",disappear_timeout=30):
#     print("网络连接失败，请检查网络 重启当前程序程序")
#     os.system("python3 fhcc.py")
#     sys.exit()

## 是否出现文字游戏维护中 重新则退出
if game.wait_for_text_appear(d, "游戏维护中", timeout=3):
    sys.exit("游戏维护中，退出程序")
    
if not game.click_icon(d, os.path.join(BASE_DIR, "icon", "战场.png")):
    sys.exit("点击战场图标失败")

if not game.click_icon(d,os.path.join(BASE_DIR, "icon", "商城.png")):
    sys.exit("点击商城失败")

if not game.click_icon(d, os.path.join(BASE_DIR, "icon", "看视频得奖励列表.png")):
    sys.exit("点击看视频得奖励列表图标失败")

# 点击刷新卡广告
# if not game.click_icon(d, os.path.join(BASE_DIR, "icon", "刷新卡广告.png")):
#     sys.exit("点击刷新卡广告图标失败")


# # # 等待文字消失：跳过 等待“首次出现”的最长时间45秒(广告30s 广告加载给15s 识别不到文字的保底方法)
# if not game.wait_for_text_disappear(d, "跳过" ,appear_timeout=45):
#     sys.exit("等待跳过广告失败")

# # # 点击关闭广告
# if not game.click_icon(d, os.path.join(BASE_DIR, "icon", "关闭广告.png")):
#     sys.exit("点击关闭广告图标失败")
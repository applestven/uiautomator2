import uiautomator2 as u2
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import common.utils as utils
import common.game as game
d = u2.connect_usb()

print("设备连接成功:", d)

# 如果不在前台才启动 # 等待加载
if d.app_current()['package'] != "com.MsgSender.io.fycc":
    d.app_start("com.MsgSender.io.fycc")
    time.sleep(1)


game.click_text(d, "进入游戏")

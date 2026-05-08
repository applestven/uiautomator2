import uiautomator2 as u2
import common.getSoulMsg as getSoulMsg
import common.sendMsgSoul as sendMsgSoul
import soul as soul
import common.utils as utils

# 进入聊天流程
generate_response = "在干嘛" # 这里应该是调用AI模型生成回复的函数

def chat(d):
    # 获取用户基础信息 
    # user_info = getSoulMsg.get_chat_info(d)
    # print("用户信息:", user_info)

    # 获取用户的最新消息
    # latest_other_messages = getSoulMsg.get_latest_other_messages(d,10)
    # print("用户最新消息:", latest_other_messages)
    latest_other_messages = getSoulMsg.get_chat_messages_stable(d,10)
    print("用户最新10条消息:", latest_other_messages)


    # 最新消息为空数组 则返回主页  这里可能有bug 比如被别的app 拦截了视图 则会发两次打招呼消息
    # if not latest_other_messages:
    #     print("没有最新消息")
    #     return False

    # 查数据库是否有历史聊天记录 
    # print("通过数据库获取用户是否有历史聊天记录")

    # 如果有聊天记录 将最新消息 + 数据库历史聊天记录 合成一个完整的聊天记录chat_messages
    # 如果没有聊天记录 则获取所有的聊天记录chat_messages 
    # chat_messages = [1, 2] #假设这是所有的聊天记录

    # ai根据用户画像-提供的形象特质  以及 chat_messages 生成回复
    # ai_response = generate_response
    # print("AI回复:", ai_response)

    # 处理messages
    messages = utils.process_messages(latest_other_messages)
    print("处理后的消息:", messages)

    # 调用AI模型
    ai_response = utils.ai_chat(messages)

    # 输入框输入
    callBackFlag = sendMsgSoul.send_message(d, ai_response)

    # 发送成功则存储到数据库 并返回主页
    if callBackFlag:
        print("发送成功")
        sendMsgSoul.go_back(d)
        return True

    else:
        print("发送失败")
        sendMsgSoul.go_back(d)
        return False

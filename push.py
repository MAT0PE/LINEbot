from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, LocationMessage, TextSendMessage
import json, re
import database
from datetime import datetime, timedelta

f = open('creds.txt', 'r')
first, second = f.read().split("\n")[:-1]
f.close()
line_bot_api = LineBotApi(first)

def send_everybody():
    lineids = database.get_all_nonmuted_lineids()
    try:
        for lineid in lineids:
            data = database.get_today(lineid)
            text = "最高気温：{0}\n最低気温：{1}\n風：{2}\n朝：{3}　{4}\n昼：{5}　{6}\n夜：{7}　{8}".format(data["temperature"][0], data["temperature"][1], data["wind"], data["rain"][1], data["comments"][0], data["rain"][2], data["comments"][1], data["rain"][3], data["comments"][2])
            line_bot_api.push_message(lineid, TextSendMessage(text=text))
        print(datetime.now()+timedelta(hours=9), " -> sent")
    except Exception as e:
        print(str(e))


if __name__ == '__main__':
    send_everybody()

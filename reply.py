from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, LocationMessage, TextSendMessage
import json, re
import database

app = Flask(__name__)

f = open('creds.txt', 'r')
first, second = f.read().split("\n")[:-1]
f.close()
line_bot_api = LineBotApi(first)
handler = WebhookHandler(second)

@app.route("/tenki/privacy_policy.html")
def privacy_policy_html():
    return app.send_static_file("privacy_policy.html")

@app.route("/tenki/privacy_policy.css")
def privacy_policy_css():
    return app.send_static_file("privacy_policy.css")

@app.route("/tenki/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    today = ['天気', '教えて', '教えて！', '教えろ', '教えろ！', '天気を教えて', '天気を教えろ', '天気教えて', '天気教えろ', '天気を教えて！', '天気を教えろ！', '天気教えて！', '天気教えろ！', '今日', '今日の天気', '今日の天気を教えて', '今日の天気を教えろ', '今日の天気教えて', '今日の天気教えろ', '今日の天気を教えて！', '今日の天気を教えろ！', '今日の天気教えて！', '今日の天気教えろ！']
    tomorrow = ['明日', '明日の天気', '明日の天気は？', '明日の天気を教えて', '明日の天気を教えろ', '明日の天気教えて', '明日の天気教えろ', '明日の天気を教えて！', '明日の天気を教えろ！', '明日の天気教えて！', '明日の天気教えろ！']
    postalcode = database.lineid_to_postalcode(event.source.user_id)
    print('postalcode:', postalcode)
    if postalcode:
        if event.message.text in today:
            data = database.get_today(event.source.user_id)
            if data:
                text = "最高気温：{0}\n最低気温：{1}\n風：{2}\n朝：{3}　{4}\n昼：{5}　{6}\n夜：{7}　{8}".format(data["temperature"][0], data["temperature"][1], data["wind"], data["rain"][1], data["comments"][0], data["rain"][2], data["comments"][1], data["rain"][3], data["comments"][2])
            else:
                text = "もう少しお待ちください。"
        elif event.message.text in tomorrow:
            data = database.get_tomorrow(event.source.user_id)
            if data:
                text = "最高気温：{0}\n最低気温：{1}\n風：{2}\n朝：{3}　{4}\n昼：{5}　{6}\n夜：{7}　{8}".format(data["temperature"][0], data["temperature"][1], data["wind"], data["rain"][1], data["comments"][0], data["rain"][2], data["comments"][1], data["rain"][3], data["comments"][2])
            else:
                text = "もう少しお待ちください。"
        elif re.fullmatch(r'[0-9０-９]{3}(-|ー|–|−)[0-9０-９]{4}', event.message.text):
            postalcode = event.message.text.translate(str.maketrans({'０':'0', '１':'1', '２':'2', '３':'3', '４':'4', '５':'5', '６':'6', '７':'7', '８':'8', '９':'9', 'ー':'-', '–':'-', '−':'-'}))
            urls = database.fetch_urls(postalcode)
            if urls:
                if event.source.user_id not in database.get_all_lineids():
                    database.create_user(event.source.user_id)
                database.change_postalcode(event.source.user_id, postalcode)
                text = '郵便番号の登録を{}に変更しました'.format(postalcode)
                if postalcode not in database.get_all_postalcodes():
                    url1, url2 = urls
                    database.insert_record_pu(postalcode, url1, url2)
                    database.insert_record(postalcode)
            else:
                text = '有効な郵便番号を入力して下さい。'
        else:
            text = "申し訳ありませんが、このアカウントでは個別の返信ができません\uDBC0\uDC92\n今日の天気を知りたい場合は「天気」、「天気を教えて」、「今日」など、明日の天気を知りたい場合は「明日」、「明日の天気」、「明日の天気を教えろ！」などとおっしゃって下さい。\n郵便番号を変更したい場合は郵便番号をハイフン付きで送るか、位置情報を送信して下さい\n現在は{}が登録されています".format(postalcode)
    elif re.fullmatch(r'[0-9０-９]{3}(-|ー|–|−)[0-9０-９]{4}', event.message.text):
        postalcode = event.message.text.translate(str.maketrans({'０':'0', '１':'1', '２':'2', '３':'3', '４':'4', '５':'5', '６':'6', '７':'7', '８':'8', '９':'9', 'ー':'-', '–':'-', '−':'-'}))
        urls = database.fetch_urls(postalcode)
        if urls:
            if event.source.user_id not in database.get_all_lineids():
                database.create_user(event.source.user_id)
            database.change_postalcode(event.source.user_id, postalcode)
            text = '郵便番号の登録を{}に変更しました'.format(postalcode)
            if postalcode not in database.get_all_postalcodes():
                url1, url2 = urls
                database.insert_record_pu(postalcode, url1, url2)
                database.insert_record(postalcode)
        else:
            text = '有効な郵便番号を入力して下さい。'
    else:
        text = "郵便番号をハイフン付きで送信するか位置情報を送信することで郵便番号を登録することができます。"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text))


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    postalcode = re.search(r'[0-9]{4}-[0-9]{3}', event.message.address[::-1]).group()[::-1]
    if event.source.user_id not in database.get_all_lineids():
        database.create_user(event.source.user_id)
    database.change_postalcode(event.source.user_id, postalcode)
    text = '郵便番号の登録を{}に変更しました'.format(postalcode)
    if postalcode not in database.get_all_postalcodes():
        url1, url2 = database.fetch_urls(postalcode)
        database.insert_record_pu(postalcode, url1, url2)
        database.insert_record(postalcode)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text))


if __name__ == "__main__":
    app.run(port="8000")

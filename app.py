import os
import sys
import requests

from bs4 import BeautifulSoup
from flask import Flask, request, abort
from rent591 import *

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = Flask(__name__)


@app.route("/callback", methods=['POST'])
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
        abort(400)

    return 'OK'


def androidweekly():
    target_url = 'http://androidweekly.net'
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ''

    cnt = 0
    for item in soup.select('.latest-stuff .latest-issue .rahmen .sections .article-headline'):
        title = item.text
        link = item['href']
        data = '{}\n{}\n\n'.format(title, link)
        content += data
        cnt += 1
        if cnt >= 5:
            break
    return content


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    event_message = event.message.text.strip().split(' ')
    main_action = event_message[0]
    if main_action == 'androidweekly':
        content = androidweekly()
        print(content)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    if main_action == '591':
        argu = event_message[1:]
        items = rent_591_object_list(argu)
        content = rent_591_object_list_tostring(items)
        print(content)
        if content == '':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='找不到物件。'))
            return 0
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()

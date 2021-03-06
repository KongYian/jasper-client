# -*- coding: utf-8-*-

import json
import logging
import sys
from uuid import getnode as get_mac
from app_utils import create_reminder
import requests

reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('..')

WORDS = ["EMOTIBOT"]
SLUG = "emotibot"


def chat(texts, config, mic, bot):
    msg = ''.join(texts)
    try:
        url = "http://idc.emotibot.com/api/ApiKey/openapi.php"
        register_data = {
            "cmd": "chat",
            "appid": config['appid'],
            "userid": str(get_mac())[:32],
            "text": msg,
            "location": config['location']
        }
        r = requests.post(url, params=register_data)
        jsondata = json.loads(r.text)
        result = ''
        responds = []
        if jsondata['return'] == 0:
            cmd = jsondata.get('data')[0]['cmd']
            if isSupported(cmd):
                responds.append(jsondata.get('data')[0].get('value'))
                result = '\n'.join(responds)
                if jsondata.get('data')[0]['cmd'] == 'reminder':
                    data = jsondata.get('data')[0]
                    remind_info = data.get('data').get('remind_info')
                    remind_event = remind_info[0].get('remind_event')
                    remind_time = remind_info[0].get('remind_time')

                    if not create_reminder(remind_event, remind_time):
                        result = '\n'.join('创建提醒失败了')
                if cmd != "picture":
                    mic.say(result)
                sendMoreToBot(jsondata.get('data')[0], bot, mic)
            else:
                mic.say(u"抱歉,不支持的功能")
        else:
            result = u"抱歉, 请稍后再试试."
            mic.say(result)
    except Exception, e:
        print(e)
        mic.say(u"抱歉, 我的大脑短路了,请稍后再试试.")


def isSupported(cmd):
    if cmd == "taxi" or \
       cmd == "kuaidi" or \
       cmd == "music" or \
       cmd == "audio":
        return False
    else:
        return True


def sendMoreToBot(data, bot, mic):
    if data['cmd'] == "news":
        news_items = data.get('data').get('items')
        news = "news:"
        for item in news_items:
            news = news + item["title"] + ":" + item["link"] + ".\n"
        bot.sendMessage(news)
    elif data['cmd'] == "concert":
        concert_items = data.get('data').get('items')
        concerts = "concerts:"
        for item in concert_items:
            concerts = concerts + item["title"] + "."\
                + item["time"] + "."\
                + item["location"] + "."
        bot.sendMessage(concerts)
    elif data['cmd'] == "picture":
        mic.say(u"已发送")
        bot.sendMessage(data.get('value'))


def handle(text, mic, profile, bot=None):
    logger = logging.getLogger(__name__)

    if SLUG not in profile or \
       'appid' not in profile[SLUG] or \
       'location' not in profile[SLUG]:
        mic.say(u"插件配置有误，插件使用失败")
        return
    if not isValid(text):
        logger.info("use as default handler")
        chat(text, profile[SLUG], mic, bot)
        return

    mic.say(u'hello')
    if 'robot_name' in profile:
        persona = profile['robot_name']

    while True:
        try:
            threshold, transcribed = mic.passiveListen(persona)
        except Exception:
            threshold, transcribed = (None, None)

        if not transcribed or not threshold:
            continue

        input = mic.activeListen()

        if input and any(ext in input for ext in [u"结束", u"退出", u"停止"]):
            return
        else:
            chat(input, profile[SLUG], mic, bot)


def isValid(text):
    return any(word in text for word in [u"小影", u"小影机器人"])

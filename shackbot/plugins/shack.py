import asyncio
from datetime import date, datetime

import bs4
import requests

from bot import Bot
from registry import bot_command
from storage import store


bot = Bot()


@bot_command('open')
def open(parsed, user, target, text):
    try:
        response = requests.get('http://shackspace.de/sopen/text/en')
        response.raise_for_status()
        reply = response.content.decode()
    except:
        bot.say(target, 'Error ({}) while trying to reach the shack :('.format(
            response.status_code if response else 'ouch!')
        )
    else:
        if 'open' in reply:
            bot.say(target, 'shack is open')
        elif 'close' in reply:
            bot.say(target, 'shack is closed')
        else:
            bot.say(target, 'Defuq? I have no idea.')


@bot_command('plenum')
def next_plenum(parsed, user, target, text):
    try:
        response = requests.get('http://shackspace.de/nextplenum/text/iso')
        response.raise_for_status()
        next_date = datetime.strptime(response.content.decode().strip(), '%Y-%m-%d')
        delta = (next_date.date() - date.today()).days

        if delta == 0:
            reply_string = "Heute ist Plenum!"
        elif delta == 1:
            reply_string = "Morgen ist Plenum!"
        else:
            reply_string = "Das nächste Plenum ist in {delta} Tagen, am {date}.".format(
                delta=delta, date=next_date.strftime('%d.%m')
            )
        bot.say(target, reply_string)
    except:
        bot.say(target, 'Heute Plenum, morgen Plenum, das sind doch bürgerliche Kategorien.')


@bot_command(['plenumlink', 'plenumslink'])
def link_plenum(parsed, user, target, text):
    try:
        bot.say(target, requests.get('http://shackspace.de/nextplenum/http300/current').url)
    except:
        bot.say(target, 'Plenum ist ja eigentlich auch überbewertet.')


@bot_command('online')
def online(parsed, user, target, text):
    try:
        bot.say(target, requests.get('http://shackproxy.unimatrix21.org/shackles/online').content.decode())
    except:
        bot.say(target, 'rashfael: Das tut schon wieder nicht.')


def check_site():
    try:
        response = requests.get('http://shackspace.de/sopen/text/en')
        response.raise_for_status()
        new = response.content.decode().strip()
        old = store.get('shack.state')
        old = old.decode() if old else ''

        if not 'no data' in new:
            store.set('shack.state', new)
            if 'open' in new and 'closed' in old:
                bot.say('#shackspace-dev', 'The shack has been opened.')
            elif 'open' in old and 'closed' in new:
                bot.say('#shackspace-dev', 'The shack has been closed.')
    except:
        pass

    asyncio.get_event_loop().call_later(60, check_site)


def check_blog():
    response = requests.get('http://shackspace.de/?feed=rss2')
    soup = bs4.BeautifulSoup(response.text, 'lxml-xml')
    latest_post = soup.rss.find('item')
    last_post = store.get('shack.blogpost')
    last_post = last_post.decode() if last_post else ''

    if last_post != latest_post.link:
        bot.say('#shackspace-dev', 'New blog post! »{title}« by {author}: {url}'.format(
            title=latest_post.title,
            author=latest_post.find('creator').text,
            url=latest_post.link,
        ))
        store.set('shack.blogpost', latest_post.link)
    asyncio.get_event_loop().call_later(60, check_blog)


asyncio.get_event_loop().call_later(60, check_site)
asyncio.get_event_loop().call_later(60, check_blog)

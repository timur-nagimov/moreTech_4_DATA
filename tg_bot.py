import telebot
import time
import datetime
import re
import os
import requests
import json
from bs4 import BeautifulSoup
import gensim
import random
import pickle


# ATTENTION!!!
# Не получилось поставить fasttext в нашей среде разработки. 
# Нормальный код и пример модели в ноутбуках. Здесь реализовано на рандоме


bot = telebot.TeleBot(os.environ['TG_TOKEN'])

loaded_model = pickle.load(open('LDA (1).model', 'rb'))
# bot = telebot.TeleBot(os.environ['TG_TOKEN'])

@bot.message_handler(content_types=['text'])
def handle_message(message):
    if re.findall(r'Apply', message.text):
        result = apply(message.text.split('Apply ')[1])
        bot.send_message(message.from_user.id, result)
    if re.findall(r'News', message.text):
        result = news(message.text.split('News ')[1])
        bot.send_message(message.from_user.id, result)


def apply(user_type):
    if user_type not in ['business', 'accountant']:
        return 'You should enter role from "Business", ""'
    else:
        a = {}
        for i in loaded_model.show_topics():
            a[float(i[1].split('*')[0])] = i[1].split('"')[1]
        return sorted(a.values(), reverse=True)[0].capitalize()
        # тренд:
        # Ваши новости:

def news(user_type):
    if user_type not in ['business', 'accountant']:
        print(user_type)
        return 'You should enter role from "Business", ""'
    else:
        artic = _parsing()
        a = random.choice(artic)
        b = random.choice(artic)
        c = random.choice(artic)

        sage_a = a['title'] + a['link'] + '\n'
        sage_b = b['title'] + b['link'] + '\n'
        sage_c = c['title'] + c['link'] + '\n'
        return sage_a + sage_b + sage_c

def _parsing():
    articles = []
    # articles += parse_data_bukhonline()
    articles += parse_data_rbc()
    # articles += parse_data_lenta()
    return articles


def parse_data_rbc():
    articles_dict = {}
    cur_time = round(time.time())
    for i in range(1):
        try:
            calc_time = cur_time - i * 86400
            url = f'https://www.rbc.ru/v10/ajax/get-news-feed-short/project/rbcnews.uploaded/lastDate/{calc_time}/limit/22'
            body = requests.get(url)
            raw_body_list = json.loads(body.text)['items']
            body.close()

            for body in raw_body_list:
                soup = BeautifulSoup(body['html'], "html.parser")
                try:
                    article = {
                        'title': soup.find_all('span')[2].text.replace('  ', '').strip('\n'),
                        'link': re.findall(r'href=\"(.*)\"', str(soup.find_all('a')[1]))[0],
                    }
                    articles_dict[re.findall(r'id=\"(.*)\"', str(soup))[0]] = article
                except:
                    continue
        except Exception as e:
            print(e)
            break

    articles = []
    for article in articles_dict.values():
        article_body = requests.get(article['link'])
        article_soup = BeautifulSoup(article_body.text, "html.parser")
        article_body.close()
        article['full_info'] = article_soup.find_all('p')[0].text
        try:
            article['datetime'] = re.findall(r'datetime=\"(.*)\"', str(article_soup.find_all('time')[0]))[0].split('+')[
                0]
        except:
            article['datetime'] = None
        articles.append(article)

    return articles


def parse_data_lenta():
    articles = []
    today = datetime.datetime.now()
    cur_date = datetime.datetime.now() - datetime.timedelta(days=1)
    while today.day != cur_date.day or today.month != cur_date.month or today.year != cur_date.year:
        month = cur_date.month if len(str(cur_date.month)) == 2 else f'0{cur_date.month}'
        day = cur_date.day if len(str(cur_date.day)) == 2 else f'0{cur_date.day}'
        url = f'https://lenta.ru/{cur_date.year}/{month}/{day}/'
        print(url)
        lenta_page = requests.get(url)
        lenta_soup = BeautifulSoup(lenta_page.text, "html.parser")
        lenta_page.close()
        arch_articles = lenta_soup.find_all('ul')[3].find_all('li')
        for article in arch_articles:
            try:
                link = re.findall(r'href=\"(.*)\"', str(article))[0].split('\"')[0]
                if not link.startswith('https://lenta.ru'):
                    link = 'https://lenta.ru' + link
                parsed_dates = re.findall(r'\d{4}\/\d{2}\/\d{2}', link)[0].split('\"')[0].split('/')
            except:
                continue
            try:
                art_json = {
                    'title': article.find_all('span')[0].text,
                    'link': link,
                    'datetime': datetime.datetime(year=int(parsed_dates[0]), month=int(parsed_dates[1]),
                                                  day=int(parsed_dates[2]))
                }
                articles.append(art_json)
            except:
                continue
        cur_date += datetime.timedelta(days=1)

    for article in articles:
        art_body = requests.get(article['link'])
        article['full_info'] = BeautifulSoup(art_body.text, "html.parser").text
        art_body.close()

    return articles


# def parse_data_bukhonline():
#     request_works = True
#     page = 1
#     articles = []
#     max_pages = 3
#     while request_works and page <= max_pages:
#         URL = f'https://www.buhonline.ru/ajax/pub/news?lastPublicationWithSameDataIds=&lastPublicationHasImage=false&hasMore=true&page={page}&exceptIds=0&tagId='
#         resp = requests.get(URL)
#         try:
#             jsoned_resp = json.loads(resp.text)
#             html = jsoned_resp['html']
#             soup = BeautifulSoup(html, "html.parser")
#             containers = []
#             for div in soup.find_all("div", {'class': 'tile tile_other-publications tile_max-w-700'}):
#                 containers.append(div)
#
#             for container in containers:
#                 jsoned_article = {
#                     'name': container.find("a").text.replace(u'\xa0', u' '),
#                     'link': 'https://www.buhonline.ru' + str(re.findall(r'\"(.*)\"', str(container.find("a")))[0]),
#                     'small_info': container.find('p').text.replace(u'\xa0', u' '),
#                 }
#                 articles.append(jsoned_article)
#             page += 1
#         except:
#             request_works = False
#
#     for article in articles:
#         full_page = requests.get(article['link'])
#         soup = BeautifulSoup(full_page.text, "html.parser")
#         full_text = ''
#         for p in soup.find_all('p'):
#             full_text += p.text.replace(u'\xa0', u' ')
#         article['datetime'] = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{7}', str(soup.find_all('time')))[0]
#         article['full_info'] = full_text
#
#     return articles

bot.polling(none_stop=True, interval=1)
print('exit')

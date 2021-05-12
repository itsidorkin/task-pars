#!/usr/bin/env python3
import calendar
import datetime
import sys
from asyncio import ensure_future, gather, get_event_loop

import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta


def get_url(date):
    """
    :param date: Дата публикации картинки
    :return: Ссылка на картинки опубликованные в указанную дату
    """
    next_date = date + relativedelta(months=1)
    return 'https://www.smashingmagazine.com/{}/{:02}/desktop-wallpaper-calendars-{}-{}/'.format(
        date.year, date.month, calendar.month_name[next_date.month], next_date.year)


async def fetch(url, session):
    """
    :param url: Ссылка на картинку
    :param session: Интерфейс для выполнения HTTP-запросов
    :return: Ожидание получения ответа
    """
    async with session.get(url) as response:
        return await response.read()


async def run_check(pics):
    """
    :param pics: Список всех ссылок на картинки удовлетворяющие требованиям (дата, разрешение)
    :return: Ожидание выполнения списка запланированных задач
    """
    tasks = []
    async with ClientSession() as session:
        for j in pics:
            task = ensure_future(fetch(j, session))  # преобразует ссылку в задачу
            tasks.append(task)
        return await gather(*tasks)


def main():
    date, resolution = sys.argv[1:]
    y = int(date[2:])
    m = int(date[:2])
    # y = 2020
    # m = 4
    # resolution = '1280x1024'
    date = datetime.date(y, m, 1)
    url = get_url(date)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')  # получаем код страницы
    div = soup.find('div', class_='c-garfield-the-cat')  # Находим div в котором находятся ссылки
    pic_url = []
    pic_name = []
    for i in div.find_all('a', href=True):  # Находим сами ссылки
        if resolution in i['href']:  # Если в тексте ссылки находится требуемое разрешение, то забираем эту ссылку
            pic_url.append(i['href'])

            k = 0
            for j in i['href'][::-1]:  # Отсчитываем с конца количество символов до первого встречного слэша
                if j == '/':
                    break
                k += 1
            pic_name.append(i['href'][len(i['href']) - k:])  # Сохраняем имя картинки
    future = ensure_future(run_check(pic_url))
    k = 0
    for i in get_event_loop().run_until_complete(future):  # Запускаем список запланированных задач и получаем ответ
        out = open("{}".format(pic_name[k]), "wb")
        out.write(i)
        out.close()
        k += 1


if __name__ == '__main__':
    main()

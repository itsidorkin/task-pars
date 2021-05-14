#!/usr/bin/env python3
import argparse
import calendar
import datetime
from asyncio import get_event_loop, gather, ensure_future

import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta


def get_url(date):
    """
    :param date: Дата публикации изображения
    :return: Ссылка на изображения опубликованные в указанную дату
    """
    date = datetime.date(int(date[-4:]), int(date[:-4]), 1)
    next_date = date + relativedelta(months=1)

    return 'https://www.smashingmagazine.com/{}/{:02}/desktop-wallpaper-calendars-{}-{}/'.format(
        date.year, date.month, calendar.month_name[next_date.month], next_date.year)


async def fetch(url, session):
    """
    :param url: Ссылка на изображение
    :param session: Интерфейс для выполнения HTTP-запросов
    :return: Формирует ответ запроса
    """
    async with session.get(url) as response:
        if response.status == 200:
            return await response.read()


async def run_check(pics):
    """
    :param pics: Список всех ссылок на изображения удовлетворяющие требованиям (дата, разрешение)
    :return: Возвращает список awaitable объектов (запланированых задач)
    """
    tasks = []
    async with ClientSession() as session:
        for j in pics:
            task = ensure_future(fetch(j, session))  # преобразует ссылку в задачу
            tasks.append(task)
        return await gather(*tasks)


def is_date(parser, date):
    """
    :param parser: Объект парсер
    :param date: Дата
    :return: Проверяет аргумет date на соотвествие формату "дата" и возвращает его
    """
    try:
        datetime.datetime.strptime(date, '%m%Y')
    except ValueError:
        parser.error("Неверный формат даты MMYYYY")
    if int(date[-4:]) > datetime.datetime.now().year:
        parser.error("Отсутствуют изображения из будущего")
    return date


def is_resolution(parser, resolution):
    """
    :param parser: Объект парсер
    :param resolution: Разрешение
    :return: Проверяет аргумет resolution на соотвествие формату "разрешение" и возвращает его
    """
    try:
        length, width = [int(i) for i in resolution.split('x')]
        if length < 1 or width < 1:
            parser.error("Неверный формат разрешения ?*x?*")
    except ValueError:
        parser.error("Неверный формат разрешения ?*x?*")
    return resolution


def main():
    # Организуем работу с командной строкой и получаем аргументы дата/разрешение
    parser = argparse.ArgumentParser(usage='Save pictures from www.smashingmagazine.com')
    parser.add_argument('date', type=lambda x: is_date(parser, x))
    parser.add_argument('resolution', type=lambda x: is_resolution(parser, x))
    args = parser.parse_args()
    date = args.date
    resolution = args.resolution

    # resolution = '1280x1024'
    # date = '32012'

    # Получаем код страницы нужной даты и все ссылки на изображения
    url = get_url(date)
    response = requests.get(url)
    if response.status_code != 200:
        print(response.status_code, url)
        parser.error("Что-то не так. (возможно такой ссылки не существут)")
    soup = BeautifulSoup(response.text, 'html.parser')
    div = soup.find('div', class_='c-garfield-the-cat')
    links = div.find_all('a', href=True)

    # Ищем ссылки на изображения, которые соответствуют требуемому разрешению
    pic_url = []
    pic_name = []
    for i in links:
        if resolution in i['href']:
            pic_url.append(i['href'])
            pic_name.append(i['href'].split('/').pop(-1))
    if len(pic_url) == 0:
        parser.error("Изображений с таким разрешением не найдено")

    # Получаем и сохраняем найденные изображения
    future = ensure_future(run_check(pic_url))  # формируем задачи из awaitable объектов
    for i, pic in enumerate(get_event_loop().run_until_complete(future)):  # Запускаем список задач и получаем ответ
        if pic is not None:
            out = open("{}".format(pic_name[i]), "wb")
            out.write(pic)
            out.close()


if __name__ == '__main__':
    main()

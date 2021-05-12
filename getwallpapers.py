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
    next_date = date + relativedelta(months=1)
    return 'https://www.smashingmagazine.com/{}/{:02}/desktop-wallpaper-calendars-{}-{}/'.format(
        date.year, date.month, calendar.month_name[next_date.month], next_date.year)


async def _fetch(url, session):
    async with session.get(url) as response:
        return await response.read()


async def _run_check(pic):
    tasks = []
    async with ClientSession() as session:
        for j in pic:
            task = ensure_future(_fetch(j, session))
            tasks.append(task)
        return await gather(*tasks)


def main():
    date, resolution = sys.argv[1:]
    y = int(date[2:])
    m = int(date[:2])
    date = datetime.date(y, m, 1)
    url = get_url(date)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    vacancies_names = soup.find('div', class_='c-garfield-the-cat')
    pic_url = []
    pic_name = []
    for i in vacancies_names.find_all('a', href=True):
        if resolution in i['href']:
            pic_url.append(i['href'])
            k = 0
            for j in i['href'][::-1]:
                if j == '/':
                    break
                k += 1
            pic_name.append(i['href'][len(i['href']) - k:])
    future = ensure_future(_run_check(pic_url))
    k = 0
    for i in get_event_loop().run_until_complete(future):
        out = open("{}".format(pic_name[k]), "wb")
        out.write(i)
        out.close()
        k += 1


if __name__ == '__main__':
    main()

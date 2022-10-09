# Импорт библиотек
import requests as rq
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from IPython import display


class lentaRu_parser:
    def __init__(self):
        pass

    def _get_url(self, param_dict: dict) -> str:
        """
        Возвращает URL для запроса json таблицы со статьями

        url = 'https://lenta.ru/search/v2/process?'\
        + 'from=0&'\                       # Смещение
        + 'size=1000&'\                    # Кол-во статей
        + 'sort=2&'\                       # Сортировка по дате (2), по релевантности (1)
        + 'title_only=0&'\                 # Точная фраза в заголовке
        + 'domain=1&'\                     # ??
        + 'modified%2Cformat=yyyy-MM-dd&'\ # Формат даты
        + 'type=1&'\                       # Материалы. Все материалы (0). Новость (1)
        + 'bloc=4&'\                       # Рубрика. Экономика (4). Все рубрики (0)
        + 'modified%2Cfrom=2020-01-01&'\
        + 'modified%2Cto=2020-11-01&'\
        + 'query='                         # Поисковой запрос
        """
        hasType = int(param_dict['type']) != 0
        hasBloc = int(param_dict['bloc']) != 0

        url = 'https://lenta.ru/search/v2/process?' \
              + 'from={}&'.format(param_dict['from']) \
              + 'size={}&'.format(param_dict['size']) \
              + 'sort={}&'.format(param_dict['sort']) \
              + 'title_only={}&'.format(param_dict['title_only']) \
              + 'domain={}&'.format(param_dict['domain']) \
              + 'modified%2Cformat=yyyy-MM-dd&' \
              + 'type={}&'.format(param_dict['type']) * hasType \
              + 'bloc={}&'.format(param_dict['bloc']) * hasBloc \
              + 'modified%2Cfrom={}&'.format(param_dict['dateFrom']) \
              + 'modified%2Cto={}&'.format(param_dict['dateTo']) \
              + 'query={}'.format(param_dict['query'])

        return url

    def _get_search_table(self, param_dict: dict) -> pd.DataFrame:
        """
        Возвращает pd.DataFrame со списком статей
        """
        url = self._get_url(param_dict)
        r = rq.get(url)
        search_table = pd.DataFrame(r.json()['matches'])

        return search_table

    def get_articles(self,
                     param_dict,
                     time_step=37,
                     save_every=5) -> pd.DataFrame:
        """
        Функция для скачивания статей интервалами через каждые time_step дней
        Делает сохранение таблицы через каждые save_every * time_step дней

        """
        param_copy = param_dict.copy()
        time_step = timedelta(days=time_step)
        dateFrom = datetime.strptime(param_copy['dateFrom'], '%Y-%m-%d')
        dateTo = datetime.strptime(param_copy['dateTo'], '%Y-%m-%d')
        if dateFrom > dateTo:
            raise ValueError('dateFrom should be less than dateTo')

        out = pd.DataFrame()
        save_counter = 0

        while dateFrom <= dateTo:
            param_copy['dateTo'] = (dateFrom + time_step).strftime('%Y-%m-%d')
            if dateFrom + time_step > dateTo:
                param_copy['dateTo'] = dateTo.strftime('%Y-%m-%d')
            print('Parsing articles from ' \
                  + param_copy['dateFrom'] + ' to ' + param_copy['dateTo'])
            out = out.append(self._get_search_table(param_copy), ignore_index=True)
            dateFrom += time_step + timedelta(days=1)
            param_copy['dateFrom'] = dateFrom.strftime('%Y-%m-%d')
            save_counter += 1
            if save_counter == save_every:
                display.clear_output(wait=True)
                out.to_excel("/tmp/checkpoint_table.xlsx")
                print('Checkpoint saved!')
                save_counter = 0
        print('Finish')

        return out


General = ["бизнес", "тренд", "рост", "масштаб", "потребност", "запрос", "клиент", "директор", "компан", "выгод",
           "деньг", "доллар", "рубль", "работ"]
Buh = ["акт", "нормативный", "документ", "договор", "банк", "контрагент", "законодательство", "закон", "отчёт"]

# Задаем тут параметры

query = ''
offset = 0
size = 1000
sort = "3"
title_only = "0"
domain = "1"
material = "0"
bloc = "4"
dateFrom = '2022-09-01'
dateTo = "2022-10-31"
param_dict = {'query': query,
              'from': str(offset),
              'size': str(size),
              'dateFrom': dateFrom,
              'dateTo': dateTo,
              'sort': sort,
              'title_only': title_only,
              'type': material,
              'bloc': bloc,
              'domain': domain}

print("- param_dict:", param_dict)

# Тоже будем собирать итеративно, правда можно ставить time_step побольше, т.к.
# больше лимит на запрос статей. И Работает быстрее :)
parser = lentaRu_parser()
tbl = parser.get_articles(param_dict=param_dict,
                          time_step=37,
                          save_every=5)

chast = {i: [] for i in General}
for key in General:
    right = list(map(str.upper, tbl["rightcol"]))
    print(right)
    for r in right:
        print(r)
        if key.upper() in r:
            chast[key].append(r.count(key.upper()))
        else:
            chast[key].append(0)
print(chast)

mark = {i: 0 for i in range(len(tbl.index))}
for i in list(chast.values()):
    for val, ind in zip(i, range(len(i))):
        mark[ind] += val
print(mark)
for i in list(mark.keys()):
    mark[i] = round((mark[i] / len(right[i].split(" "))) * 100)
print(mark)

mark_without_empty = {key: mark[key] for key in mark if mark[key] != 0}

print(len(tbl.index))
print(tbl)
print("###########################################################################################")
print("Оценки в процентах", mark_without_empty)
sorted_values = sorted(mark_without_empty.values(), reverse=True)  # Sort the values
sorted_dict = {}

for i in sorted_values:
    for k in mark_without_empty.keys():
        if mark_without_empty[k] == i:
            sorted_dict[k] = mark_without_empty[k]
            break
print(sorted_dict)
best = {i: sorted_dict[i] for i in list(sorted_dict.keys())[:3]}
print(best)

print("Наиболее подходящие новости:")
for i in list(best.keys()):
    print(tbl['rightcol'][i])

import time
import threading
import math
from model import engine, Base, Info, session
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import glob
# import gspread
import pandas as pd
import openpyxl
from yandexparser.crud import get_all_data

import requests
from bs4 import BeautifulSoup
import lxml

import undetected_chromedriver as uc
from selenium.webdriver import ChromeOptions, Chrome, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common

"""
https://docs.google.com/spreadsheets/d/1FRf27vVhZ6XvX_X3YwQy4BSyvRyAcqOV9l9ywcSC2oQ/edit#gid=0
TODO
3) Сделать логику работы в --headless + чтобы по каждой категории собирались данные

"""


# def update_worksheet(df, name, wsname):
#     """
#      Update a worksheet in GSpread. This is a convenience method for updating a worksheet's data.
#      :param df: A : class : ` pandas. DataFrame ` with column names and values to update
#      :param name: The name of the file to write to
#      :param wsname: The name of the worksheet to write to
#     """
#     creds = "./token/creds.json"
#     gc = gspread.service_account(filename=creds)
#     sh = gc.open(name)
#     worksheet = sh.worksheet(wsname)
#     worksheet.clear()
#     worksheet.update([df.columns.values.tolist()] + df.values.tolist())


def get_greate_places(browser: uc.Chrome, actions: ActionChains, url_cat: str) -> list:
    '''Получение ссылок на заведения'''

    browser.get(url_cat)
    time.sleep(5)

    browser.set_window_size(600, 1345)
    time.sleep(5)
    actions.move_by_offset(xoffset=360, yoffset=70).click().perform()
    # browser.maximize_window()
    count_wait_problem = 0
    while ', если не нашли их на карте.' not in browser.page_source:
        time.sleep(0.005)
        actions.key_down(Keys.SPACE).perform()

        count_wait = 0
        while 'Загрузка...' in browser.page_source and count_wait < 10:
            count_wait += 1
            print('Закгрузка...')
            time.sleep(0.5)

        if count_wait == 10:
            count_wait_problem += 1
            if count_wait_problem > 10:
                break

    list_place_cards = browser.find_elements(By.CSS_SELECTOR, 'li[class="search-snippet-view"]')

    print(f'Всего заведений найдено - {len(list_place_cards)}')

    list_links = []
    dict_links = {}
    for idx, place in enumerate(list_place_cards):
        try:
            print(f"Попытка достать ссылку из карточки заведения №{idx + 1}.")
            link = place.find_element(By.CSS_SELECTOR, 'span[data-nosnippet] a').get_attribute('href')
            dict_links[idx] = link
            list_links.append(link)
        except:
            continue
    print(dict_links)
    result_links = list(set(list_links))

    print(f'Количество ссылок - {len(result_links)}')
    print('-----------------------------------------------------------------------------------------------------------')
    print('-----------------------------------------------------------------------------------------------------------')
    print('-----------------------------------------------------------------------------------------------------------')
    print(result_links)
    return result_links


def get_data(browser: uc.Chrome, actions: ActionChains, wait: WebDriverWait, list_links: list, data_collection: list,
             worker_name: str):
    '''Получение данных о заведениях'''
    print('|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||')
    print(f'"{worker_name}" count links >>> {len(list_links)}')
    print('|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||')
    if list_links:
        for link in list_links:
            print('_______________________________________________________________________________________________')
            print(f"{worker_name} >>> {link} start.")
            print('_______________________________________________________________________________________________')
            browser.get(link)
            time.sleep(0.5)
            # название, описание, часы работы, номер телефона, фотографии
            try:
                name = browser.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]').text.strip()
            except:
                name = None

            try:
                description = browser.find_element(By.CSS_SELECTOR, 'span[class="business-summary__text"]').text.strip()
            except:
                description = None

            try:
                phone_button = browser.find_element(By.CSS_SELECTOR, 'div[class="orgpage-phones-view__more"]')
                wait.until(EC.element_to_be_clickable(phone_button))
                actions.move_to_element(phone_button).click().perform()
                time.sleep(0.3)
            except:
                pass
            try:
                phone = \
                    browser.find_element(By.CSS_SELECTOR, 'div[class="card-phones-view__phone-number"]').text.split(
                        '\n')[
                        0].strip()
            except:
                phone = None

            try:
                if browser.find_element(By.CSS_SELECTOR, 'section[class="business-ownership-view _wide"]'):
                    relevance_information = 1
            except:
                relevance_information = 0

            try:
                wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'div[class="business-working-status-flip-view _clickable"]')))
            except:
                pass
            time.sleep(0.3)
            try:
                working_hours_button_open = browser.find_element(By.CSS_SELECTOR,
                                                                 'div[class="business-working-status-flip-view _clickable"]')
                wait.until(EC.element_to_be_clickable(working_hours_button_open))

                actions.move_to_element(working_hours_button_open).click().perform()
                time.sleep(0.3)
            except:
                pass

            try:
                working_hours_elements = browser.find_elements(By.CSS_SELECTOR,
                                                               'div[class="business-working-intervals-view _wide"] div[class="card-feature-view__content"]')
                working_hours = {}
                for wh_element in working_hours_elements:
                    day = wh_element.find_element(By.CSS_SELECTOR,
                                                  'div[class="business-working-intervals-view__day"]').text.strip()
                    interval = wh_element.find_element(By.CSS_SELECTOR,
                                                       'div[class="business-working-intervals-view__interval"]').text.strip()
                    working_hours[day] = interval

                working_hours_button_close = browser.find_element(By.CSS_SELECTOR, 'div[class=dialog__content] button')
                actions.move_to_element(working_hours_button_close).click().perform()
            except:
                working_hours = None
                try:
                    working_hours_button_close = browser.find_element(By.CSS_SELECTOR,
                                                                      'div[class=dialog__content] button')
                    actions.move_to_element(working_hours_button_close).click().perform()
                except:
                    pass

            try:
                address_elements = browser.find_elements(By.CSS_SELECTOR,
                                                         'a[class="orgpage-header-view__address"] span')
                address = ', '.join([address_element.text.strip() for address_element in address_elements]) if len(
                    address_elements) > 1 else address_elements[0].text.strip()
            except:
                address = None

            try:
                site = browser.find_element(By.CSS_SELECTOR,
                                            'div[class="business-urls-view__url"] a[class="business-urls-view__link"]').get_attribute(
                    'href')
            except:
                site = None

            try:
                raiting = browser.find_element(By.CSS_SELECTOR,
                                               'span[class="business-rating-badge-view__rating-text _size_m"]').text.strip()
            except:
                raiting = None

            try:
                coordinates = browser.current_url.split('/')[-1].split('=')[-2].replace('z', '').replace('&',
                                                                                                         '').replace(
                    '2C', '').split('%')

                longitude = coordinates[0]  # Долгота
                latitude = coordinates[1]  # Широта
            except:
                longitude = None
                latitude = None


            browser.get(link + '/gallery/')
            time.sleep(0.3)
            for i in range(10):
                actions.key_down(Keys.PAGE_DOWN).perform()
            time.sleep(3)
            photo_link_list = [img_element.get_attribute('src') for img_element in
                               browser.find_elements(By.CSS_SELECTOR, 'div img[class="media-wrapper__media"]')]

            photo_links = ', '.join(photo_link_list)

            browser.get(link + '/features/')
            time.sleep(0.3)

            try:
                type = browser.find_elements(By.CSS_SELECTOR,
                                             'a[class="orgpage-categories-info-view__link"] span[class="button__text"]')[
                    0].text.strip()
            except:
                type = None

            try:
                kitchen_elements = browser.find_elements(By.CSS_SELECTOR,
                                                         'span[class="business-features-view__valued-title"]')
                for idx, kitchen_element in enumerate(kitchen_elements):
                    if "Кухня" in kitchen_element.text.strip():
                        kitchen = browser.find_elements(By.CSS_SELECTOR,
                                                        'span[class="business-features-view__valued-title"] + span')[
                            idx].text.strip()
                        break
            except:
                kitchen = None

            try:
                prices_elements = browser.find_elements(By.CSS_SELECTOR,
                                                        'div span[class="business-features-view__valued-title"]')
                for idx, prices_element in enumerate(prices_elements):
                    if "Цены" in prices_element.text.strip():
                        prices = browser.find_elements(By.CSS_SELECTOR,
                                                       'div span[class="business-features-view__valued-title"] + span')[
                            idx].text.strip()
                        break
            except:
                prices = None

            try:
                average_check_elements = browser.find_elements(By.CSS_SELECTOR,
                                                               'div span[class="business-features-view__valued-title"]')
                for idx, average_check_element in enumerate(average_check_elements):
                    if "Средний" in average_check_element.text.strip():
                        average_check = browser.find_elements(By.CSS_SELECTOR,
                                                              'div span[class="business-features-view__valued-title"] + span')[
                            idx].text.strip()
                        break
            except:
                average_check = None

            browser.get(link + '/menu/')
            time.sleep(0.3)

            menu = {}
            try:
                menu_category_elements = browser.find_elements(By.CSS_SELECTOR,
                                                               'div[class="business-full-items-grouped-view__category"]')
                for menu_category in menu_category_elements:
                    category = menu_category.find_element(By.CSS_SELECTOR,
                                                          'div[class="business-full-items-grouped-view__title"]').text.strip()
                    menu[category] = {}
                    menu_items = [item.text.strip() for item in menu_category.find_elements(By.CSS_SELECTOR,
                                                                                            'div[class="related-item-list-view__title"]')]
                    menu_items_prices = [price.text.strip() for price in menu_category.find_elements(By.CSS_SELECTOR,
                                                                                                     'div[class="related-item-list-view__price"]')]

                    for i in range(len(menu_items)):
                        menu[category][menu_items[i]] = menu_items_prices[i]
            except:
                menu = None

            print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print(f"{worker_name} >>> {link} done.")
            print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')

            data_collection.append(
                [name, type, kitchen, menu, raiting, description, address, phone, site, working_hours,
                 photo_links, prices, average_check, relevance_information, longitude, latitude, link])

def run_parse_threads(list_links: list, data_collection: list):
    options_1 = uc.ChromeOptions();
    options_1.add_argument("--headless")
    options_2 = uc.ChromeOptions();
    options_2.add_argument("--headless")
    options_3 = uc.ChromeOptions();
    options_3.add_argument("--headless")

    browser_1 = uc.Chrome(version_main=114, options=options_1)
    browser_2 = uc.Chrome(version_main=114, options=options_2)
    browser_3 = uc.Chrome(version_main=114, options=options_3)

    wait_1 = WebDriverWait(driver=browser_1, timeout=10, ignored_exceptions=[selenium.common.TimeoutException])
    wait_2 = WebDriverWait(driver=browser_2, timeout=10, ignored_exceptions=[selenium.common.TimeoutException])
    wait_3 = WebDriverWait(driver=browser_3, timeout=10, ignored_exceptions=[selenium.common.TimeoutException])

    actions_1 = ActionChains(driver=browser_1)
    actions_2 = ActionChains(driver=browser_2)
    actions_3 = ActionChains(driver=browser_3)

    thread_1 = threading.Thread(target=get_data, args=(
        browser_1, actions_1, wait_1, list_links[:math.ceil(len(list_links) / 3)], data_collection, "th_1"),
                                name="th_1")
    thread_2 = threading.Thread(target=get_data, args=(
        browser_2, actions_2, wait_2, list_links[math.ceil(len(list_links) / 3):math.ceil(len(list_links) / 3) * 2],
        data_collection, "th_2"), name="th_2")
    thread_3 = threading.Thread(target=get_data, args=(
        browser_3, actions_3, wait_3, list_links[math.ceil(len(list_links) / 3) * 2:], data_collection, "th_3"),
                                name="th_3")

    thread_1.start()
    thread_2.start()
    thread_3.start()

    thread_1.join()
    thread_2.join()
    thread_3.join()

    try:
        browser_1.quit()
    except:
        pass
    try:
        browser_2.quit()
    except:
        pass
    try:
        browser_3.quit()
    except:
        pass

def data_to_xlsx(matrix: list[list], name: str) -> None:
    '''Сохранение данных в XLSX'''
    columns = ["Название", "Тип заведения", "Кухня", "Меню", "Рейтинг", "Описание",
               "Адрес", "Телефон", "Сайт", "График работы",
               "Ссылки на фото", "Цены", "Средний чек", "Актуализация информации", "Долгота",
               "Широта", "Яндекс ссылка"]
    df = pd.DataFrame(matrix, columns=columns)
    df.to_excel(f'data/{name}.xlsx', index=False)

def save_excel_to_data_base(df: pd.DataFrame) -> None:

    for index, row in df.iterrows():

        name = row[0]
        type = row[1]
        kitchen = row[2]
        menu = row[3]
        raiting = row[4]
        description = row[5]
        address = row[6]
        phone = row[7]
        site = row[8]
        working_hours = row[9]
        photo_links = row[10]
        prices = row[11]
        average_check = row[12]
        relevance_information = row[13]
        if relevance_information == 1: relevance_information = True
        else: relevance_information = False
        longitude = row[14]
        latitude = row[15]
        link = row[16]
        daterenew = date.today()

        check_exists_link = session.query(Info).filter_by(link=link).first()

        if not check_exists_link:

            stack_info = Info(
                name=name,
                type=type,
                kitchen=kitchen,
                menu=menu,
                raiting=raiting,
                description=description,
                address=address,
                phone=phone,
                site=site,
                working_hours=working_hours,
                photo_links=photo_links,
                prices=prices,
                average_check=average_check,
                relevance_information=relevance_information,
                longitude=longitude,
                latitude=latitude,
                link=link,
                daterenew=daterenew)
            session.add(stack_info)
        else:
            check_exists_link.name = name
            check_exists_link.type = type
            check_exists_link.kitchen = kitchen
            check_exists_link.raiting = raiting
            check_exists_link.description = description
            check_exists_link.address = address
            check_exists_link.phone = phone
            check_exists_link.working_hours = working_hours
            check_exists_link.photo_links = photo_links
            check_exists_link.average_check = average_check
            check_exists_link.relevance_information = relevance_information
            check_exists_link.longitude = longitude
            check_exists_link.latitude = latitude
            check_exists_link.daterenew = daterenew

    session.commit()
    session.close()

def main():

    URL_DICT = {'Рестораны': 'https://yandex.ru/maps/2/saint-petersburg/category/restaurant/',
                'Кафе': 'https://yandex.ru/maps/2/saint-petersburg/category/cafe',
                'Кофейни': 'https://yandex.ru/maps/2/saint-petersburg/category/coffee_shop',
                "Бар": 'https://yandex.ru/maps/2/saint-petersburg/search/%D0%91%D0%B0%D1%80',
                "Паб": 'https://yandex.ru/maps/2/saint-petersburg/category/bar_pub',
                "Кондитерская": 'https://yandex.ru/maps/2/saint-petersburg/category/confectionary'}

    for name, url in URL_DICT.items():
        print("Start.")
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        links: list = []
        with uc.Chrome(version_main=114, options=options) as browser:  # todo Блок инициализации браузера
            actions = ActionChains(browser)
            links.extend(get_greate_places(browser=browser, actions=actions, url_cat=url))  # Сбор целевых ссылок
        data_collection = []
        run_parse_threads(list_links=links, data_collection=data_collection)
        data_to_xlsx(matrix=data_collection, name=name)
        print('______________________________________D-O-N-E______________________________________')

    """ объединение эксель файлов """

    path = glob.glob('data/*')
    df = pd.concat((pd.read_excel(file) for file in path), ignore_index=True)
    df = df.drop_duplicates(subset=['Яндекс ссылка'], keep='first')
    df.reset_index(inplace=True)
    df.drop('index', axis=1, inplace=True)
    df.to_excel('./data/data.xlsx', index=False)

    """ очищение папки с данными"""

    """ сохранение данных в базу данных """
    df = pd.read_excel('data/data.xlsx')
    save_excel_to_data_base(df=df)

    """ post to google sheets """
    df_info = get_all_data()
    df_info.to_excel("RESULT.xlsx", engine='openpyxl')
    # update_worksheet(df_info, name="Location Bot", wsname="Data")





if __name__ == '__main__':

    import datetime
    while True:
        now = datetime.datetime.now()

        if now.hour == 16:  # Настройка времени запуска парсера

            Base.metadata.create_all(bind=engine)

            """ запуск основного файла """

            main()

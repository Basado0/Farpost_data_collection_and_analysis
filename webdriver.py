import pickle
import asyncio
from config import BASE_URL,HEADERS
from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import requests
from selenium.common.exceptions import NoSuchElementException
import time
import os

def get_cookies_with_selenium(url, cookie_file='cookies.pkl', headless=True):
    """
    Запускает браузер, открывает url, ждёт ручного решения капчи (при необходимости),
    сохраняет куки в файл и возвращает словарь кук для requests.
    """
    options = ChromeOptions()
    if headless:
        options.add_argument('--headless')
    # Дополнительные опции для уменьшения детекта
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--log-level=3')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    service = Service(executable_path='chromedriver.exe',log_output=open(os.devnull, 'w'))

    driver = Chrome(options=options,service=service)
    driver.get(url)
    if is_captcha_on_screen(driver):
        print('Обнаружена капча')
        solve_captha_with_capmonster(driver,url)
    
    # Получаем куки
    selenium_cookies = driver.get_cookies()
    driver.quit()
    
    # Преобразуем в формат requests
    cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    
    # Сохраняем в файл для будущих запусков
    with open(cookie_file, 'wb') as f:
        pickle.dump(cookies_dict, f)
    
    return cookies_dict

def get_cookies_dict(file:str):
    with open(file,'rb') as f:
        cookies_dict = pickle.load(f)
    return cookies_dict


def is_captcha_on_screen(driver:Chrome):
    time.sleep(5)
    html = driver.page_source
    return True if 'Вы не робот' in html else False


def click_element_xpath(driver,element_xpath):
    try:
        element =  WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, element_xpath))
    )
        element.click()
        print('Кнопка нажата')

    except Exception as e:
        if is_captcha_on_screen(driver):
            print(f'Не удалось нажать кнопку, {e}')
        else:
            pass

def click_element(driver,class_name):
    try:
        element =  WebDriverWait(driver, 4).until(
        EC.element_to_be_clickable((By.CLASS_NAME, class_name))
    )
        element.click()
        print('Кнопка нажата')

    except Exception as e:
        if is_captcha_on_screen(driver):
            print(f'Не удалось нажать кнопку, {e}')
        else:
            pass

def solve_captha_with_capmonster(driver:Chrome,url):
    checkbox_name = 'altcha-label'
    continue_button = '//*[@id="send-button"]'

    driver.get(url)

    try:
        checkbox = driver.find_element(By.CLASS_NAME,checkbox_name)
        checkbox.click()
        WebDriverWait(driver, 5).until(
                EC.text_to_be_present_in_element((By.CLASS_NAME, checkbox_name), "Проверено")
        )
        click_element_xpath(driver,continue_button)

    except NoSuchElementException:
        print('На странице нет чекбокса, Капча ушла')


def refresh_session(url,headers=HEADERS,headless=True):
    cookies_dict = get_cookies_with_selenium(url,headless=headless)
    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(cookies_dict)

    return session

    


if __name__ == "__main__":
    
    session = refresh_session(BASE_URL,headless=False)
    #webdrive()

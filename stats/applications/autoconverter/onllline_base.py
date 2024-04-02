import datetime
import os
import time

import requests
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import JavascriptException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from applications.autoconverter.models import ConverterTask


def onllline_worker(task: ConverterTask):
    url = 'https://www.onllline.ru'
    service = Service()
    options = uc.ChromeOptions()
    # Отключаю окно сохранения пароля
    prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)
    options.add_argument('--headless')  # Браузер без GUI

    driver = webdriver.Chrome(options=options, service=service)

    driver.get(url)
    wait = WebDriverWait(driver, 120)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(0.5)

    onllline_authorize(driver)
    import_result = onllline_import_export(driver, task)
    driver.quit()

    return import_result


def onllline_authorize(driver):
    """
    Авторизация на onllline.ru
    :return:
    """
    login_input = driver.find_element(By.NAME, 'auth_login')
    login_input.send_keys(os.getenv('ONLLLINE_AUTH_LOGIN'))
    time.sleep(0.2)
    password_input = driver.find_element(By.NAME, 'auth_password')
    password_input.send_keys(os.getenv('ONLLLINE_AUTH_PASSWORD'))
    time.sleep(0.2)
    submit_btn = driver.find_element(By.NAME, 'auth_go')
    submit_btn.click()
    time.sleep(0.5)


def onllline_import_export(driver, task: ConverterTask):
    """
    Импортирует прайс в базу, после этого экспортирует на площадки
    :param driver:
    :param task:
    :return:
    """
    # price = 'https://ph.onllline.ru/converter/avilon-premium-volgogradka/prices/price_avilon-premium-volgogradka.csv'
    # salon = '326'
    # import_mode = 'AddDel'
    if not task.import_to_onllline:
        return

    # Настройки импорта
    salon = task.onllline_salon_to_import
    price = f'https://ph.onllline.ru/{task.price}'
    import_mode = task.onllline_import_mode

    # Импортирую
    driver.get(f'https://www.onllline.ru/salons/import/{salon}/')
    time.sleep(0.5)
    wait = WebDriverWait(driver, 120)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(1)

    import_input = driver.find_element(By.NAME, 'import_file_text')
    import_input.send_keys(price)

    # Вариант импорта
    import_select_element = driver.find_element(By.NAME, 'import_mode')
    import_select = Select(import_select_element)
    import_select.select_by_value(import_mode)

    # Опции импорта
    for option in task.onllline_import_options:
        if option == '-----':
            continue
        driver.find_element(By.CSS_SELECTOR, f'label[for="{option}"]').click()
    # Размножение стока
    if task.onllline_import_multiply_price:
        driver.find_element(By.ID, 'stock').send_keys(task.onllline_import_multiply_price)

    upload_btn = driver.find_element(By.NAME, 'ad_import')
    upload_btn.click()

    # Отчет импорта
    import_result = driver.find_element(By.ID, 'import_result')
    importing = True
    while importing:
        # print('жду отчет импорта')
        time.sleep(1)
        child_elements = import_result.find_elements(By.CLASS_NAME, 'access-message')
        if child_elements:
            importing = False

    # Удаляю лишний текст с отчета импорта
    try:
        driver.execute_script("document.querySelector('div.img-info label[class=blue-dash]').remove();")
    except JavascriptException:
        pass
    driver.execute_script("document.getElementById('salon_copyimages').remove();")
    import_result = driver.find_element(By.ID, 'import_result').text
    lines = import_result.splitlines()
    filtered_lines = [line for line in lines if not line.startswith("Отчет сохранен")]
    import_result = '\n'.join(filtered_lines)
    import_result = import_result.replace('\n\n', '')

    # Экспортирую
    if not task.export_to_onllline:
        return import_result

    export_btn = driver.find_element(By.NAME, 'salon_export1')
    export_btn.click()

    # Выбор площадок
    # driver.save_screenshot(f'scr/scr_{datetime.datetime.now().strftime("%Y.%m.%d %H-%M-%S")}.png')
    export_select_element = driver.find_element(By.NAME, 'export_format[]')
    time.sleep(0.5)
    export_select = Select(export_select_element)
    for website in task.export_to_websites:
        if website == '-----':
            continue
        export_select.select_by_value(website)
    time.sleep(0.5)

    export_btn2 = driver.find_element(By.NAME, 'ad_export_next')
    export_btn2.click()
    time.sleep(0.5)

    return import_result

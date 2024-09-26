import base64
import sys
from datetime import datetime
from pprint import pprint
from typing import Union, Dict, List
import undetected_chromedriver as uc
from stats.settings import env
from selenium.webdriver.chrome.webdriver import WebDriver

import os

from bs4 import BeautifulSoup
from io import BytesIO
import requests
from PIL import Image
import logging
from time import sleep
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait


from twocaptcha import TwoCaptcha


def random_delay(min_time=0.5, max_time=1.5):
    sleep(random.uniform(min_time, max_time))


def is_captcha(driver: WebDriver) -> bool:
    """Проверяет появилась ли капча."""
    return TITLE_CAPTCHA.lower() == driver.title.lower()


def is_main_page(driver: WebDriver) -> bool:
    """Проверяет, находимся ли мы на главной странице реестра."""
    return TITLE_MAIN_PAGE.lower() == driver.title.lower()


def check_captcha_and_solve(driver: WebDriver) -> None:
    """Обрабатывает капчу, если она появляется."""
    while is_captcha(driver):  # Пока есть капча, решаем ее
        mask_selenium(driver)
        enhance_fingerprinting(driver)
        add_custom_headers(driver)
        simulate_user_interaction(driver)
        print('START CAPTCHA!')
        random_delay(3, 5)  # Увеличиваем задержку
        solve_start_captcha(driver)
        random_delay(3, 5)  # Дополнительная задержка после отправки формы


def simulate_user_interaction(driver):
    """Имитация взаимодействия с элементами страницы."""
    actions = ActionChains(driver)

    # Найдем элемент капчи для взаимодействия
    captcha_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'captcha-img'))
    )

    # Прокрутим страницу, чтобы капча была видна
    driver.execute_script("arguments[0].scrollIntoView(true);", captcha_element)
    random_delay()

    # Перемещение курсора к капче (без использования смещения)
    actions.move_to_element(captcha_element).perform()
    random_delay()

    # Эмуляция движения мыши по странице (с использованием точного перемещения по координатам)
    for _ in range(5):
        # Плавное перемещение мыши по элементу капчи
        actions.move_to_element_with_offset(captcha_element, random.randint(-5, 5), random.randint(-5, 5)).perform()
        random_delay()

    # Можно добавить скролл вверх и вниз для имитации случайных действий
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    random_delay()
    driver.execute_script("window.scrollTo(0, 0);")
    random_delay()


def mask_selenium(driver):
    """Маскировка Selenium для обхода защиты."""
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })


def enhance_fingerprinting(driver):
    """Эмуляция расширенного отпечатка браузера."""
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })
    driver.execute_script("""
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
    """)


def add_custom_headers(driver):
    """Добавление кастомных заголовков для имитации реального браузера."""
    # Добавляем заголовки, чтобы имитировать запросы с реального браузера
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})


def update_hidden_fields(driver):
    """Проверяем и обновляем скрытые поля на форме."""
    hidden_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='hidden']")
    for field in hidden_fields:
        # Пример обновления скрытых полей, если они необходимы для прохождения проверки
        if field.get_attribute('name') == 'x':
            driver.execute_script("arguments[0].value = 'новое значение';", field)


def solve_start_captcha(driver: WebDriver) -> None:
    """Решение стартовой капчи на входной странице с поэтапным вводом символов."""
    simulate_user_interaction(driver)
    solution = solve_captcha(driver, 'captcha-img')
    if solution['status success']:
        code_solve = solution['code']  # Получаем текст капчи
        print('Код для капчи получен:', code_solve)
        input_element = driver.find_element(By.ID, 'image_code')
        input_element.click()
        simulate_user_interaction(driver)
        # Вводим капчу по одному символу с паузами
        # actions = ActionChains(driver)
        # actions.move_to_element(input_element).click().perform()
        for char in code_solve:
            input_element.send_keys(char)
            # actions.send_keys(char).perform()
            random_delay()  # Случайная пауза между символами

        random_delay(2, 3)  # Ожидание после полного ввода капчи

        # Эмуляция взаимодействия с элементами страницы перед отправкой формы
        simulate_user_interaction(driver)

        # Обновляем скрытые поля перед отправкой формы
        update_hidden_fields(driver)
        random_delay(2, 3)
        # Отправляем форму с использованием JS (чтобы не было явных кликов Selenium)
        driver.execute_script("document.querySelector('form').submit();")

        print('Капча введена и форма отправлена')


def capture_captcha_screenshot(driver: WebDriver, captcha_element, save_path: str) -> None:
    """
    Делает скриншот элемента капчи и сохраняет его как изображение.
    """
    # Скриншот всей страницы
    screenshot_base64 = driver.get_screenshot_as_base64()
    screenshot_data = base64.b64decode(screenshot_base64)

    # Открываем изображение как объект Pillow
    screenshot_image = Image.open(BytesIO(screenshot_data))

    # Получаем положение и размер капчи на странице
    location = captcha_element.location
    size = captcha_element.size

    # Определяем координаты капчи для обрезки
    left = location['x']
    top = location['y']
    right = left + size['width']
    bottom = top + size['height']

    # Обрезаем изображение, чтобы получить только капчу
    captcha_image = screenshot_image.crop((left, top, right, bottom))
    # Сохраняем изображение капчи локально
    captcha_image.save(save_path)
    print(f"Скриншот капчи сохранен как {save_path}")


def solve_captcha(driver: WebDriver, captcha_selector: str) -> dict[str, str | bool]:
    """
    Решение капчи через внешний сервис 2Captcha.
    Возвращает словарь с полем `status success` и кодом капчи.
    """
    # Найдем элемент капчи на странице
    captcha_element = driver.find_element(By.CLASS_NAME, captcha_selector)
    # Сделаем скриншот капчи и сохраним его
    # Указываем путь к директории проекта или той, где вы хотите сохранять файлы
    project_directory = os.path.dirname(os.path.realpath(__file__))  # Это директория, где находится ваш текущий файл
    save_path = os.path.join(project_directory, "captcha_image.png")
    capture_captcha_screenshot(driver, captcha_element, save_path)

    try:
        print('Ожидание ответа от 2Captcha...')
        result = solver.normal(save_path)
        if 'code' not in result or 'ERROR_CAPTCHA_UNSOLVABLE' in result:
            return {'status success': False}
        return {'status success': True, 'code': result['code']}
    except Exception as e:
        print(f"Ошибка при решении капчи: {e}")
        return {'status success': False}


def solve_second_captcha(driver: WebDriver) -> None:
    """Решение второй капчи на форме поиска."""
    solution = solve_captcha(driver, 'captcha_image')
    if solution['status success']:
        code_solve = solution['code']
        input_element = driver.find_element(By.ID, 'gruzoviki_reestr_form_captcha')
        input_element.clear()
        input_element.send_keys(code_solve)


def close_cookies_banner(driver: WebDriver) -> None:
    """Закрывает баннер с cookie, если он присутствует."""
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'cookies-wrapper')))
        close_button = driver.find_element(By.CLASS_NAME, 'cookies-close')
        close_button.click()
        print("Баннер с cookies закрыт")
    except Exception as e:
        print(f"Ошибка при закрытии баннера с cookies: {e}")


def parse_main_page(driver: WebDriver, number: str) -> Dict[str, str]:
    """Отправляет номер автомобиля на проверку и возвращает его статус."""
    select_element = wait.until(EC.presence_of_element_located((By.ID, 'gruzoviki_reestr_form_type')))
    select = Select(select_element)
    select.select_by_value('byTransportRegNumber')
    sleep(1)

    input_element = wait.until(EC.presence_of_element_located((By.ID, 'gruzoviki_reestr_form_byTransportRegNumber')))
    input_element.clear()
    input_element.send_keys(number)
    sleep(1)

    solve_second_captcha(driver)
    sleep(1)
    close_cookies_banner(driver)
    click_button(driver, 'gruzoviki_reestr_form_submit')
    sleep(2)

    passes_data = parse_pass_data(driver)
    if passes_data:
        return passes_data[0]  # Возвращаем первую запись (самую последнюю)
    return {}


def click_button(driver: WebDriver, selector) -> None:
    """Кликает на кнопку по указанному селектору."""
    submit_button = driver.find_element(By.ID, selector)
    submit_button.click()


def parse_pass_data(driver: WebDriver) -> List[Dict[str, str]]:
    """
    Парсит данные о пропусках на странице и возвращает список словарей с номером и статусом.
    """
    html_page = driver.page_source
    soup = BeautifulSoup(html_page, 'html.parser')
    rows = soup.find_all('div', class_='row')

    passes = []
    current_pass = {}

    field_mapping = {
        'ГРЗ': 'номер',
        'Серия': 'серия',
        'Номер': 'номер_пропуска',
        'Действителен с': 'действителен_с',
        'Действителен по': 'действителен_по',
        'Тип действия пропуска (по времени суток)': 'тип_пропуска',
        'Статус': 'статус'
    }

    def calculate_days_left(end_date_str: str) -> str:
        """Вычисляет количество оставшихся дней до окончания действия пропуска."""
        today = datetime.today()
        end_date = datetime.strptime(end_date_str, '%d.%m.%Y')
        days_left = (end_date - today).days

        if days_left > 0:
            return f"Осталось {days_left} дней"
        elif days_left == 0:
            return "Заканчивается сегодня"
        else:
            return "Закончился"

    for row in rows:
        cols = row.find_all('div', class_='col-4')
        if len(cols) == 2:
            field_name = cols[0].get_text(strip=True)
            field_value = cols[1].get_text(strip=True)

            if field_name in field_mapping:
                key = field_mapping[field_name]
                current_pass[key] = field_value

        # Когда найдены все необходимые поля, можно вычислить статус и добавить запись
        if 'номер' in current_pass and 'статус' in current_pass and 'действителен_по' in current_pass:
            # Вычисляем статус на основе даты окончания
            current_pass['статус'] = calculate_days_left(current_pass['действителен_по'])
            current_pass['статус_цвет'] = "Неактивен" if current_pass['статус'] == 'Закончился' else "Активен"
            passes.append(current_pass)
            current_pass = {}

    return passes


# Основной блок
TITLE_CAPTCHA = 'CAPCH PAGE'
TITLE_MAIN_PAGE = "Реестр действующих пропусков грузового транспорта - Единый Транспортный Портал"

api_key = env('APIKEY_2CAPTCHA')
solver = TwoCaptcha(api_key)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
)


# Подключаем undetected-chromedriver для маскировки использования Selenium
def start_driver():
    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)
    return driver


def solve_and_parse(nomera: List[str]) -> List[Dict]:
    # Сюда поместим логику для запуска драйвера, решения капчи и парсинга
    global wait
    driver = start_driver()
    wait = WebDriverWait(driver, 20)

    transport = "https://transport.mos.ru/gruzoviki/reestr"
    driver.get(transport)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Решение первой капчи
    check_captcha_and_solve(driver)
    if is_main_page(driver):
        results = []
        for number in nomera:
            # Заполняем поле с номером и решаем вторую капчу
            print('Обработка номера', number)
            result = parse_main_page(driver, number)

            results.append(result)

        driver.quit()
        return results

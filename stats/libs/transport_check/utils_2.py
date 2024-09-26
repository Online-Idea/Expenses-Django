import sys
from datetime import datetime
from typing import Union, Dict, List
from selenium.webdriver.chrome.webdriver import WebDriver

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import undetected_chromedriver as uc
from twocaptcha import TwoCaptcha
import time


def is_captcha(driver: WebDriver) -> bool:
    """Проверяет появилась ли капча."""
    return TITLE_CAPTCHA.lower() == driver.title.lower()


def is_main_page(driver: WebDriver) -> bool:
    """Проверяет, находимся ли мы на главной странице реестра."""
    return TITLE_MAIN_PAGE.lower() == driver.title.lower()


def wait_for_user_to_solve_captcha(driver: WebDriver) -> None:
    """
    Ожидание, пока пользователь вручную решит первую капчу.
    """
    print("Пожалуйста, пройдите капчу на сайте вручную.")
    while is_captcha(driver):
        time.sleep(5)  # Периодическая проверка, пока не будет решена капча
    print("Капча пройдена, продолжаем работу...")


def solve_second_captcha(driver: WebDriver) -> None:
    """Решение второй капчи на форме поиска через сервис 2Captcha."""
    solution = solve_captcha(driver, 'captcha_image')
    if solution['status success']:
        code_solve = solution['code']
        input_element = driver.find_element(By.ID, 'gruzoviki_reestr_form_captcha')
        input_element.clear()
        input_element.send_keys(code_solve)


def solve_captcha(driver: WebDriver, captcha_selector: str) -> dict[str, str | bool]:
    """
    Решение капчи через внешний сервис 2Captcha.
    Возвращает словарь с полем `status success` и кодом капчи.
    """
    html_page = driver.page_source
    soup = BeautifulSoup(html_page, 'html.parser')
    img_tag = soup.find('img', class_=captcha_selector)
    captcha_image_url = img_tag['src']

    # Решение капчи через 2Captcha
    try:
        print('Ожидание ответа от 2Captcha...')
        result = solver.normal(captcha_image_url)
        if 'code' not in result or 'ERROR_CAPTCHA_UNSOLVABLE' in result:
            return {'status success': False}
        return {'status success': True, 'code': result['code']}
    except Exception as e:
        print(f"Ошибка при решении капчи: {e}")
        return {'status success': False}


def parse_main_page(driver: WebDriver, number: str) -> Dict[str, str]:
    """Отправляет номер автомобиля на проверку и возвращает его статус."""
    select_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, 'gruzoviki_reestr_form_type')))
    select = Select(select_element)
    select.select_by_value('byTransportRegNumber')

    input_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, 'gruzoviki_reestr_form_byTransportRegNumber')))
    input_element.clear()
    input_element.send_keys(number)

    solve_second_captcha(driver)

    click_button(driver, 'gruzoviki_reestr_form_submit')

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
            current_pass['статус'] = calculate_days_left(current_pass['действителен_по'])
            passes.append(current_pass)
            current_pass = {}

    return passes


# Основной блок
TITLE_CAPTCHA = 'CAPCH PAGE'
TITLE_MAIN_PAGE = "Реестр действующих пропусков грузового транспорта - Единый Транспортный Портал"

api_key = '46e8f02a7c0a431df134579b122392d8'
solver = TwoCaptcha(api_key)


# Подключаем undetected-chromedriver для работы с Selenium
def start_driver():
    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    driver = uc.Chrome(options=options)
    return driver


def solve_and_parse(nomera: List[str]) -> List[Dict]:
    """Основная функция для решения капчи и парсинга страницы."""
    driver = start_driver()

    transport = "https://transport.mos.ru/gruzoviki/reestr"
    driver.get(transport)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Проверяем, если капча
    if is_captcha(driver):
        wait_for_user_to_solve_captcha(driver)

    # Продолжаем, если попали на главную страницу
    if is_main_page(driver):
        results = []
        for number in nomera:
            print('Обработка номера: ', number)
            result = parse_main_page(driver, number)
            results.append(result)

        driver.quit()
        return results

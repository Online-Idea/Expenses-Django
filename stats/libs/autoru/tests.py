import re
from datetime import time
from typing import Dict

import requests
from stats.settings import env

from pprint import pprint
# # Ваш набор строк с модификациями
# modifications = [
#     "0.7 MT (58 л.с.)",
#     "0.7 AT (58 л.с.)",
#     "2.8 AT (177 л.с.) 4WD",
#     "2.8d MT (177 л.с.)",
#     "2.8hyb CVT (187 л.с.) FWD",
#     "SDI 1.9d MT (64 л.с.)",
#     "300 CDI BlueTEC 2.1hyb AT (204 л.с.) FWD",
#     "109 CDI 1.5 MT (95 л.с.) FWD",
#     "Electro AT (85 кВт)",
#     "ZE40 Q90 Electro MT (65 кВт)",
#     "72kWh  ZE40 Electro AT (68 кВт) FWD",
#     "L Electro AT (100 кВт)",
#     "75kWh L Electro AT (1200 кВт)",
#     "Turbo S E-Hybrid Executive 4.0hyb AMT (571 л.с.) 4WD",
#     "Turbo S E-Hybrid 4.0hyb AMT (571 л.с.) 4WD",
#     "T 6.8 AT (500 л.с.)"
# ]
#
# # Паттерн для обработки электромобилей
# regex_pattern_electro = re.compile(
#     r'(?:(?P<battery>\d+)kWh\s+)?(?:[A-Z0-9]+\s+)*(?:(?:[A-Z0-9]+\s+)?Electro\s+)?(?P<transmission>[A-Z]+)\s+(?:(?P<battery_after>\d+)kWh\s+)?\((?P<power>\d+)\s+кВт\)(?:\s+(?P<drive>\w+))?'
# )
#
# # Паттерн для обработки обычных автомобилей
# regex_pattern_normal = re.compile(
#     r'(?:(?P<engine_volume>[\d.]+)(?P<engine_type>[a-z]*)\s+)?(?:[A-Z0-9]+\s+)*(?P<transmission>[A-Z]+)\s+\((?P<power>\d+)\s+л\.с\.\)(?:\s+(?P<drive>\w+))?'
# )
#
#
# # Функция для обработки типа двигателя
# def process_engine_type(engine_type):
#     match engine_type:
#         case 'd':
#             return 'Дизель'
#         case 'hyb':
#             return 'Гибрид'
#         case _:
#             return 'Бензин'
#
#
# # Функция для извлечения информации о модификации
# def extract_modification_info(modification):
#     result = {}
#     if 'Electro' in modification:
#         match = re.search(regex_pattern_electro, modification)
#         if match:
#             result['engine_type'] = 'Электро'
#             result['battery_capacity'] = match.group('battery') if match.group('battery') else (
#                 match.group('battery_after') if match.group('battery_after') else '')
#             result['transmission'] = match.group('transmission')
#             result['power'] = match.group('power')
#             result['drive'] = match.group('drive') if match.group('drive') else 'FWD | RWD'
#     else:
#         match = re.search(regex_pattern_normal, modification)
#         if match:
#             result['engine_type'] = process_engine_type(match.group('engine_type'))
#             result['engine_volume'] = match.group('engine_volume')
#             result['transmission'] = match.group('transmission')
#             result['power'] = match.group('power')
#             result['drive'] = match.group('drive') if match.group('drive') else 'FWD | RWD'
#     return result if result else None
#
#
# # Применяем функцию extract_modification_info к каждой модификации и выводим результат
# for indx, mod in enumerate(modifications):
#     result = extract_modification_info(mod)
#     if result:
#         print(f"№ {indx + 1}. {result}")

# import re
#
# # Обновлённый паттерн для обработки электромобилей
# regex_pattern_electro = re.compile(
#     r'(?:[A-Z0-9]+\s+)*'
#     r'(?:'
#     r'(?P<battery>(\d+(\.\d+)?)\s*kWh|(\d+(\.\d+)?)kWh|\(\d+\s*kWh\))\s+'
#     r')?'
#     r'(?:[A-Z0-9]+\s+)*'
#     r'Electro\s+'
#     r'(?P<transmission>[A-Z]+)\s+\('
#     r'(?P<power>\d+)\s+кВт\)\s*'
#     r'(?P<drive>\w+)?'
# )
#
# texts = [
#     "111 kWh Electro AT (455 кВт) 4WD",
#     "94.5 kWh Electro AT (175 кВт)",
#     "86  kWh Electro AT (150 кВт)",
#     "35kWh Electro AT (100 кВт)",
#     "Ei5 61.1kWh Electro AT (135 кВт)",
#     "GT 59.1 kWh Electro AT (126 кВт)",
#     "L 50kWh Electro AT (100 кВт)",
#     "500e 42 kWh Electro AT (87 кВт)",
#     "Pro (50 kWh) Electro AT (100 кВт)"
# ]
#
# for text in texts:
#     match = re.search(regex_pattern_electro, text)
#     if match:
#         battery_match = match.group('battery')
#         if battery_match:
#             battery_value = re.search(r'\d+(\.\d+)?', battery_match).group()
#         else:
#             battery_value = None
#         transmission = match.group('transmission')
#         power = match.group('power')
#         drive = match.group('drive')
#
#         print(f"Battery: {battery_value}, Transmission: {transmission}, Power: {power}, Drive: {drive}")
#


AUTORU_API_KEY = env('AUTORU_API_KEY')
HEADERS_AUTH = {'x-authorization': AUTORU_API_KEY, 'Accept': 'application/json', 'Content-Type': 'application/json'}
LOGIN = env('AUTORU_LOGIN')
PASSWORD = env('AUTORU_PASSWORD')
ENDPOINT = 'https://apiauto.ru/1.0'



def authenticate(login: str, password: str) -> Dict[str, str]:
    auth_url = f'{ENDPOINT}/auth/login'
    login_data = {'login': login, 'password': password}
    response = requests.post(url=auth_url, headers=HEADERS_AUTH, json=login_data)
    response.raise_for_status()
    session_id = {'x-session-id': response.json()['session']['id']}
    return session_id

session_id = authenticate(LOGIN, PASSWORD)
def fetch_catalog_structure(param: str, session_id: Dict[str, str], retries: int = 3) -> Dict:
    url = f'{ENDPOINT}/search/cars/breadcrumbs'
    headers = {**HEADERS_AUTH, **session_id}
    params = {'bc_lookup': param}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise RuntimeError(f"Failed to fetch data from auto.ru API after {retries} attempts: {e}")


def fetch_generation_name(mark_code: str, model_code: str, generation_id: str, session_id: Dict[str, str]) -> str:
    """Fetch generation name from API."""
    param = f"{mark_code}#{model_code}#{generation_id}" if generation_id else f"{mark_code}#{model_code}"
    try:
        api_result = fetch_catalog_structure(param, session_id)
        for breadcrumb in api_result.get('breadcrumbs', []):
            if breadcrumb.get('meta_level') == 'GENERATION_LEVEL':
                return breadcrumb.get('entities', [{}])[0].get('name', 'Unknown')
        return 'Unknown'
    except Exception as e:
        print(f"Error fetching generation name: {e}")
        return 'Unknown'

res = fetch_generation_name('THAIRUNG', 'TRANSFORMER','23666273', session_id)
print(res)
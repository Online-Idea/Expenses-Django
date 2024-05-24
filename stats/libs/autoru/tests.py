import re

# Ваш набор строк с модификациями
modifications = [
    "0.7 MT (58 л.с.)",
    "0.7 AT (58 л.с.)",
    "2.8 AT (177 л.с.) 4WD",
    "2.8d MT (177 л.с.)",
    "2.8hyb CVT (187 л.с.) FWD",
    "SDI 1.9d MT (64 л.с.)",
    "300 CDI BlueTEC 2.1hyb AT (204 л.с.) FWD",
    "109 CDI 1.5 MT (95 л.с.) FWD",
    "Electro AT (85 кВт)",
    "ZE40 Q90 Electro MT (65 кВт)",
    "72kWh  ZE40 Electro AT (68 кВт) FWD",
    "L Electro AT (100 кВт)",
    "75kWh L Electro AT (1200 кВт)",
    "Turbo S E-Hybrid Executive 4.0hyb AMT (571 л.с.) 4WD",
    "Turbo S E-Hybrid 4.0hyb AMT (571 л.с.) 4WD",
    "T 6.8 AT (500 л.с.)"
]

# Паттерн для обработки электромобилей
regex_pattern_electro = re.compile(
    r'(?:(?P<battery>\d+)kWh\s+)?(?:[A-Z0-9]+\s+)*(?:(?:[A-Z0-9]+\s+)?Electro\s+)?(?P<transmission>[A-Z]+)\s+(?:(?P<battery_after>\d+)kWh\s+)?\((?P<power>\d+)\s+кВт\)(?:\s+(?P<drive>\w+))?'
)

# Паттерн для обработки обычных автомобилей
regex_pattern_normal = re.compile(
    r'(?:(?P<engine_volume>[\d.]+)(?P<engine_type>[a-z]*)\s+)?(?:[A-Z0-9]+\s+)*(?P<transmission>[A-Z]+)\s+\((?P<power>\d+)\s+л\.с\.\)(?:\s+(?P<drive>\w+))?'
)


# Функция для обработки типа двигателя
def process_engine_type(engine_type):
    match engine_type:
        case 'd':
            return 'Дизель'
        case 'hyb':
            return 'Гибрид'
        case _:
            return 'Бензин'


# Функция для извлечения информации о модификации
def extract_modification_info(modification):
    result = {}
    if 'Electro' in modification:
        match = re.search(regex_pattern_electro, modification)
        if match:
            result['engine_type'] = 'Электро'
            result['battery_capacity'] = match.group('battery') if match.group('battery') else (
                match.group('battery_after') if match.group('battery_after') else '')
            result['transmission'] = match.group('transmission')
            result['power'] = match.group('power')
            result['drive'] = match.group('drive') if match.group('drive') else 'FWD | RWD'
    else:
        match = re.search(regex_pattern_normal, modification)
        if match:
            result['engine_type'] = process_engine_type(match.group('engine_type'))
            result['engine_volume'] = match.group('engine_volume')
            result['transmission'] = match.group('transmission')
            result['power'] = match.group('power')
            result['drive'] = match.group('drive') if match.group('drive') else 'FWD | RWD'
    return result if result else None


# Применяем функцию extract_modification_info к каждой модификации и выводим результат
for indx, mod in enumerate(modifications):
    result = extract_modification_info(mod)
    if result:
        print(f"№ {indx + 1}. {result}")

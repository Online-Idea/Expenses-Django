import logging


class ColoredLogger(logging.Logger):
    """
    Класс ColoredLogger расширяет функциональность стандартного логгера Python,
    добавляя поддержку цветного вывода сообщений в консоль с помощью ANSI-кодов.
    """

    # ANSI коды для цвета текста
    ANSI_CODES = {
        'BLUE': "\033[34m",
        'GREEN': "\033[32m",
        'YELLOW': "\033[33m",
        'RED': "\033[31m",
        'PURPLE': "\033[35m",
        'RESET': "\033[0m",  # Сбрасывает цвет текста до обычного
        'CYAN': "\033[96m",
        'MAGENTA': '\033[95m',
        'WHITE': '\033[97m',
    }

    def __init__(self, name: str, level: int = logging.NOTSET):
        """
        Инициализирует ColoredLogger.

        :param name: Имя логгера.
        :param level: Уровень логирования.
        """
        super().__init__(name, level)  # Инициализация базового логгера
        formatter = logging.Formatter('%(message)s')  # Форматирование логов

        handler = logging.StreamHandler()  # Создание обработчика для вывода логов в консоль
        handler.setFormatter(formatter)  # Применение форматтера к обработчику

        self.addHandler(handler)  # Добавление обработчика к логгеру

    def log(self, color: str, msg: str, *args, **kwargs):
        """
        Логирует сообщение в цвете, указанном в параметре color.

        :param color: Название цвета для логирования (например, 'RED', 'BLUE').
        :param msg: Сообщение для логирования.
        :param args: Дополнительные аргументы для логирования.
        :param kwargs: Дополнительные параметры для логирования.
        """
        # Получение ANSI кода для выбранного цвета. Если цвет не найден, используется RESET.
        color_code = self.ANSI_CODES.get(color, self.ANSI_CODES['RESET'])
        # Формируем цветное сообщение с сбросом цвета после текста
        message = f"{color_code}{msg}{self.ANSI_CODES['RESET']}"

        # Если указан аргумент 'return_value', возвращаем цветное сообщение вместо логирования
        if kwargs.get('return_value', False):
            return message

        # Логируем сообщение на уровне DEBUG (10 - это код уровня DEBUG)
        super().log(10, message, *args, **kwargs)

    # Методы для быстрого логирования сообщений в разных цветах

    def cyan(self, msg: str, *args, **kwargs):
        """ Логирует сообщение с цветом CYAN. """
        return self.log('CYAN', msg, *args, **kwargs)

    def blue(self, msg: str, *args, **kwargs):
        """ Логирует сообщение с цветом BLUE. """
        return self.log('BLUE', msg, *args, **kwargs)

    def green(self, msg: str, *args, **kwargs):
        """ Логирует сообщение с цветом GREEN. """
        return self.log('GREEN', msg, *args, **kwargs)

    def yellow(self, msg: str, *args, **kwargs):
        """ Логирует сообщение с цветом YELLOW. """
        return self.log('YELLOW', msg, *args, **kwargs)

    def red(self, msg: str, *args, **kwargs):
        """ Логирует сообщение с цветом RED. """
        return self.log('RED', msg, *args, **kwargs)

    def purple(self, msg: str, *args, **kwargs):
        """ Логирует сообщение с цветом PURPLE. """
        return self.log('PURPLE', msg, *args, **kwargs)

    def white(self, msg: str, *args, **kwargs):
        """ Логирует сообщение с цветом WHITE. """
        return self.log('WHITE', msg, *args, **kwargs)

    def magenta(self, msg: str, *args, **kwargs):
        """ Логирует сообщение с цветом MAGENTA. """
        return self.log('MAGENTA', msg, *args, **kwargs)


if __name__ == "__main__":
    # Пример использования
    logger = ColoredLogger(__name__)  # Создаем экземпляр цветного логгера
    logger.purple('Сообщение в фиолетовом цвете')
    logger.magenta('Сообщение в цвете MAGENTA')
    logger.white('Сообщение в белом цвете')

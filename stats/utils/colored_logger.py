import logging


class ColoredLogger(logging.Logger):
    # ANSI коды для цвета текста
    ANSI_CODES = {
        'BLUE': "\033[34m",
        'GREEN': "\033[32m",
        'YELLOW': "\033[33m",
        'RED': "\033[31m",
        'PURPLE': "\033[35m",
        'RESET': "\033[0m",
        'CYAN': "\033[96m",
        'MAGENTA': '\033[95m',
        'WHITE': '\033[97m',
    }

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        formatter = logging.Formatter('%(message)s')

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.addHandler(handler)

    def log(self, color: str, msg: str, *args, **kwargs):
        # Используем строковое значение для получения соответствующего ANSI кода цвета
        color_code = self.ANSI_CODES.get(color, self.ANSI_CODES['RESET'])  # По умолчанию используется RESET
        message = f"{color_code}{msg}{self.ANSI_CODES['RESET']}"  # Используем ANSI код RESET для сброса цвета после сообщения

        if kwargs.get('return_value', False):
            return message
        super().log(10, message, *args, **kwargs)

    def cyan(self, msg, *args, **kwargs):
        return self.log('CYAN', msg, *args, **kwargs)

    def blue(self, msg, *args, **kwargs):
        return self.log('BLUE', msg, *args, **kwargs)

    def green(self, msg, *args, **kwargs):
        return self.log('GREEN', msg, *args, **kwargs)

    def yellow(self, msg, *args, **kwargs):
        return self.log('YELLOW', msg, *args, **kwargs)

    def red(self, msg, *args, **kwargs):
        return self.log('RED', msg, *args, **kwargs)

    def purple(self, msg, *args, **kwargs):
        return self.log('PURPLE', msg, *args, **kwargs)

    def white(self, msg, *args, **kwargs):
        return self.log('WHITE', msg, *args, **kwargs)

    def magenta(self, msg, *args, **kwargs):
        return self.log('MAGENTA', msg, *args, **kwargs)


if __name__ == "__main__":
    logger = ColoredLogger(__name__)
    logger.purple('fff')
    logger.magenta('World')
    logger.white('hahaha')


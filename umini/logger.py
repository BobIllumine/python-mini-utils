import logging

from abc import abstractmethod, ABC

class Logger:
    def __init__(
        self, 
        format_str: str = '(%(asctime)s) [%(levelname)s]: %(message)s', 
        log_level: int = logging.INFO,
        log_file_path: str | None = None,
        from_logger: logging.Logger | None = None
    ):
        self.logger = from_logger or logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        formatter = logging.Formatter(format_str)
        self.formatter = formatter
        
        self.handlers = []
        
        if log_file_path:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(self.formatter)
            self.handlers.append(file_handler)
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(self.formatter)

        self.handlers.append(stream_handler)

        self._update_handlers()

    def disable(self):
        self.logger.disabled = True
    
    def enable(self):
        self.logger.disabled = False

    def _update_handlers(self):
        for handler in self.handlers:
            try:
                self.logger.addHandler(handler)
            except Exception as e:
                print(f"Failed to add handler {handler} to logger {self.logger}: {e}")

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def debug(self, message: str):
        self.logger.debug(message)

class LoggedObject(ABC):

    @abstractmethod
    def __init__(self, logger: Logger = Logger()):
        self.logger = logger

    def disable_logging(self):
        self.logger.disable()

    def enable_logging(self):
        self.logger.enable()

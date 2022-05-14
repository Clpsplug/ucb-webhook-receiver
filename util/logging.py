from abc import ABC
from abc import abstractmethod
from datetime import datetime


class ILogger(ABC):
    """
    Logger Interface
    """

    @abstractmethod
    def info(self, message: str):
        pass

    @abstractmethod
    def warning(self, message: str):
        pass

    @abstractmethod
    def error(self, message: str):
        pass


class PrintLogger(ILogger):
    """
    Logger that prints out the message into console. Use for Docker.
    """

    def info(self, message: str):
        print("{time} [INFO]: {message}".format(time=datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), message=message))

    def warning(self, message: str):
        print("{time} [WARN]: {message}".format(time=datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), message=message))

    def error(self, message: str):
        print("{time} [ERR!]: {message}".format(time=datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), message=message))

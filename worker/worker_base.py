from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Callable

from util.logging import ILogger


class OSType(Enum):
    macOS = 0
    Windows = 1


class BinaryType(Enum):
    LOCAL = 0
    DEV = 1
    PROD = 2


class IWorker(ABC):
    """
    Binary worker interface

    :ivar url: URL from which the binary is downloaded
    :ivar project_name: Project Name of the given binary
    :ivar target_name: Target Name (or build configuration name)
    :ivar logger: Logger. this should be a ILogger implementation
    """

    def __init__(self, url: str, project_name: str, target_name: str, logger: ILogger):
        self.url = url
        self.project_name = project_name
        self.target_name = target_name
        self.logger = logger

    @abstractmethod
    def process_binary(self) -> Callable:
        """
        Process the given binary, and put them in an appropriate directory.
        """
        pass

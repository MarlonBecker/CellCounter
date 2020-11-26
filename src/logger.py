"""logger definition """
import logging


ANSI_WHITE = "\u001b[37m"
ANSI_YELLOW = "\u001b[33m"
ANSI_RED = "\u001b[31m"
ANSI_GREEN = "\u001b[32m"


class Logger():
    """Logger."""
    _logger = None
    def __init__(self):
        self._logger = logging.getLogger("LegCount")
        self._logger.setLevel(logging.INFO)
        # Print the Messages to the console
        _handler = logging.StreamHandler()
        # Only show the Logger Name and the Message (eg. LegCount::INFO:    MSG)
        _loggingFormatter = logging.Formatter("%(name)s::%(message)s")
        _handler.setFormatter(_loggingFormatter)
        self._logger.handlers = [_handler]
        self._logger.propagate = False

    def info(self, msg):
        """Print info message
        :param str msg: message. """
        # print(msg)
        self._logger.info(f"INFO:\t{msg}")
        # if self.QTLogger is not None: self.QTLogger.write(f"INFO:\t{msg}")

    def warn(self, msg):
        """Print warning message.
        :param str msg: message. """
        self._logger.warn(f"{ANSI_YELLOW}WARN:\t{msg}{ANSI_WHITE}")
        # if self.QTLogger is not None: self.QTLogger.write(f"WARN:\t{msg}")

    def fatal(self, msg):
        """Print fatal message.
        :param str msg: message. """
        self._logger.fatal(f"{ANSI_RED}FATAL:\t{msg}{ANSI_WHITE}")
        # if self.QTLogger is not None: self.QTLogger.write(f"FATAL:\t{msg}")



logger = Logger()

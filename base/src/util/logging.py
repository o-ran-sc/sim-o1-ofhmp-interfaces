# /*************************************************************************
# *
# * Copyright 2025 highstreet technologies and others
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *     http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# ***************************************************************************/

import logging
from logging import Logger

pynts_log_level = logging.WARNING
logger_list = []

def set_pynts_log_level(level) -> None:
    global pynts_log_level, logger_list

    if level == "DEBUG":
        pynts_log_level = logging.DEBUG
    elif level == "INFO":
        pynts_log_level = logging.INFO
    elif level == "WARNING":
        pynts_log_level = logging.WARNING
    elif level == "ERROR":
        pynts_log_level = logging.ERROR
    elif level == "CRITICAL":
        pynts_log_level = logging.CRITICAL
    else:
        raise Exception(f"Invalid log level {level}")

    for logger in logger_list:
        logger.setLevel(pynts_log_level)
        for handler in logger.handlers:
            handler.setLevel(pynts_log_level)

def get_pynts_log_level():
    global pynts_log_level
    return pynts_log_level

class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(name)s: %(message)s"
    # format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatter.datefmt = "%Y-%m-%dT%H:%M:%S"
        return formatter.format(record)

def get_pynts_logger(name: str) -> Logger:
    global logger_list
    logger = logging.getLogger(name)
    logger_list.append(logger)
    logger.setLevel(pynts_log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(pynts_log_level)
    ch.setFormatter(CustomFormatter())

    logger.addHandler(ch)
    return logger

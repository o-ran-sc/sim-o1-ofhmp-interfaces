#!/usr/bin/python3

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

import argparse
from util.logging import get_pynts_logger, set_pynts_log_level
import importlib
from pathlib import Path

from core.core import Core
from util.threading import stop_event, sa_sleep

logger = get_pynts_logger("pynts")

EXTENSIONS = Path("./extensions")

class Application():
    def __init__(self) -> None:
        # argument parsing
        parser = argparse.ArgumentParser(description="PyNTS")
        parser.add_argument(
            '-v', '--verbose',
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            help='Set the logging level',
            default='debug'
        )
        args = parser.parse_args()

        # setup logging
        set_pynts_log_level(args.verbose.upper())

        logger.info("bbbbbbb")
        # get available extensions
        self.loaded_extensions = [Core()]

        if EXTENSIONS.exists():
            for folder in EXTENSIONS.iterdir():
                if folder.is_dir():
                    logger.info(f"loading {folder}")
                    main_file = folder / "main.py"
                    if main_file.exists():
                        absolute_path = main_file.resolve()

                        module_name = main_file.stem
                        spec = importlib.util.spec_from_file_location(module_name, absolute_path)
                        module = importlib.util.module_from_spec(spec)

                        spec.loader.exec_module(module)
                        cls = getattr(module, "Main")
                        self.loaded_extensions.append(cls())
                        logger.info(f"loaded {folder}")
                    else:
                        logger.error(f"failed to load {folder}")


        # init
        for extension in self.loaded_extensions:
            extension.init()


        # startup
        for extension in self.loaded_extensions:
            extension.startup()

        # run
        self.run()
        logger.info("thread finished")

    def run(self) -> None:
        while not stop_event.is_set():
            # logger.info(".")
            sa_sleep(1)

if __name__ == "__main__":
    a = Application()

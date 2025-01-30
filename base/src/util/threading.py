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

import signal
import threading
import time

# Event to signal threads to stop
stop_event = threading.Event()

def signal_handler(sig, frame):
    print('SIGINT received; stopping...')
    stop_event.set()

    from core.rest import Rest
    rest = Rest()
    rest.stop_server()

def sa_sleep(interval, extra_event=None):
    """Signal aware sleep in small increments to allow checking for stop_event."""
    end_time = time.time() + interval
    while time.time() < end_time:
        if extra_event is not None:
            if stop_event.is_set() or extra_event.is_set():
                return
        else:
            if stop_event.is_set():
                return

        time.sleep(min(1, end_time - time.time()))

# Set up the signal handler
signal.signal(signal.SIGINT, signal_handler)

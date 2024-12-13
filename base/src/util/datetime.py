# /*************************************************************************
# *
# * Copyright 2024 highstreet technologies and others
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

from datetime import datetime, timezone
from dateutil import parser

def ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        # Convert naive datetime to aware datetime with UTC offset
        return dt.replace(tzinfo=timezone.utc)
    return dt

def yang_datetime_to_datetime(yang: str) -> datetime:
    return parser.parse(yang)

def datetime_to_yang_datetime(dt: datetime) -> str:
    r = dt.replace(microsecond=0).isoformat()
    if dt.tzinfo is None:
        r = r + "Z"
    return r

def datetime_utcnow() -> datetime:
    return datetime.utcnow()

def timestamp_in_microseconds(now: datetime|None=None) -> int:
    """Returns the current timestamp in microseconds."""
    if now is None:
        now = datetime_utcnow()  # Use UTC time
    timestamp_in_microseconds = int(now.timestamp() * 1_000_000)
    return timestamp_in_microseconds

def yang_timestamp_with_miliseconds(now: datetime|None=None) -> str:
    """Returns the current timestamp in the NETCONF format with 3 digits for milliseconds."""
    if now is None:
        now = datetime_utcnow()  # Use UTC time
    netconf_timestamp = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return netconf_timestamp

def seconds_to_duration(seconds: int) -> str:
    """Converts a given number of seconds into an ISO 8601 duration string."""
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    duration = 'P'

    if days > 0:
        duration += f'{days}D'

    if hours > 0 or minutes > 0 or seconds > 0:
        duration += 'T'
        if hours > 0:
            duration += f'{hours}H'
        if minutes > 0:
            duration += f'{minutes}M'
        if seconds > 0:
            duration += f'{seconds}S'

    return duration

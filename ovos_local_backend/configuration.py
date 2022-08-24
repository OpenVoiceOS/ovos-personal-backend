# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from os.path import exists
from json_database import JsonConfigXDG

DEFAULT_CONFIG = {
    "stt": {"module": "ovos-stt-plugin-server",
            "ovos-stt-plugin-server": {"url": "https://stt.openvoiceos.com/stt"}},
    "backend_port": 6712,
    "admin_key": "CHANGE_ME",  # TODO empty/disabled by default - change before merge
    "default_location": {
        "city": {
            "code": "Lawrence",
            "name": "Lawrence",
            "state": {
                "code": "KS",
                "name": "Kansas",
                "country": {
                    "code": "US",
                    "name": "United States"
                }
            }
        },
        "coordinate": {
            "latitude": 38.971669,
            "longitude": -95.23525
        },
        "timezone": {
            "code": "America/Chicago",
            "name": "Central Standard Time",
            "dstOffset": 3600000,
            "offset": -21600000
        }
    },
    "date_format": "DMY",
    "system_unit": "metric",
    "time_format": "full",
    "geolocate": True,
    "override_location": False,
    "api_version": "v1",
    "data_path": "~",
    "record_utterances": False,
    "record_wakewords": False,
    "wolfram_key": "Y7R353-9HQAAL8KKA",
    "owm_key": "28fed22898afd4717ce5a1535da1f78c",
    "email": {
        "username": None,
        "password": None
    }
}

CONFIGURATION = JsonConfigXDG("ovos_backend")

if not exists(CONFIGURATION.path):
    CONFIGURATION.merge(DEFAULT_CONFIG, skip_empty=False)
    CONFIGURATION.store()


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
from ovos_utils.configuration import get_xdg_data_save_path
from ovos_utils.log import LOG

BACKEND_IDENTITY = f"{get_xdg_data_save_path('ovos_backend')}/identity2.json"

DEFAULT_CONFIG = {
    "stt": {
        "module": "ovos-stt-plugin-server",
        "ovos-stt-plugin-server": {
            "url": "https://stt.openvoiceos.com/stt"
        },
        "ovos-stt-plugin-selene": {
            "url": "https://api.mycroft.ai",
            "version": "v1",
            "identity_file": BACKEND_IDENTITY  # path to identity2.json file
        }
    },
    "backend_port": 6712,
    "admin_key": "",  # To enable simply set this string to something
    "skip_auth": False,  # you almost certainly do not want this, only for atypical use cases such as ovos-qubes
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
    "default_ww": "hey_mycroft",  # needs to be present below
    "ww_configs": {  # these can be exposed in a web UI for selection
        "hey_mycroft": {"phonemes": "HH EY . M AY K R AO F T",
                        "module": "ovos-ww-plugin-pocketsphinx",
                        "threshold": 1e-90},
        "hey_jarvis": {"phonemes": "HH EY . JH AA R V AH S .",
                       "module": "ovos-ww-plugin-pocketsphinx",
                       "threshold": 0.000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001},
        "christopher": {"phonemes": "K R IH S T AH F ER .",
                        "module": "ovos-ww-plugin-pocketsphinx",
                        "threshold": 1e-25},
        "hey_ezra": {"phonemes": "HH EY . EH Z R AH",
                     "module": "ovos-ww-plugin-pocketsphinx",
                     "threshold": 1e-10}
    },
    "default_tts": "American Male",  # needs to be present below
    "tts_configs": {  # these can be exposed in a web UI for selection
        "American Male": {"module": "ovos-tts-plugin-mimic2", "voice": "kusal"},
        "British Male": {"module": "ovos-tts-plugin-mimic", "voice": "ap"}
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
    "wolfram_key": "",
    "owm_key": "",
    "email": {
        "username": None,
        "password": None
    },
    "selene": {
        "enabled": False,  # needs to be explicitly enabled by user
        "url": "https://api.mycroft.ai",  # change if you are self hosting selene
        "version": "v1",
        # pairing settings
        # NOTE: the file should be used exclusively by backend, do not share with a mycroft-core instance
        "identity_file": BACKEND_IDENTITY,  # path to identity2.json file
        # send the pairing from selene to any device that attempts to pair with local backend
        # this will provide voice/gui prompts to the user and avoid the need to copy a identity file
        # only happens if backend is not paired with selene (hopefully exactly once)
        # if False you need to pair an existing mycroft-core as usual and move the file for backend usage
        "proxy_pairing": False,

        # micro service settings
        # NOTE: STT is handled at plugin level, configure ovos-stt-plugin-selene
        "proxy_weather": True,  # use selene for weather api calls
        "proxy_wolfram": True,  # use selene for wolfram alpha api calls
        "proxy_geolocation": True,  # use selene for geolocation api calls
        "proxy_email": False,  # use selene for sending email (only for email registered in selene)

        # device settings - if you want to spoof data in selene set these to False
        "download_location": True,  # set default location from selene
        "download_prefs": True,  # set default device preferences from selene
        "download_settings": True,  # download shared skill settings from selene
        "upload_settings": True,  # upload shared skill settings to selene
        "force2way": False,  # this forcefully re-enables 2way settings sync with selene
        # this functionality was removed from core, we hijack the settingsmeta endpoint to upload settings
        # upload will happen when mycroft-core boots and overwrite any values in selene (no checks for settings changed)
        # the assumption is that selene changes are downloaded instantaneously
        # if a device is offline when selene changes those changes will be discarded on next device boot

        # opt-in settings - what data to share with selene
        # NOTE: these also depend on opt_in being set in selene
        "opt_in": False,  # share data from all devices with selene (as if from a single device)
        "opt_in_blacklist": [],  # list of uuids that should ignore opt_in flag (never share data)
        "upload_metrics": True,  # upload device metrics to selene
        "upload_wakewords": True,  # upload wake word samples to selene
        "upload_utterances": True  # upload utterance samples to selene
    }
}

CONFIGURATION = JsonConfigXDG("ovos_backend")
if not exists(CONFIGURATION.path):
    CONFIGURATION.merge(DEFAULT_CONFIG, skip_empty=False)
    CONFIGURATION.store()
    LOG.info(f"Saved default configuration: {CONFIGURATION.path}")
else:
    # set any new default values since file creation
    for k, v in DEFAULT_CONFIG.items():
        if k not in CONFIGURATION:
            CONFIGURATION[k] = v
    LOG.info(f"Loaded configuration: {CONFIGURATION.path}")

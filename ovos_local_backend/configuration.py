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
from os.path import exists, expanduser

from json_database import JsonConfigXDG
from ovos_utils.configuration import get_xdg_data_save_path
from ovos_utils.log import LOG

BACKEND_IDENTITY = f"{get_xdg_data_save_path('ovos_backend')}/identity2.json"

DEFAULT_CONFIG = {
    "stt": {
        "module": "ovos-stt-plugin-server",
        "ovos-stt-plugin-server": {
            "url": "https://stt.openvoiceos.com/stt"
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
            "android": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/android.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "computer": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/computer.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "hey_chatterbox": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_chatterbox.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "hey_firefox": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_firefox.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "hey_k9": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_k9.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "hey_kit": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_kit.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "hey_moxie": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_moxie.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "hey_mycroft": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_mycroft.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "hey_scout": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_scout.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "marvin": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/marvin.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "o_sauro": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/o_sauro.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "sheila": {"module": "ovos-ww-plugin-precise-lite",
                            "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/sheila.tflite",
                            "expected_duration": 3,
                            "trigger_level": 3,
                            "sensitivity": 0.5
                        },
            "hey_jarvis": {"module": "ovos-ww-plugin-vosk",
                            "rule": "fuzzy",
                            "samples": [
                                "hay jarvis",
                                "hey jarvis",
                                "hay jarbis",
                                "hey jarbis"
                                ]
                        },
            "christopher": {"module": "ovos-ww-plugin-vosk",
                            "rule": "fuzzy",
                            "samples": [
                                "christopher"
                                ]
                        },
            "hey_ezra": {"module": "ovos-ww-plugin-vosk",
                            "rule": "fuzzy",
                            "samples": [
                                "hay ezra",
                                "hey ezra"
                                ]
                        },
            "hey_ziggy": {"module": "ovos-ww-plugin-vosk",
                        "rule": "fuzzy",
                        "samples": [
                            "hey ziggy",
                            "hay ziggy"
                            ]
                        },
            "hey_neon": {"module": "ovos-ww-plugin-vosk",
                         "rule": "fuzzy",
                         "samples": [
                             "hey neon",
                             "hay neon"
                             ]
                         }
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
    "data_path": expanduser("~"),
    "record_utterances": False,
    "record_wakewords": False,
    "microservices": {
        # if query fail, attempt to use free ovos services
        "ovos_fallback": True,
        # backend can be auto/local/ovos
        # auto == attempt local -> ovos
        "wolfram_provider": "auto",
        "weather_provider": "auto",
        # auto == OpenStreetMap default
        # valid - osm/arcgis/geocode_farm
        "geolocation_provider": "auto",
        # secret keys
        "wolfram_key": "",
        "owm_key": ""
    },
    "email": {
        "username": None,
        "password": None
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

# migrate old keys location
if "owm_key" in CONFIGURATION:
    CONFIGURATION["microservices"]["owm_key"] = CONFIGURATION.pop("owm_key")
if "wolfram_key" in CONFIGURATION:
    CONFIGURATION["microservices"]["wolfram_key"] = CONFIGURATION.pop("wolfram_key")

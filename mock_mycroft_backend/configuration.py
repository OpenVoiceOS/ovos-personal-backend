# Copyright 2019 Mycroft AI Inc.
#
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
from os.path import join, expanduser, isdir, exists
from os import makedirs
from json_database import JsonStorage

# DATABASE
DATA_PATH = join(expanduser("~/.mycroft/mock_backend"))
if not isdir(DATA_PATH):
    makedirs(DATA_PATH)
METRICS_DB = join(DATA_PATH, "metrics.json")
CONFIG_PATH = join(DATA_PATH, "mock_backend.conf")

# SSL
SSL = False
SSL_CERT = join(DATA_PATH, "mock_backend.crt")
SSL_KEY = join(DATA_PATH, "mock_backend.key")

# MOCK BACKEND
API_VERSION = "v1"
BACKEND_PORT = 6712

# EMAIL

MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = "xxx@gmail.com"
MAIL_PASSWORD = "xxx"
MAIL_DEFAULT_SENDER = MAIL_USERNAME

RECEIVING_EMAIL = MAIL_USERNAME

STT_CONFIG = {"module": "google",
              "google": {}}

LANG = "en-us"

OVERRIDE_LOCATION = False
GEOLOCATE_IP = False
DEFAULT_LOCATION = {
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
}


def default_conf():
    default = {
        "lang": LANG,
        "stt": STT_CONFIG,
        "backend_port": BACKEND_PORT,
        "ssl": SSL,
        "ssl_cert": SSL_CERT,
        "ssl_key": SSL_KEY,
        "mail_user": MAIL_USERNAME,
        "mail_password": MAIL_PASSWORD,
        "mail_server": MAIL_SERVER,
        "mail_port": MAIL_PORT,
        "default_location": DEFAULT_LOCATION,
        "geolocate": GEOLOCATE_IP,
        "override_location": OVERRIDE_LOCATION,
        "data_dir": DATA_PATH,
        "metrics_db": METRICS_DB,
        "api_version": API_VERSION,
        "email": RECEIVING_EMAIL,
        "data_path": DATA_PATH
    }
    config = JsonStorage(CONFIG_PATH)
    for k in default:
        config[k] = default[k]
    return config


if not exists(CONFIG_PATH):
    CONFIGURATION = default_conf()
    CONFIGURATION.store()
else:
    CONFIGURATION = JsonStorage(CONFIG_PATH)

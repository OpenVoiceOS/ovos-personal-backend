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
import json
import random

import flask

from ovos_backend_client.api import WolframAlphaApi, OpenWeatherMapApi, BackendType, GeolocationApi
from ovos_config import Configuration


def generate_code():
    k = ""
    while len(k) < 6:
        k += random.choice(["A", "B", "C", "D", "E", "F", "G", "H", "I",
                            "J", "K", "L", "M", "N", "O", "P", "Q", "R",
                            "S", "T", "U", "Y", "V", "X", "W", "Z", "0",
                            "1", "2", "3", "4", "5", "6", "7", "8", "9"])
    return k.upper()


def nice_json(arg):
    response = flask.make_response(json.dumps(arg, sort_keys=True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response


def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])


def dict_to_camel_case(data):
    converted = {}
    for k, v in data.items():
        new_k = to_camel_case(k)
        if isinstance(v, dict):
            v = dict_to_camel_case(v)
        if isinstance(v, list):
            for idx, item in enumerate(v):
                if isinstance(item, dict):
                    v[idx] = dict_to_camel_case(item)
        converted[new_k] = v
    return converted


class ExternalApiManager:
    def __init__(self):
        self.config = Configuration().get("microservices", {})
        self.units = Configuration()["system_unit"]

        self.wolfram_key = self.config.get("wolfram_key")
        self.owm_key = self.config.get("owm_key")

    @property
    def owm(self):
        return OpenWeatherMapApi(backend_type=BackendType.OFFLINE, key=self.owm_key)

    @property
    def wolfram(self):
        return WolframAlphaApi(backend_type=BackendType.OFFLINE, key=self.wolfram_key)

    def geolocate(self, address):
        return GeolocationApi(backend_type=BackendType.OFFLINE).get_geolocation(address)

    def wolfram_spoken(self, query, units=None, lat_lon=None):
        units = units or self.units
        if units != "metric":
            units = "imperial"
        return self.wolfram.spoken(query, units, lat_lon)

    def wolfram_simple(self, query, units=None, lat_lon=None):
        units = units or self.units
        if units != "metric":
            units = "imperial"
        return self.wolfram.simple(query, units, lat_lon)

    def wolfram_full(self, query, units=None, lat_lon=None):
        units = units or self.units
        if units != "metric":
            units = "imperial"
        return self.wolfram.full_results(query, units, lat_lon)

    def wolfram_xml(self, query, units=None, lat_lon=None):
        units = units or self.units
        if units != "metric":
            units = "imperial"
        return self.wolfram.full_results(query, units, lat_lon,
                                         optional_params={"output": "xml"})

    def owm_current(self, lat, lon, units, lang="en-us"):
        return self.owm.get_current((lat, lon), lang, units)

    def owm_onecall(self, lat, lon, units, lang="en-us"):
        return self.owm.get_weather((lat, lon), lang, units)

    def owm_hourly(self, lat, lon, units, lang="en-us"):
        return self.owm.get_hourly((lat, lon), lang, units)

    def owm_daily(self, lat, lon, units, lang="en-us"):
        return self.owm.get_daily((lat, lon), lang, units)

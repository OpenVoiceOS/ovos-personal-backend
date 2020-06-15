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
from flask import make_response
from subprocess import check_output
import random
import json
from os.path import exists, join, dirname
import requests


def root_dir():
    """ Returns root directory for this project """
    return dirname(dirname(__file__))


def generate_code():
    k = ""
    while len(k) < 6:
        k += random.choice(["A", "B", "C", "D", "E", "F", "G", "H", "I",
                            "J", "K", "L", "M", "N", "O", "P", "Q", "R",
                            "S", "T", "U", "Y", "V", "X", "W", "Z", "0",
                            "1", "2", "3", "4", "5", "6", "7", "8", "9"])
    return k.upper()


def nice_json(arg):
    response = make_response(json.dumps(arg, sort_keys=True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response


def geo_locate(ip):
    if ip in ["0.0.0.0", "127.0.0.1"]:
        ip = str(check_output(['hostname', '--all-ip-addresses'])).split(" ")[0][2:]
    data = requests.get("http://ip-api.com/json/" + ip,
                        params={"fields": "status,country,countryCode,region,regionName,city,lat,lon,timezone,query"})\
        .json()
    return location_dict(
        city=data["city"],
        region_code=data["region"],
        country_code=data["countryCode"],
        country_name=data["country"],
        region=data["regionName"],
        longitude=data["lon"],
        latitude=data["lat"],
        timezone=data["timezone"]
    )


def location_dict(city="", region_code="", country_code="",
                  country_name="", region="", longitude=0, latitude=0,
                  timezone="", **kwargs):
    region_data = {"code": region_code, "name": region,
                   "country": {
                       "code": country_code,
                       "name": country_name}}
    city_data = {"code": city, "name": city,
                 "state": region_data,
                 "region": region_data}
    timezone_data = {"code": timezone, "name": timezone,
                     "dstOffset": 3600000,
                     "offset": -21600000}
    coordinate_data = {"latitude": float(latitude),
                       "longitude": float(longitude)}
    return {"city": city_data,
            "coordinate": coordinate_data,
            "timezone": timezone_data}

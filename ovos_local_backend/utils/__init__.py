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

from flask import make_response


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

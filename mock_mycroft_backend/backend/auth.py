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

from mock_mycroft_backend.backend import API_VERSION
from mock_mycroft_backend.utils import nice_json
from mock_mycroft_backend.backend.decorators import noindex
from flask import request
import time


def get_auth_routes(app):
    @app.route("/" + API_VERSION + "/pair/<code>/<uuid>/<name>/<mail>",
               methods=['PUT'])
    @noindex
    def pair(code, uuid, name, mail):
        # auto - pair
        return nice_json({"paired": True})

    @app.route("/" + API_VERSION + "/auth/token", methods=['GET'])
    @noindex
    def token():
        token = request.headers.get('Authorization', '').replace("Bearer ", "")
        device = {"uuid": "AnonDevice",
                  "expires_at": time.time() + 999999999999999999,
                  "accessToken": token,
                  "refreshToken": token}
        return nice_json(device)

    return app

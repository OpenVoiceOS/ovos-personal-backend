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
import time

import flask

import ovos_local_backend.database as db
from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_admin
from ovos_local_backend.utils import generate_code
from ovos_local_backend.utils import nice_json
from ovos_local_backend.utils.geolocate import get_request_location
from ovos_config import LocalConf, USER_CONFIG, Configuration


def get_admin_routes(app):

    @app.route("/" + API_VERSION + "/admin/config", methods=['POST', 'GET'])
    @requires_admin
    @noindex
    def update_config():
        if flask.request.method == 'GET':
            return nice_json(Configuration())
        cfg = LocalConf(USER_CONFIG)
        cfg.merge(flask.request.json["config"])
        cfg.store()
        Configuration.reload()
        return nice_json(cfg)

    @app.route("/" + API_VERSION + "/admin/<uuid>/pair", methods=['GET'])
    @requires_admin
    @noindex
    def pair_device(uuid):
        code = generate_code()
        token = f"{code}:{uuid}"
        # add device to db
        entry = db.get_device(uuid)
        if not entry:
            location = get_request_location()
            db.add_device(uuid, token, location=location)
        else:
            db.update_device(uuid, token=token)

        device = {"uuid": uuid,
                  "expires_at": time.time() + 99999999999999,
                  "accessToken": token,
                  "refreshToken": token}
        return nice_json(device)

    @app.route("/" + API_VERSION + "/admin/<uuid>/device", methods=['PUT'])
    @requires_admin
    @noindex
    def set_device(uuid):
        device_data = db.update_device(uuid, **flask.request.json)
        return nice_json(device_data)

    @app.route("/" + API_VERSION + "/admin/<uuid>/location", methods=['PUT'])
    @requires_admin
    @noindex
    def set_location(uuid):
        device_data = db.update_device(uuid, location=flask.request.json)
        return nice_json(device_data)

    @app.route("/" + API_VERSION + "/admin/<uuid>/prefs", methods=['PUT'])
    @requires_admin
    @noindex
    def set_prefs(uuid):
        device_data = db.update_device(uuid, **flask.request.json)
        return nice_json(device_data)

    return app

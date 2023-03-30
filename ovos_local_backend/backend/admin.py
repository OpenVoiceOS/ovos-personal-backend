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

from flask import request
from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_admin
from ovos_local_backend.database import add_device, update_device
from ovos_local_backend.utils import generate_code
from ovos_local_backend.utils import nice_json
from ovos_local_backend.utils.geolocate import get_request_location


def get_database_crud(app):
    # DATABASE - (backend manager uses these)
    @app.route("/" + API_VERSION + "/admin/<uuid>/skill_settings",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_skill_settings(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/<uuid>/skill_settings/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_skill_settings(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/<uuid>/skill_settings/<skill_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_skill_settings(uuid, skill_id):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/skill_settings",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_shared_skill_settings():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/skill_settings/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_shared_skill_settings():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/skill_settings/<skill_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_shared_skill_settings(skill_id):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/oauth_apps",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_oauth_app(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/oauth_apps/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_oauth_apps(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/oauth_apps/<uuid>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_oauth_apps(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/oauth_toks",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_oauth_toks():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/oauth_toks/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_oauth_toks():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/oauth_toks/<uuid>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_oauth_toks(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/voice_recs",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_voice_rec():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/voice_recs/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_voice_recs():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/voice_recs/<uuid>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_voice_recs(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/ww_recs",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_ww_rec():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/ww_recs/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_ww_recs():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/ww_recs/<uuid>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_ww_recs(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/metrics",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_metric():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/metrics/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_metrics():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/metrics/<uuid>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_metric(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/devices",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_device():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/devices/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_devices():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/device/<uuid>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_device(uuid):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/voice_defs",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_voice_defs():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/voice_defs/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_voice_defs():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/voice_defs/<voice_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_voice_def(voice_id):
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/ww_defs",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_ww_def():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/ww_defs/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_ww_defs():
        return {}  # TODO

    @app.route("/" + API_VERSION + "/admin/ww_defs/<ww_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_ww_def(ww_id):
        return {}  # TODO

    return app


def get_admin_routes(app):
    @app.route("/" + API_VERSION + "/admin/<uuid>/pair", methods=['GET'])
    @requires_admin
    @noindex
    def pair_device(uuid):
        code = generate_code()
        token = f"{code}:{uuid}"
        # add device to db
        location = get_request_location()
        add_device(uuid, token, location=location)

        device = {"uuid": uuid,
                  "expires_at": time.time() + 99999999999999,
                  "accessToken": token,
                  "refreshToken": token}
        return nice_json(device)

    @app.route("/" + API_VERSION + "/admin/<uuid>/device", methods=['PUT'])
    @requires_admin
    @noindex
    def set_device(uuid):
        device_data = update_device(uuid, **request.json)
        return nice_json(device_data)

    @app.route("/" + API_VERSION + "/admin/<uuid>/location", methods=['PUT'])
    @requires_admin
    @noindex
    def set_location(uuid):
        device_data = update_device(uuid, location=request.json)
        return nice_json(device_data)

    @app.route("/" + API_VERSION + "/admin/<uuid>/prefs", methods=['PUT'])
    @requires_admin
    @noindex
    def set_prefs(uuid):
        device_data = update_device(uuid, **request.json)
        return nice_json(device_data)

    return get_database_crud(app)

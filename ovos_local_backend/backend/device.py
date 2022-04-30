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
import time
from flask import request

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.metrics import JsonMetricDatabase
from ovos_local_backend.utils import generate_code, nice_json
from ovos_local_backend.utils.geolocate import ip_geolocate
from ovos_local_backend.utils.mail import send_email


def get_device_routes(app):
    @app.route("/v1/device/<uuid>/settingsMeta", methods=['PUT'])
    def settingsmeta(uuid):
        return nice_json({"success": True, "uuid": uuid})

    @app.route("/v1/device/<uuid>/skill/settings", methods=['GET'])
    def skill_settings(uuid):
        return nice_json({"backend_disabled": True})

    @app.route("/v1/device/<uuid>/skillJson", methods=['PUT'])
    def skill_json(uuid):
        return nice_json({"backend_disabled": True})

    @app.route("/" + API_VERSION + "/device/<uuid>/location", methods=['GET'])
    @noindex
    def location(uuid):
        if not request.headers.getlist("X-Forwarded-For"):
            ip = request.remote_addr
        else:
            # TODO http://esd.io/blog/flask-apps-heroku-real-ip-spoofing.html
            ip = request.headers.getlist("X-Forwarded-For")[0]
        if CONFIGURATION["override_location"]:
            new_location = CONFIGURATION["default_location"]
        elif CONFIGURATION["geolocate"]:
            new_location = ip_geolocate(ip)
        else:
            new_location = {}
        return nice_json(new_location)

    @app.route("/" + API_VERSION + "/device/<uuid>/setting", methods=['GET'])
    @noindex
    def setting(uuid=""):
        result = {}
        return nice_json(result)

    @app.route("/" + API_VERSION + "/device/<uuid>", methods=['PATCH', 'GET'])
    @noindex
    def get_uuid(uuid):
        device = {"uuid": "AnonDevice",
                  "expires_at": time.time() + 72000,
                  "accessToken": uuid,
                  "refreshToken": uuid}
        return nice_json(device)

    @app.route("/" + API_VERSION + "/device/code", methods=['GET'])
    @noindex
    def code():
        uuid = request.args["state"]
        code = generate_code()
        result = {"code": code, "uuid": uuid}
        return nice_json(result)

    @app.route("/" + API_VERSION + "/device/", methods=['GET'])
    @noindex
    def device():
        token = request.headers.get('Authorization', '').replace("Bearer ", "")
        device = {"uuid": "AnonDevice",
                  "expires_at": time.time() + 72000,
                  "accessToken": token,
                  "refreshToken": token}
        return nice_json(device)

    @app.route("/" + API_VERSION + "/device/activate", methods=['POST'])
    @noindex
    def activate():
        token = request.json["state"]
        device = {"uuid": "AnonDevice",
                  "expires_at": time.time() + 72000,
                  "accessToken": token,
                  "refreshToken": token}
        return nice_json(device)

    @app.route("/" + API_VERSION + "/device/<uuid>/message", methods=['PUT'])
    @noindex
    def send_mail(uuid=""):
        data = request.json
        send_email(data["title"], data["body"])

    @app.route("/" + API_VERSION + "/device/<uuid>/metric/<name>", methods=['POST'])
    @noindex
    def metric(uuid="", name=""):
        data = request.json
        with JsonMetricDatabase() as db:
            db.add_metric(name, json.dumps(data))
        upload_data = {"uploaded": False}
        return nice_json({"success": True, "uuid": uuid,
                          "metric": data,
                          "upload_data": upload_data})

    @app.route("/" + API_VERSION + "/device/<uuid>/subscription", methods=['GET'])
    @noindex
    def subscription_type(uuid=""):
        sub_type = "free"
        subscription = {"@type": sub_type}
        return nice_json(subscription)

    @app.route("/" + API_VERSION + "/device/<uuid>/voice", methods=['GET'])
    @noindex
    def get_subscriber_voice_url(uuid=""):
        arch = request.args["arch"]
        return nice_json({"link": "", "arch": arch})

    return app

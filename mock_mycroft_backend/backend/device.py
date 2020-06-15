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
from flask_mail import Message
from flask import request
from mock_mycroft_backend.utils import geo_locate, generate_code, nice_json
from mock_mycroft_backend.configuration import CONFIGURATION
from mock_mycroft_backend.backend import API_VERSION
from mock_mycroft_backend.backend.decorators import noindex
from mock_mycroft_backend.database.metrics import JsonMetricDatabase
import time
import json


def get_device_routes(app, mail_sender):
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
            new_location = geo_locate(ip)
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
        message = data["body"]
        subject = data["title"]
        msg = Message(recipients=[CONFIGURATION["email"]],
                      body=message,
                      subject=subject,
                      sender=data["sender"])
        mail_sender.send(msg)

    @app.route("/" + API_VERSION + "/device/<uuid>/metric/<name>",
               methods=['POST'])
    @noindex
    def metric(uuid="", name=""):
        data = request.json
        with JsonMetricDatabase() as db:
            db.add_metric(name, json.dumps(data))

    @app.route("/" + API_VERSION + "/device/<uuid>/subscription",
               methods=['GET'])
    @noindex
    def subscription_type(uuid=""):
        sub_type = "free"
        subscription = {"@type": sub_type}
        return nice_json(subscription)

    @app.route("/" + API_VERSION + "/device/<uuid>/voice", methods=['GET'])
    @noindex
    def get_subscriber_voice_url(uuid=""):
        arch = request.args["arch"]
        return nice_json({"link": "",
                          "arch": arch})

    return app

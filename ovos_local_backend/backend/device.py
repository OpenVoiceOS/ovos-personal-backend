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
from ovos_local_backend.backend.decorators import noindex, requires_auth, requires_opt_in
from ovos_local_backend.database import SkillSettings
from ovos_local_backend.utils import generate_code, nice_json
from ovos_local_backend.utils.geolocate import get_request_location
from ovos_local_backend.utils.mail import send_email
from ovos_config import Configuration


@requires_opt_in
def save_metric(uuid, name, data):
    db.add_metric(uuid, name, data)


def get_device_routes(app):
    @app.route(f"/{API_VERSION}/device/<uuid>/settingsMeta", methods=['PUT'])
    @requires_auth
    def settingsmeta(uuid):
        """ new style skill settings meta (upload only) """
        s = SkillSettings.deserialize(flask.request.json)
        # ignore s.settings on purpose
        db.update_skill_settings(s.remote_id,
                                 metadata_json=s.meta,
                                 display_name=s.display_name)
        return nice_json({"success": True, "uuid": uuid})

    @app.route(f"/{API_VERSION}/device/<uuid>/skill/settings", methods=['GET'])
    @requires_auth
    def skill_settings_v2(uuid):
        """ new style skill settings (download only)"""
        return {s.skill_id: s.settings for s in db.get_skill_settings_for_device(uuid)}

    @app.route(f"/{API_VERSION}/device/<uuid>/skill", methods=['GET', 'PUT'])
    @requires_auth
    def skill_settings(uuid):
        """ old style skill settings/settingsmeta - supports 2 way sync
         PUT - json for 1 skill
         GET - list of all skills """
        if flask.request.method == 'PUT':
            s = SkillSettings.deserialize(flask.request.json)
            db.update_skill_settings(s.remote_id,
                                     settings_json=s.settings,
                                     metadata_json=s.meta,
                                     display_name=s.display_name)
            return nice_json({"success": True, "uuid": uuid})
        else:
            return nice_json([s.serialize() for s in db.get_skill_settings_for_device(uuid)])

    @app.route(f"/{API_VERSION}/device/<uuid>/skillJson", methods=['PUT'])
    @requires_auth
    def skill_json(uuid):
        """ device is communicating to the backend what skills are installed
        drop the info and don't track it! maybe if we add a UI and it becomes useful..."""
        # everything works in skill settings without using this
        data = flask.request.json
        # {'blacklist': [],
        # 'skills': [{'name': 'fallback-unknown',
        #             'origin': 'default',
        #             'beta': False,
        #             'status': 'active',
        #             'installed': 0,
        #             'updated': 0,
        #             'installation': 'installed',
        #             'skill_gid': 'fallback-unknown|21.02'}]
        return data

    @app.route(f"/{API_VERSION}/device/<uuid>/location", methods=['GET'])
    @requires_auth
    @noindex
    def location(uuid):
        device = db.get_device(uuid)
        if device:
            return device.location_json
        return get_request_location()

    @app.route(f"/{API_VERSION}/device/<uuid>/setting", methods=['GET'])
    @requires_auth
    @noindex
    def setting(uuid=""):
        device = db.get_device(uuid)
        if device:
            return device.selene_settings
        return {}

    @app.route(f"/{API_VERSION}/device/<uuid>", methods=['PATCH', 'GET'])
    @requires_auth
    @noindex
    def get_uuid(uuid):
        if flask.request.method == 'PATCH':
            # drop the info, we do not track it
            data = flask.request.json
            # {'coreVersion': '21.2.2',
            # 'platform': 'unknown',
            # 'platform_build': None,
            # 'enclosureVersion': None}
            return {}

        # get from local db
        device = db.get_device(uuid)
        if device:
            return device.selene_device

        # dummy valid data
        token = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
        uuid = token.split(":")[-1]
        return {
            "description": "unknown",
            "uuid": uuid,
            "name": "unknown",
            # not tracked / meaningless
            # just for api compliance with selene
            'coreVersion': "unknown",
            'platform': 'unknown',
            'enclosureVersion': "",
            "user": {"uuid": uuid}  # users not tracked
        }

    @app.route(f"/{API_VERSION}/device/code", methods=['GET'])
    @noindex
    def code():
        """ device is asking for pairing token
        we simplify things and use a deterministic access token, same as pairing token created here
        """
        uuid = flask.request.args["state"]
        code = generate_code()

        # pairing device with backend
        token = f"{code}:{uuid}"
        result = {"code": code, "uuid": uuid, "token": token,
                  # selene api compat
                  "expiration": 99999999999999, "state": uuid}
        return nice_json(result)

    @app.route(f"/{API_VERSION}/device/activate", methods=['POST'])
    @noindex
    def activate():
        """this is where the device checks if pairing was successful in selene
        in local backend we pair the device automatically in this step
        in selene this would only succeed after user paired via browser
        """
        uuid = flask.request.json["state"]

        # we simplify things and use a deterministic access token, shared with pairing token
        token = flask.request.json["token"]

        # add device to db
        try:
            location = get_request_location()
        except:
            location = Configuration()["location"]
        db.add_device(uuid, token, location=location)

        device = {"uuid": uuid,
                  "expires_at": time.time() + 99999999999999,
                  "accessToken": token,
                  "refreshToken": token}
        return nice_json(device)

    @app.route(f"/{API_VERSION}/device/<uuid>/message", methods=['PUT'])
    @noindex
    @requires_auth
    def send_mail(uuid=""):

        data = flask.request.json
        skill_id = data["sender"]  # TODO - auto append to body ?

        target_email = None
        device = db.get_device(uuid)
        if device:
            target_email = device.email
        send_email(data["title"], data["body"], target_email)

    @app.route(f"/{API_VERSION}/device/<uuid>/metric/<name>", methods=['POST'])
    @noindex
    @requires_auth
    def metric(uuid="", name=""):
        data = flask.request.json
        save_metric(uuid, name, data)
        return nice_json({"success": True,
                          "uuid": uuid,
                          "metric": data,
                          "upload_data": {"uploaded": False}})

    @app.route(f"/{API_VERSION}/device/<uuid>/subscription", methods=['GET'])
    @noindex
    @requires_auth
    def subscription_type(uuid=""):
        subscription = {"@type": "free"}
        return nice_json(subscription)

    @app.route(f"/{API_VERSION}/device/<uuid>/voice", methods=['GET'])
    @noindex
    @requires_auth
    def get_subscriber_voice_url(uuid=""):
        arch = flask.request.args["arch"]
        return nice_json({"link": "", "arch": arch})

    return app

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

from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth, check_selene_pairing
from ovos_local_backend.database.metrics import save_metric
from ovos_local_backend.database.settings import DeviceDatabase, SkillSettings, SettingsDatabase
from ovos_local_backend.utils import generate_code, nice_json
from ovos_local_backend.utils.geolocate import get_request_location
from ovos_local_backend.utils.mail import send_email
from ovos_local_backend.utils.selene import get_selene_code
from selene_api.api import DeviceApi
from selene_api.pairing import is_paired


def get_device_routes(app):
    @app.route("/v1/device/<uuid>/settingsMeta", methods=['PUT'])
    @check_selene_pairing
    @requires_auth
    def settingsmeta(uuid):
        """ new style skill settings meta (upload only) """
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and selene_cfg.get("upload_settings"):
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            # TODO - upload settings meta to selene if enabled
            # TODO - force 2-way-sync flag

        # save new settings meta to db
        with SettingsDatabase() as db:
            s = SkillSettings.deserialize(request.json)
            # keep old settings, update meta only
            old_s = db.get_setting(s.skill_id, uuid)
            if old_s:
                s.settings = old_s.settings
            db.add_setting(uuid, s.skill_id, s.settings, s.meta,
                           s.display_name, s.remote_id)
        return nice_json({"success": True, "uuid": uuid})

    @app.route("/v1/device/<uuid>/skill/settings", methods=['GET'])
    @check_selene_pairing
    @requires_auth
    def skill_settings_v2(uuid):
        """ new style skill settings (download only)"""
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and selene_cfg.get("download_settings"):
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            # TODO - get settings from selene if enabled

        db = SettingsDatabase()
        return {s.skill_id: s.settings for s in db.get_device_settings(uuid)}

    @app.route("/v1/device/<uuid>/skill", methods=['GET', 'PUT'])
    @check_selene_pairing
    @requires_auth
    def skill_settings(uuid):
        """ old style skill settings/settingsmeta - supports 2 way sync
         PUT - json for 1 skill
         GET - list of all skills """
        selene_cfg = CONFIGURATION.get("selene") or {}
        url = selene_cfg.get("url")
        version = selene_cfg.get("version") or "v1"
        identity_file = selene_cfg.get("identity_file")

        if request.method == 'PUT':
            if selene_cfg.get("enabled") and selene_cfg.get("upload_settings"):
                # TODO - upload settings to selene if enabled
                pass

            with SettingsDatabase() as db:
                s = SkillSettings.deserialize(request.json)
                db.add_setting(uuid, s.skill_id, s.settings, s.meta,
                               s.display_name, s.remote_id)
            return nice_json({"success": True, "uuid": uuid})
        else:
            if selene_cfg.get("enabled") and selene_cfg.get("upload_settings"):
                # TODO - get settings from selene if enabled
                pass

            return nice_json([s.serialize() for s in SettingsDatabase().get_device_settings(uuid)])

    @app.route("/v1/device/<uuid>/skillJson", methods=['PUT'])
    @requires_auth
    def skill_json(uuid):
        """ device is communicating to the backend what skills are installed
        drop the info and don't track it! maybe if we add a UI and it becomes useful..."""
        # TODO - do we care about sending this to selene? seems optional....
        # everything works in skill settings without using this
        data = request.json
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

    @app.route("/" + API_VERSION + "/device/<uuid>/location", methods=['GET'])
    @requires_auth
    @check_selene_pairing
    @noindex
    def location(uuid):
        # get location from selene if enabled
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and selene_cfg.get("download_location"):
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            api = DeviceApi(url, version, identity_file)
            # update in local db
            loc = api.get_location()
            with DeviceDatabase() as db:
                device = db.get_device(uuid)
                device.location = loc
                db.update_device(device)
            return loc

        device = DeviceDatabase().get_device(uuid)
        if device:
            return device.location
        return get_request_location()

    @app.route("/" + API_VERSION + "/device/<uuid>/setting", methods=['GET'])
    @check_selene_pairing
    @requires_auth
    @noindex
    def setting(uuid=""):
        # get/update device preferences from selene if enabled
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and selene_cfg.get("download_prefs"):
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            api = DeviceApi(url, version, identity_file)
            data = api.get_settings()
            # update in local db
            with DeviceDatabase() as db:
                device = db.get_device(uuid)
                device.system_unit = data["systemUnit"]
                device.time_format = data["timeFormat"]
                device.date_format = data["dateFormat"]
                db.update_device(device)

        device = DeviceDatabase().get_device(uuid)
        if device:
            return device.selene_settings
        return {}

    @app.route("/" + API_VERSION + "/device/<uuid>", methods=['PATCH', 'GET'])
    @check_selene_pairing
    @requires_auth
    @noindex
    def get_uuid(uuid):
        if request.method == 'PATCH':
            # drop the info, we do not track it
            data = request.json
            # {'coreVersion': '21.2.2',
            # 'platform': 'unknown',
            # 'platform_build': None,
            # 'enclosureVersion': None}
            return {}

        # get/update device_name and device_location from selene if enabled
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and selene_cfg.get("download_prefs"):
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            api = DeviceApi(url, version, identity_file)
            data = api.get()
            device_location = data.get("description") or "unknown"
            device_name = data.get("name") or "unknown"
            # update local db with remote info
            with DeviceDatabase() as db:
                device = db.get_device(uuid)
                device.name = device_name
                device.device_location = device_location
                db.update_device(device)
        else:
            device_location = device_name = "unknown"

        # get from local db
        device = DeviceDatabase().get_device(uuid)
        if device:
            return device.selene_device

        # dummy valid data
        token = request.headers.get('Authorization', '').replace("Bearer ", "")
        uuid = token.split(":")[-1]
        return {
            "description": device_location,
            "uuid": uuid,
            "name": device_name,
            # not tracked / meaningless
            # just for api compliance with selene
            'coreVersion': "unknown",
            'platform': 'unknown',
            'enclosureVersion': "",
            "user": {"uuid": uuid}  # users not tracked
        }

    @app.route("/" + API_VERSION + "/device/code", methods=['GET'])
    @noindex
    def code():
        """ device is asking for pairing token
        we simplify things and use a deterministic access token, same as pairing token created here
        """
        uuid = request.args["state"]
        code = generate_code()

        # if selene enabled and not paired
        #  return selene pairing code
        #  only ask it from selene once, return same code to all devices
        #  devices are only being used to prompt the user for action in backend
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and not is_paired():
            # pairing device with backend + backend with selene
            # share spoken code for simplicity
            # hijacking devices to speak prompts for selene pairing
            code = get_selene_code() or code

        # pairing device with backend
        token = f"{code}:{uuid}"
        result = {"code": code, "uuid": uuid, "token": token,
                  # selene api compat
                  "expiration": 99999999999999, "state": uuid}
        return nice_json(result)

    @app.route("/" + API_VERSION + "/device/activate", methods=['POST'])
    @noindex
    def activate():
        """this is where the device checks if pairing was successful in selene
        in local backend we pair the device automatically in this step
        in selene this would only succeed after user paired via browser
        """
        uuid = request.json["state"]

        # we simplify things and use a deterministic access token, shared with pairing token
        token = request.json["token"]

        # add device to db
        location = get_request_location()
        with DeviceDatabase() as db:
            db.add_device(uuid, token, location=location)

        device = {"uuid": uuid,
                  "expires_at": time.time() + 99999999999999,
                  "accessToken": token,
                  "refreshToken": token}
        return nice_json(device)

    @app.route("/" + API_VERSION + "/device/<uuid>/message", methods=['PUT'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def send_mail(uuid=""):

        data = request.json
        skill_id = data["sender"]  # TODO - auto append to body ?

        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and selene_cfg.get("proxy_email"):
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            api = DeviceApi(url, version, identity_file)
            return api.send_email(data["title"], data["body"], skill_id)

        target_email = None
        device = DeviceDatabase().get_device(uuid)
        if device:
            target_email = device.email
        send_email(data["title"], data["body"], target_email)

    @app.route("/" + API_VERSION + "/device/<uuid>/metric/<name>", methods=['POST'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def metric(uuid="", name=""):
        data = request.json

        save_metric(uuid, name, data)

        # contribute to mycroft metrics dataset
        # may require https://github.com/OpenVoiceOS/OVOS-local-backend/issues/20
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and \
                selene_cfg.get("upload_metrics") and \
                selene_cfg.get("opt_in"):
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            api = DeviceApi(url, version, identity_file)
            return api.report_metric(name, data)

        return nice_json({"success": True,
                          "uuid": uuid,
                          "metric": data,
                          "upload_data": {"uploaded": False}})

    @app.route("/" + API_VERSION + "/device/<uuid>/subscription", methods=['GET'])
    @noindex
    @requires_auth
    def subscription_type(uuid=""):
        # if selene enabled and paired check type in selene
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and is_paired():
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            api = DeviceApi(url, version, identity_file)
            return api.get_subscription()

        subscription = {"@type": "free"}
        return nice_json(subscription)

    @app.route("/" + API_VERSION + "/device/<uuid>/voice", methods=['GET'])
    @noindex
    @check_selene_pairing
    @requires_auth
    def get_subscriber_voice_url(uuid=""):
        arch = request.args["arch"]
        # if selene enabled and paired return premium voice data
        selene_cfg = CONFIGURATION.get("selene") or {}
        if selene_cfg.get("enabled") and is_paired():
            url = selene_cfg.get("url")
            version = selene_cfg.get("version") or "v1"
            identity_file = selene_cfg.get("identity_file")
            api = DeviceApi(url, version, identity_file)
            return api.get_subscriber_voice_url(arch=arch)
        return nice_json({"link": "", "arch": arch})

    return app

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

import base64

import flask

import ovos_local_backend.database as db
from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_admin


def get_database_crud(app):

    # DATABASE - (backend manager uses these)
    @app.route("/" + API_VERSION + "/admin/<uuid>/skill_settings",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_skill_settings(uuid):
        data = flask.request.json
        skill_id = data.pop("skill_id")
        device = db.get_device(uuid)
        if not device:
            return {"error": f"unknown uuid: {uuid}"}
        if device.isolated_skills:
            remote_id = f"@{uuid}|{skill_id}"
        else:
            remote_id = skill_id
        entry = db.add_skill_settings(remote_id, **data)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/<uuid>/skill_settings/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_skill_settings(uuid):
        entries = db.get_skill_settings_for_device(uuid)
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/<uuid>/skill_settings/<skill_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_skill_settings(uuid, skill_id):
        device = db.get_device(uuid)
        if not device:
            return {"error": f"unknown uuid: {uuid}"}
        if device.isolated_skills:
            remote_id = f"@{uuid}|{skill_id}"
        else:
            remote_id = skill_id
        if flask.request.method == 'DELETE':
            success = db.delete_skill_settings(remote_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_skill_settings(remote_id, **flask.request.json)
        else:  # GET
            entry = db.get_skill_settings(remote_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/skill_settings",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_shared_skill_settings():
        data = flask.request.json
        skill_id = data.pop("skill_id")
        entry = db.add_skill_settings(skill_id, **data)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/skill_settings/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_shared_skill_settings():
        entries = db.list_skill_settings()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/skill_settings/<skill_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_shared_skill_settings(skill_id):
        if flask.request.method == 'DELETE':
            success = db.delete_skill_settings(skill_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_skill_settings(skill_id, **flask.request.json)
        else:  # GET
            entry = db.get_skill_settings(skill_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/oauth_apps",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_oauth_app():
        entry = db.add_oauth_application(**flask.request.json)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/oauth_apps/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_oauth_apps():
        entries = db.list_oauth_applications()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/oauth_apps/<token_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_oauth_apps(token_id):
        if flask.request.method == 'DELETE':
            success = db.delete_oauth_application(token_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_oauth_application(token_id, **flask.request.json)
        else:  # GET
            entry = db.get_oauth_application(token_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/oauth_toks",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_oauth_toks():
        entry = db.add_oauth_token(**flask.request.json)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/oauth_toks/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_oauth_toks():
        entries = db.list_oauth_tokens()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/oauth_toks/<token_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_oauth_toks(token_id):
        if flask.request.method == 'DELETE':
            success = db.delete_oauth_token(token_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_oauth_token(token_id, **flask.request.json)
        else:  # GET
            entry = db.get_oauth_token(token_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/voice_recs/<uuid>",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_voice_rec(uuid):
        # b64 decode bytes before saving
        data = flask.request.json
        audio_b64 = data.pop("audio_b64")
        data["byte_data"] = base64.b64decode(audio_b64)
        entry = db.add_stt_recording(uuid, **data)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/voice_recs/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_voice_recs():
        entries = db.list_stt_recordings()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/voice_recs/<recording_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_voice_rec(recording_id):
        # rec_id = f"@{uuid}|{transcription}|{count}"
        if flask.request.method == 'DELETE':
            success = db.delete_stt_recording(recording_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_stt_recording(recording_id, **flask.request.json)
        else:  # GET
            entry = db.get_stt_recording(recording_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/ww_recs/<uuid>",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_ww_rec(uuid):
        # b64 decode bytes before saving
        data = flask.request.json
        audio_b64 = data.pop("audio_b64")
        data["byte_data"] = base64.b64decode(audio_b64)
        entry = db.add_ww_recording(uuid, **data)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/ww_recs/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_ww_recs():
        entries = db.list_ww_recordings()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/ww_recs/<recording_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_ww_rec(recording_id):
        #  rec_id = f"@{uuid}|{transcription}|{count}"
        if flask.request.method == 'DELETE':
            success = db.delete_ww_recording(recording_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_ww_recording(recording_id, **flask.request.json)
        else:  # GET
            entry = db.get_ww_recording(recording_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/metrics/<uuid>",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_metric(uuid):
        entry = db.add_metric(uuid, **flask.request.json)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/metrics/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_metrics():
        entries = db.list_metrics()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/metrics/<metric_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_metric(metric_id):
        # metric_id = f"@{uuid}|{name}|{count}"
        if flask.request.method == 'DELETE':
            success = db.delete_metric(metric_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_metric(metric_id, flask.request.json)
        else:  # GET
            entry = db.get_metric(metric_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/devices",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_device():
        kwargs = flask.request.json
        uuid = kwargs.pop("uuid")
        entry = db.get_device(uuid)
        if entry:
            entry = db.update_device(uuid, **kwargs)
            return entry.serialize()

        token = kwargs.pop("token")
        entry = db.add_device(uuid, token, **kwargs)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/devices/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_devices():
        entries = db.list_devices()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/devices/<uuid>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_device(uuid):
        if flask.request.method == 'DELETE':
            success = db.delete_device(uuid)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_device(uuid, **flask.request.json)
        else:  # GET
            entry = db.get_device(uuid)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/voice_defs",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_voice_defs():
        kwargs = flask.request.json
        plugin = kwargs.pop("plugin")
        lang = kwargs.pop("lang")
        tts_config = kwargs.pop("tts_config")
        entry = db.add_voice_definition(plugin, lang, tts_config, **kwargs)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/voice_defs/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_voice_defs():
        entries = db.list_voice_definitions()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/voice_defs/<voice_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_voice_def(voice_id):
        if flask.request.method == 'DELETE':
            success = db.delete_voice_definition(voice_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_voice_definition(voice_id, **flask.request.json)
        else:  # GET
            entry = db.get_voice_definition(voice_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/ww_defs",
               methods=['POST'])
    @requires_admin
    @noindex
    def create_ww_def():
        entry = db.add_wakeword_definition(**flask.request.json)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    @app.route("/" + API_VERSION + "/admin/ww_defs/list",
               methods=['GET'])
    @requires_admin
    @noindex
    def list_ww_defs():
        entries = db.list_wakeword_definition()
        return [e.serialize() for e in entries]

    @app.route("/" + API_VERSION + "/admin/ww_defs/<ww_id>",
               methods=['GET', "PUT", "DELETE"])
    @requires_admin
    @noindex
    def get_ww_def(ww_id):
        if flask.request.method == 'DELETE':
            success = db.delete_wakeword_definition(ww_id)
            return {"success": success}
        elif flask.request.method == 'PUT':
            entry = db.update_wakeword_definition(ww_id, **flask.request.json)
        else:  # GET
            entry = db.get_wakeword_definition(ww_id)
        if not entry:
            return {"error": "entry not found"}
        return entry.serialize()

    return app

import flask
import json

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth, requires_opt_in
from ovos_config import Configuration
from ovos_local_backend.database import add_ww_recording


@requires_opt_in
def save_ww_recording(uuid, uploads):
    meta = {}
    audio = None
    for ww_file in uploads:
        # Werkzeug FileStorage objects
        fn = uploads[ww_file].filename
        if fn == 'audio':
            audio = uploads[ww_file].read()
        if fn == 'metadata':
            meta = json.load(uploads[ww_file])

    if not audio:
        return False  # TODO - some error? just ignore entry for now

    # classic mycroft devices send
    # {"name": "hey-mycroft",
    # "engine": "0f4df281688583e010c26831abdc2222",
    # "time": "1592192357852",
    # "sessionId": "7d18e208-05b5-401e-add6-ee23ae821967",
    # "accountId": "0",
    # "model": "5223842df0cdee5bca3eff8eac1b67fc"}

    add_ww_recording(uuid,
                     audio,
                     meta.get("name", "").replace("_", " "),
                     meta)
    return True


def get_precise_routes(app):
    @app.route('/precise/upload', methods=['POST'])
    @noindex
    @requires_auth
    def precise_upload():
        success = False
        allowed = Configuration()["listener"].get("record_wakewords")
        if allowed:
            auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
            uuid = auth.split(":")[-1]  # this split is only valid here, not selene
            success = save_ww_recording(uuid, flask.request.files)

        return {"success": success,
                "sent_to_mycroft": False,
                "saved": allowed}

    @app.route(f'/{API_VERSION}/device/<uuid>/wake-word-file', methods=['POST'])
    @noindex
    @requires_auth
    def precise_upload_v2(uuid):
        success = False
        if 'audio' not in flask.request.files:
            return "No Audio to upload", 400
        allowed = Configuration()["listener"].get("record_wakewords")

        if allowed:
            success = save_ww_recording(uuid, flask.request.files)

        return {"success": success,
                "sent_to_mycroft": False,
                "saved": allowed}

    return app
